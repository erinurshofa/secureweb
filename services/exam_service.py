"""
Exam Service Layer — Core Ujian, Timer Enforcement & Concurrency Control.
Memastikan integritas ujian dengan database row-level locking (select_for_update)
dan kalkulasi waktu berbasis backend server timestamp.
"""

from decimal import Decimal
from datetime import timedelta
from typing import Optional
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError, PermissionDenied

from accounts.models import User
from competitions.models import Competition, CompetitionStatus, ParticipantEnrollment
from questions.models import Question, QuestionOption, QuestionType
from attempts.models import ExamAttempt, AttemptAnswer, AnswerHistoryLog, AttemptStatus
from audit.models import SecurityAuditLog, AuditEventType
from grading.models import AttemptGrade


class ExamService:
    @staticmethod
    @transaction.atomic
    def start_attempt(user: User, competition_id: str, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> ExamAttempt:
        """
        Memulai sesi ujian baru untuk peserta.
        Menghitung server_deadline absolut berdasarkan backend timestamp.
        """
        competition = Competition.objects.select_for_update().get(id=competition_id)
        
        # 1. Validasi status kompetisi
        now = timezone.now()
        if competition.status != CompetitionStatus.OPEN or not (competition.start_time <= now <= competition.end_time):
            raise ValidationError("Kompetisi tidak sedang dibuka untuk pengerjaan.")
        
        # 2. Validasi enrollment
        enrollment = ParticipantEnrollment.objects.filter(
            competition=competition,
            participant=user,
            is_disqualified=False
        ).first()
        if not enrollment:
            raise PermissionDenied("Peserta tidak terdaftar pada kompetisi ini atau telah didiskualifikasi.")
        
        # 3. Hitung jumlah attempt yang sudah ada
        existing_attempts = ExamAttempt.objects.filter(
            competition=competition,
            participant=user
        ).count()
        
        if existing_attempts >= competition.max_attempts:
            raise ValidationError("Anda telah mencapai batas maksimal kesempatan (attempt) untuk kompetisi ini.")
            
        # 4. Cek apakah ada attempt yang masih IN_PROGRESS
        active_attempt = ExamAttempt.objects.filter(
            competition=competition,
            participant=user,
            status=AttemptStatus.IN_PROGRESS
        ).first()
        
        if active_attempt:
            # Jika sudah expired di backend tapi status belum update, otomatis tutup
            if active_attempt.is_expired():
                active_attempt.status = AttemptStatus.AUTO_SUBMITTED
                active_attempt.submitted_at = active_attempt.server_deadline
                active_attempt.save(update_fields=['status', 'submitted_at'])
                from services.scoring_service import ScoringService
                ScoringService.evaluate_and_score_attempt(active_attempt)
            else:
                return active_attempt

        # 5. Hitung batas waktu server (server_deadline)
        # Deadline adalah nilai terkecil antara: durasi attempt ATAU batas akhir event kompetisi
        calculated_deadline = now + timedelta(minutes=competition.duration_minutes)
        server_deadline = min(calculated_deadline, competition.end_time)
        
        attempt_number = existing_attempts + 1
        new_attempt = ExamAttempt.objects.create(
            competition=competition,
            participant=user,
            attempt_number=attempt_number,
            start_time=now,
            server_deadline=server_deadline,
            status=AttemptStatus.IN_PROGRESS,
            ip_address=ip_address,
            user_agent=user_agent or ''
        )
        
        # Buat record awal AttemptGrade
        AttemptGrade.objects.create(attempt=new_attempt)
        
        # Audit log
        SecurityAuditLog.objects.create(
            user=user,
            event_type=AuditEventType.START_EXAM,
            ip_address=ip_address,
            user_agent=user_agent or '',
            details={
                'attempt_id': str(new_attempt.id),
                'competition_id': str(competition.id),
                'attempt_number': attempt_number,
                'server_deadline': server_deadline.isoformat(),
            }
        )
        
        return new_attempt

    @staticmethod
    @transaction.atomic
    def save_answer(
        attempt_id: str,
        user: User,
        question_id: str,
        selected_option_id: Optional[str] = None,
        essay_text: Optional[str] = None,
        is_flagged: Optional[bool] = None,
        ip_address: Optional[str] = None
    ) -> AttemptAnswer:
        """
        Autosave jawaban peserta dengan penguncian baris (select_for_update)
        dan pencatatan audit trail anti-tampering.
        """
        attempt = ExamAttempt.objects.select_for_update().get(id=attempt_id, participant=user)
        
        # Validasi waktu dan status ujian
        if not attempt.can_modify_answers():
            if attempt.is_expired() and attempt.status == AttemptStatus.IN_PROGRESS:
                attempt.status = AttemptStatus.AUTO_SUBMITTED
                attempt.submitted_at = attempt.server_deadline
                attempt.save(update_fields=['status', 'submitted_at'])
                from services.scoring_service import ScoringService
                ScoringService.evaluate_and_score_attempt(attempt)
            raise ValidationError("Waktu pengerjaan telah berakhir atau ujian telah dikirim.")
            
        question = Question.objects.get(id=question_id, competition=attempt.competition)
        
        # Ambil atau buat record jawaban
        answer, created = AttemptAnswer.objects.select_for_update().get_or_create(
            attempt=attempt,
            question=question
        )
        
        previous_option_id = answer.selected_option_id
        previous_essay = answer.essay_text
        
        if question.type == QuestionType.MCQ:
            if selected_option_id:
                option = QuestionOption.objects.get(id=selected_option_id, question=question)
                answer.selected_option = option
            else:
                answer.selected_option = None
        elif question.type == QuestionType.ESSAY:
            if essay_text is not None:
                answer.essay_text = essay_text.strip()
                
        if is_flagged is not None:
            answer.is_flagged_for_review = is_flagged
            
        answer.revision_count += 1
        answer.save()
        
        # Catat jejak riwayat jawaban
        AnswerHistoryLog.objects.create(
            attempt_answer=answer,
            selected_option_id=previous_option_id,
            essay_text=previous_essay,
            ip_address=ip_address,
            revision=answer.revision_count
        )
        
        return answer

    @staticmethod
    @transaction.atomic
    def submit_attempt(attempt_id: str, user: User, is_auto: bool = False, ip_address: Optional[str] = None) -> ExamAttempt:
        """
        Finalisasi submission ujian peserta dan picu scoring pilihan ganda.
        """
        attempt = ExamAttempt.objects.select_for_update().get(id=attempt_id, participant=user)
        
        if attempt.status != AttemptStatus.IN_PROGRESS:
            return attempt
            
        now = timezone.now()
        attempt.submitted_at = now
        attempt.status = AttemptStatus.AUTO_SUBMITTED if is_auto else AttemptStatus.SUBMITTED
        attempt.save(update_fields=['status', 'submitted_at'])
        
        from services.scoring_service import ScoringService
        ScoringService.evaluate_and_score_attempt(attempt)
        
        # Audit Log
        SecurityAuditLog.objects.create(
            user=user,
            event_type=AuditEventType.FINAL_SUBMIT,
            ip_address=ip_address,
            details={
                'attempt_id': str(attempt.id),
                'is_auto_submitted': is_auto,
                'submitted_at': now.isoformat()
            }
        )
        
        return attempt
