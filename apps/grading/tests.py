from decimal import Decimal
from datetime import timedelta
from django.test import TestCase, Client
from django.utils import timezone
from django.urls import reverse

from accounts.models import User, UserRole
from competitions.models import Competition, CompetitionStatus
from questions.models import Question, QuestionType, QuestionStatus
from attempts.models import ExamAttempt, AttemptStatus, AttemptAnswer, AnswerHistoryLog
from grading.models import AttemptGrade, EssayEvaluation
from services.scoring_service import ScoringService


class JudgingAndScoringTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.now = timezone.now()

        # Users
        self.superadmin = User.objects.create_superuser(
            username='superadmin_test',
            password='Password123!',
            email='admin@test.com'
        )
        self.judge1 = User.objects.create_user(
            username='judge_alpha',
            password='Password123!',
            email='judge1@test.com',
            role=UserRole.JUDGE,
            is_staff=True
        )
        self.judge2 = User.objects.create_user(
            username='judge_beta',
            password='Password123!',
            email='judge2@test.com',
            role=UserRole.JUDGE,
            is_staff=True
        )
        self.participant = User.objects.create_user(
            username='participant_test',
            password='Password123!',
            email='user@test.com',
            role=UserRole.PARTICIPANT
        )

        # Competition & Questions
        self.competition = Competition.objects.create(
            title='Cyber Defense 2026',
            slug='cyber-defense-2026',
            status=CompetitionStatus.OPEN,
            start_time=self.now - timedelta(hours=1),
            end_time=self.now + timedelta(hours=3),
            duration_minutes=120
        )
        self.question_essay = Question.objects.create(
            competition=self.competition,
            title='Forensik Rootkit Hooking',
            body='Jelaskan teknik manipulasi /etc/ld.so.preload',
            rubric_guidelines='Kunci: ld.so.preload, libc readdir, chattr +i',
            type=QuestionType.ESSAY,
            points=Decimal('10.00'),
            sequence=1,
            status=QuestionStatus.APPROVED
        )

        # Attempt
        self.attempt = ExamAttempt.objects.create(
            participant=self.participant,
            competition=self.competition,
            attempt_number=1,
            status=AttemptStatus.SUBMITTED,
            start_time=self.now - timedelta(minutes=90),
            server_deadline=self.now + timedelta(minutes=30),
            submitted_at=self.now - timedelta(minutes=10)
        )

        # Answer
        self.answer = AttemptAnswer.objects.create(
            attempt=self.attempt,
            question=self.question_essay,
            essay_text='Rootkit memanfaatkan /etc/ld.so.preload untuk libc hooking.',
            revision_count=2
        )

    def test_multi_judge_average_scoring(self):
        """Uji perhitungan rata-rata (mean score) ketika dua juri memberi nilai."""
        # Juri 1 beri 9.0
        ScoringService.grade_essay(
            answer_id=str(self.answer.id),
            judge=self.judge1,
            score=Decimal('9.00'),
            feedback='Sangat bagus.',
            internal_notes='Poin lengkap'
        )

        grade = AttemptGrade.objects.get(attempt=self.attempt)
        self.assertEqual(grade.essay_score, Decimal('9.00'))

        # Juri 2 beri 7.0
        ScoringService.grade_essay(
            answer_id=str(self.answer.id),
            judge=self.judge2,
            score=Decimal('7.00'),
            feedback='Cukup baik.',
            internal_notes='Kurang mitigasi'
        )

        grade.refresh_from_db()
        # Rata-rata dari 9.00 dan 7.00 adalah 8.00
        self.assertEqual(grade.essay_score, Decimal('8.00'))

    def test_score_discrepancy_detection(self):
        """Uji deteksi selisih nilai mencolok (>= 30% dari bobot soal)."""
        # Juri 1 beri 9.0
        ScoringService.grade_essay(str(self.answer.id), self.judge1, Decimal('9.00'))
        # Juri 2 beri 4.0 (Selisih 5.0 >= 30% dari 10.00 yaitu 3.00)
        ScoringService.grade_essay(str(self.answer.id), self.judge2, Decimal('4.00'))

        self.answer.refresh_from_db()
        disc = ScoringService.check_score_discrepancy(self.answer)
        self.assertTrue(disc['has_discrepancy'])
        self.assertEqual(disc['delta'], Decimal('5.00'))

    def test_judge_separation_of_duties_rbac(self):
        """Juri dilarang mengakses bank soal panitia namun dapat mengakses panel grading."""
        self.client.force_login(self.judge1)

        # Akses panel grading harus berhasil (200 OK)
        res_grading = self.client.get(reverse('manage_grading'))
        self.assertEqual(res_grading.status_code, 200)

        # Akses edit/kelola soal harus ditolak (Redirect 302 dengan pesan error atau 403)
        res_questions = self.client.get(reverse('manage_questions'))
        self.assertEqual(res_questions.status_code, 302)

        # Akses kelola peserta harus ditolak
        res_participants = self.client.get(reverse('manage_participants'))
        self.assertEqual(res_participants.status_code, 302)
