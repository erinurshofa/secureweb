"""
Scoring Service Layer — Auto-Scoring MCQ & Penilaian Manual Essay Juri.
"""

from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError

from accounts.models import User
from questions.models import QuestionType
from attempts.models import ExamAttempt, AttemptAnswer
from grading.models import AttemptGrade, EssayEvaluation
from audit.models import SecurityAuditLog, AuditEventType


class ScoringService:
    @staticmethod
    @transaction.atomic
    def score_mcq_attempt(attempt: ExamAttempt) -> Decimal:
        """
        Melakukan auto-scoring untuk seluruh soal pilihan ganda pada suatu attempt.
        """
        answers = AttemptAnswer.objects.filter(
            attempt=attempt,
            question__type=QuestionType.MCQ
        ).select_related('question', 'selected_option')
        
        total_mcq = Decimal('0.00')
        
        for answer in answers:
            if answer.selected_option and answer.selected_option.is_correct:
                total_mcq += answer.question.points
                
        grade, _ = AttemptGrade.objects.get_or_create(attempt=attempt)
        grade.mcq_score = total_mcq
        grade.recalculate_total()
        grade.save(update_fields=['mcq_score', 'total_score', 'graded_at'])
        
        return total_mcq

    @staticmethod
    def calculate_answer_score(answer: AttemptAnswer) -> Decimal:
        """
        Menghitung nilai efektif suatu jawaban essay berdasarkan evaluasi seluruh juri.
        Jika dinilai oleh lebih dari 1 juri, digunakan nilai Rata-Rata (Mean Score).
        """
        evals = list(answer.essay_evaluations.all())
        if not evals:
            return Decimal('0.00')
        total_awarded = sum((ev.score_awarded for ev in evals), Decimal('0.00'))
        return (total_awarded / Decimal(len(evals))).quantize(Decimal('0.01'))

    @staticmethod
    def check_score_discrepancy(answer: AttemptAnswer, threshold_ratio: Decimal = Decimal('0.30')) -> dict:
        """
        Mendeteksi apakah terdapat selisih nilai mencolok antar dewan juri (>= threshold_ratio dari bobot soal).
        """
        evals = list(answer.essay_evaluations.all())
        threshold = (answer.question.points * threshold_ratio).quantize(Decimal('0.01'))
        if len(evals) < 2:
            return {'has_discrepancy': False, 'delta': Decimal('0.00'), 'threshold': threshold, 'eval_count': len(evals)}
        
        scores = [ev.score_awarded for ev in evals]
        min_s = min(scores)
        max_s = max(scores)
        delta = max_s - min_s
        threshold = (answer.question.points * threshold_ratio).quantize(Decimal('0.01'))
        
        return {
            'has_discrepancy': delta >= threshold,
            'delta': delta,
            'threshold': threshold,
            'min_score': min_s,
            'max_score': max_s,
            'eval_count': len(evals)
        }

    @staticmethod
    @transaction.atomic
    def grade_essay(
        answer_id: str,
        judge: User,
        score: Decimal,
        feedback: str = "",
        internal_notes: str = "",
        is_flagged: bool = False,
        dispute_reason: str = ""
    ) -> EssayEvaluation:
        """
        Menyimpan penilaian essay oleh juri dan mengupdate akumulasi essay_score pada attempt
        menggunakan konsensus Multi-Judge Average (Rata-Rata).
        """
        answer = AttemptAnswer.objects.select_related('attempt', 'question').get(id=answer_id)
        
        if answer.question.type != QuestionType.ESSAY:
            raise ValidationError("Soal yang dinilai bukan merupakan tipe essay.")
            
        if score < 0 or score > answer.question.points:
            raise ValidationError(f"Nilai essay harus berada di antara 0 dan {answer.question.points}.")
            
        evaluation, _ = EssayEvaluation.objects.update_or_create(
            attempt_answer=answer,
            judge=judge,
            defaults={
                'score_awarded': score,
                'feedback': feedback,
                'internal_notes': internal_notes,
                'is_flagged_for_review': is_flagged,
                'dispute_reason': dispute_reason
            }
        )
        
        # Hitung akumulasi nilai essay untuk seluruh attempt
        # Menggunakan Multi-Judge Average per jawaban essay
        essay_answers = AttemptAnswer.objects.filter(
            attempt=answer.attempt,
            question__type=QuestionType.ESSAY
        ).prefetch_related('essay_evaluations')
        
        total_essay = Decimal('0.00')
        for ea in essay_answers:
            total_essay += ScoringService.calculate_answer_score(ea)
                
        grade, _ = AttemptGrade.objects.get_or_create(attempt=answer.attempt)
        grade.essay_score = total_essay
        grade.recalculate_total()
        grade.save(update_fields=['essay_score', 'total_score', 'graded_at'])
        
        # Audit log
        SecurityAuditLog.objects.create(
            user=judge,
            event_type=AuditEventType.GRADE_ESSAY,
            details={
                'answer_id': str(answer.id),
                'judge_id': str(judge.id),
                'score_awarded': str(score),
                'attempt_id': str(answer.attempt.id),
                'is_flagged': is_flagged
            }
        )
        
        return evaluation

    @staticmethod
    @transaction.atomic
    def evaluate_and_score_attempt(attempt_or_id) -> AttemptGrade:
        """
        Kalkulasi komprehensif seluruh penilaian untuk suatu attempt:
        - Auto-score soal pilihan ganda
        - Hitung akumulasi essay yang telah dinilai (Multi-Judge Average)
        - Rekalkulasi total skor akhir dan simpan grade
        """
        if isinstance(attempt_or_id, ExamAttempt):
            attempt = attempt_or_id
        else:
            attempt = ExamAttempt.objects.select_for_update().get(id=str(attempt_or_id))

        # 1. Skor Pilihan Ganda
        ScoringService.score_mcq_attempt(attempt)

        # 2. Skor Essay (Multi-Judge Mean Calculation)
        essay_answers = AttemptAnswer.objects.filter(
            attempt=attempt,
            question__type=QuestionType.ESSAY
        ).prefetch_related('essay_evaluations')

        total_essay = Decimal('0.00')
        for ea in essay_answers:
            total_essay += ScoringService.calculate_answer_score(ea)

        grade, _ = AttemptGrade.objects.get_or_create(attempt=attempt)
        grade.essay_score = total_essay
        grade.recalculate_total()
        grade.save(update_fields=['essay_score', 'total_score', 'graded_at'])

        return grade
