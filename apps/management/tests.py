import json
from decimal import Decimal
from datetime import timedelta
from django.test import TestCase, Client
from django.utils import timezone
from django.urls import reverse

from accounts.models import User, UserRole
from competitions.models import Competition, CompetitionStatus
from questions.models import Question, QuestionType, QuestionStatus, QuestionOption
from attempts.models import ExamAttempt, AttemptStatus
from grading.models import AttemptGrade
from audit.models import SecurityAuditLog, AuditEventType


class ManagementFeaturesTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.now = timezone.now()

        # Users
        self.organizer = User.objects.create_user(
            username='organizer_test',
            password='Password123!',
            email='organizer@test.com',
            role=UserRole.ORGANIZER,
            is_staff=True
        )
        self.judge = User.objects.create_user(
            username='judge_test',
            password='Password123!',
            email='judge@test.com',
            role=UserRole.JUDGE,
            is_staff=True
        )
        self.participant = User.objects.create_user(
            username='participant_test',
            password='Password123!',
            email='participant@test.com',
            role=UserRole.PARTICIPANT
        )

        # Existing Competition
        self.competition = Competition.objects.create(
            title='Penyisihan CTF 2026',
            slug='penyisihan-ctf-2026',
            status=CompetitionStatus.OPEN,
            start_time=self.now,
            end_time=self.now + timedelta(days=7),
            duration_minutes=90,
            created_by=self.organizer
        )

    def test_quick_create_competition_success(self):
        """Test membuat kompetisi baru secara instan via AJAX tanpa reload halaman."""
        self.client.force_login(self.organizer)
        url = reverse('manage_competition_quick_create')
        response = self.client.post(url, {
            'title': 'Babak Final Reverse Engineering 2026',
            'duration_minutes': 120,
            'status': 'OPEN',
            'max_attempts': 1,
            'description': 'Babak perebutan juara analisis binari.'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['competition']['title'], 'Babak Final Reverse Engineering 2026')

        # Verifikasi keberadaan di database
        new_comp = Competition.objects.get(id=data['competition']['id'])
        self.assertEqual(new_comp.duration_minutes, 120)
        self.assertEqual(new_comp.created_by, self.organizer)
        self.assertTrue(new_comp.slug.startswith('babak-final-reverse-engineering-2026'))

    def test_quick_create_competition_validation_empty_title(self):
        """Test validasi gagal jika judul kompetisi kosong."""
        self.client.force_login(self.organizer)
        url = reverse('manage_competition_quick_create')
        response = self.client.post(url, {
            'title': '   ',
            'duration_minutes': 90
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['status'], 'error')
        self.assertIn('Judul kompetisi wajib diisi', data['message'])

    def test_quick_create_competition_unauthorized_judge(self):
        """Test hak akses: Role JUDGE dilarang membuat kompetisi (Separation of Duties)."""
        self.client.force_login(self.judge)
        url = reverse('manage_competition_quick_create')
        response = self.client.post(url, {
            'title': 'Unauthorized Competition'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 403)

    def test_questions_batch_create_get(self):
        """Test halaman batch creator render dengan benar."""
        self.client.force_login(self.organizer)
        url = reverse('manage_questions_batch')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'management/questions_batch.html')
        self.assertIn(self.competition, response.context['competitions'])

    def test_questions_batch_create_post_success(self):
        """Test menyimpan daftar banyak soal sekaligus (MCQ dan Essay) dalam satu request atomik."""
        self.client.force_login(self.organizer)
        url = reverse('manage_questions_batch')

        batch_payload = [
            {
                "title": "Analisis OS Command Injection",
                "type": "MCQ",
                "points": 10.0,
                "body": "Diberikan script ping.php yang menerima parameter host. Karakter apa untuk chaining?",
                "rubric": "Operator ; atau &&",
                "options": [
                    {"option_text": "; atau &&", "is_correct": True},
                    {"option_text": "-- SQL comment", "is_correct": False},
                    {"option_text": "<!-- html -->", "is_correct": False},
                    {"option_text": "None", "is_correct": False}
                ]
            },
            {
                "title": "Eksploitasi Prototype Pollution",
                "type": "ESSAY",
                "points": 25.0,
                "body": "Jelaskan mekanisme payload __proto__ pada merge function di NodeJS.",
                "rubric": "Rubrik: Prototype chain lookup dan tampering Object.prototype."
            }
        ]

        response = self.client.post(url, {
            'competition_id': str(self.competition.id),
            'batch_data': json.dumps(batch_payload)
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['count'], 2)

        # Verifikasi soal tersimpan di database
        questions = Question.objects.filter(competition=self.competition).order_by('sequence')
        self.assertEqual(questions.count(), 2)

        # Cek soal pertama (MCQ)
        mcq = questions[0]
        self.assertEqual(mcq.type, QuestionType.MCQ)
        self.assertEqual(mcq.points, Decimal('10.00'))
        self.assertEqual(mcq.options.count(), 4)
        correct_opts = mcq.options.filter(is_correct=True)
        self.assertEqual(correct_opts.count(), 1)
        self.assertEqual(correct_opts.first().option_text, "; atau &&")

        # Cek soal kedua (ESSAY)
        essay = questions[1]
        self.assertEqual(essay.type, QuestionType.ESSAY)
        self.assertEqual(essay.points, Decimal('25.00'))
        self.assertIn("Prototype chain lookup", essay.rubric_guidelines)

        # Cek Audit Log tercipta
        audit_log = SecurityAuditLog.objects.filter(
            user=self.organizer,
            event_type=AuditEventType.QUESTION_CREATE
        ).exists()
        self.assertTrue(audit_log)

    def test_judge_can_access_live_monitoring_and_ranking(self):
        """Test Dewan Juri diizinkan melihat Live Monitoring dan Papan Peringkat (Ranking)."""
        self.client.force_login(self.judge)

        # 1. Akses Live Monitoring
        resp_mon = self.client.get(reverse('manage_attempts'))
        self.assertEqual(resp_mon.status_code, 200)
        self.assertTrue(resp_mon.context['is_judge'])

        # 2. Akses Papan Peringkat (Ranking)
        resp_rank = self.client.get(reverse('manage_ranking'))
        self.assertEqual(resp_rank.status_code, 200)

    def test_ranking_and_attempts_sort_by_highest_score(self):
        """Test pemeringkatan dan filter berdasarkan Poin Paling Banyak (skor tertinggi)."""
        # Buat peserta kedua
        p2 = User.objects.create_user(username='participant_hacker2', password='Password123!', email='p2@test.com', role=UserRole.PARTICIPANT)

        # Sesi p1: skor 70
        att1 = ExamAttempt.objects.create(
            participant=self.participant,
            competition=self.competition,
            start_time=self.now - timedelta(minutes=45),
            submitted_at=self.now - timedelta(minutes=10),
            server_deadline=self.now + timedelta(minutes=45),
            status=AttemptStatus.SUBMITTED
        )
        AttemptGrade.objects.create(attempt=att1, mcq_score=Decimal('50.00'), essay_score=Decimal('20.00'), total_score=Decimal('70.00'))

        # Sesi p2: skor 95 (Juara 1)
        att2 = ExamAttempt.objects.create(
            participant=p2,
            competition=self.competition,
            start_time=self.now - timedelta(minutes=50),
            submitted_at=self.now - timedelta(minutes=5),
            server_deadline=self.now + timedelta(minutes=40),
            status=AttemptStatus.SUBMITTED
        )
        AttemptGrade.objects.create(attempt=att2, mcq_score=Decimal('50.00'), essay_score=Decimal('45.00'), total_score=Decimal('95.00'))

        self.client.force_login(self.judge)

        # Cek Papan Peringkat
        resp_rank = self.client.get(reverse('manage_ranking'))
        self.assertEqual(resp_rank.status_code, 200)
        ranked = resp_rank.context['ranked_list']
        self.assertEqual(len(ranked), 2)
        # Peringkat 1 harus p2 dengan skor 95
        self.assertEqual(ranked[0]['rank'], 1)
        self.assertEqual(ranked[0]['attempt'].participant, p2)
        self.assertEqual(ranked[0]['grade'].total_score, Decimal('95.00'))

        # Peringkat 2 harus p1 dengan skor 70
        self.assertEqual(ranked[1]['rank'], 2)
        self.assertEqual(ranked[1]['attempt'].participant, self.participant)

    def test_attempts_search_filter(self):
        """Test pencarian peserta di live monitoring dan leaderboard."""
        att1 = ExamAttempt.objects.create(
            participant=self.participant,
            competition=self.competition,
            start_time=self.now - timedelta(minutes=10),
            server_deadline=self.now + timedelta(minutes=80),
            status=AttemptStatus.IN_PROGRESS
        )

        self.client.force_login(self.judge)
        # Cari kata kunci yang cocok
        resp = self.client.get(reverse('manage_attempts') + f"?q={self.participant.username}")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(att1, resp.context['attempts'])

        # Cari kata kunci yang tidak cocok
        resp_empty = self.client.get(reverse('manage_attempts') + "?q=nonexistentuserxyz")
        self.assertEqual(resp_empty.status_code, 200)
        self.assertNotIn(att1, resp_empty.context['attempts'])

    def test_questions_can_exceed_one_hundred(self):
        """Test sistem mendukung lebih dari 100 soal tanpa batasan teknis."""
        # Buat 105 soal untuk kompetisi
        bulk_questions = [
            Question(
                competition=self.competition,
                title=f"Soal Tantangan Siber #{i}",
                body=f"Narasi soal siber ke-{i}...",
                type=QuestionType.MCQ,
                points=Decimal('10.00'),
                sequence=i,
                status=QuestionStatus.APPROVED,
                created_by=self.organizer
            )
            for i in range(1, 106)
        ]
        Question.objects.bulk_create(bulk_questions)

        self.assertEqual(Question.objects.filter(competition=self.competition).count(), 105)

        # Cek soal ke-105 dapat dicari dan dimuat
        q105 = Question.objects.get(competition=self.competition, sequence=105)
        self.assertEqual(q105.title, "Soal Tantangan Siber #105")

        self.client.force_login(self.organizer)
        resp = self.client.get(reverse('manage_questions') + f"?competition_id={self.competition.id}&q=105")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(q105, resp.context['questions'])
