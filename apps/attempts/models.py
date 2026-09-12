import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone


class AttemptStatus(models.TextChoices):
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    SUBMITTED = 'SUBMITTED', 'Submitted'
    AUTO_SUBMITTED = 'AUTO_SUBMITTED', 'Auto Submitted'
    DISQUALIFIED = 'DISQUALIFIED', 'Disqualified'


class ExamAttempt(models.Model):
    """
    Model Sesi Pengerjaan Ujian (Attempt).
    Waktu deadline dihitung murni di backend (server_deadline).
    Mencegah manipulasi countdown timer browser.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    competition = models.ForeignKey(
        'competitions.Competition',
        on_delete=models.CASCADE,
        related_name='attempts'
    )
    participant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='exam_attempts'
    )
    attempt_number = models.PositiveIntegerField(default=1)
    
    start_time = models.DateTimeField(
        help_text="Timestamp server saat peserta menekan Mulai Ujian"
    )
    server_deadline = models.DateTimeField(
        help_text="Batas waktu absolut pengerjaan yang ditegakkan server"
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    
    status = models.CharField(
        max_length=20,
        choices=AttemptStatus.choices,
        default=AttemptStatus.IN_PROGRESS,
        db_index=True
    )
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'quiz_exam_attempts'
        verbose_name = 'Exam Attempt'
        verbose_name_plural = 'Exam Attempts'
        constraints = [
            models.UniqueConstraint(
                fields=['competition', 'participant', 'attempt_number'],
                name='unique_attempt_per_number'
            )
        ]
        indexes = [
            models.Index(fields=['participant', 'status']),
            models.Index(fields=['competition', 'status']),
        ]

    def __str__(self) -> str:
        return f"Attempt #{self.attempt_number} by {self.participant.username} ({self.competition.title})"

    def is_expired(self) -> bool:
        """Memeriksa apakah server deadline telah terlewati."""
        return timezone.now() > self.server_deadline

    def time_remaining_seconds(self) -> int:
        """Menghitung sisa detik pengerjaan berdasarkan jam backend server."""
        if self.status != AttemptStatus.IN_PROGRESS:
            return 0
        diff = (self.server_deadline - timezone.now()).total_seconds()
        return max(0, int(diff))

    def can_modify_answers(self) -> bool:
        """Validasi backend apakah peserta masih berhak menyimpan jawaban."""
        return self.status == AttemptStatus.IN_PROGRESS and not self.is_expired()


class AttemptAnswer(models.Model):
    """
    Model Penyimpanan Jawaban Peserta (Autosave & Final).
    Satu record per kombinasi attempt dan soal.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt = models.ForeignKey(
        ExamAttempt,
        on_delete=models.CASCADE,
        related_name='answers'
    )
    question = models.ForeignKey(
        'questions.Question',
        on_delete=models.CASCADE,
        related_name='participant_answers'
    )
    selected_option = models.ForeignKey(
        'questions.QuestionOption',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='selected_by_answers'
    )
    essay_text = models.TextField(blank=True, default='')
    saved_at = models.DateTimeField(auto_now=True)
    revision_count = models.PositiveIntegerField(default=1)
    is_flagged_for_review = models.BooleanField(
        default=False,
        help_text="Penanda ragu-ragu oleh peserta"
    )

    class Meta:
        db_table = 'quiz_attempt_answers'
        verbose_name = 'Attempt Answer'
        verbose_name_plural = 'Attempt Answers'
        constraints = [
            models.UniqueConstraint(
                fields=['attempt', 'question'],
                name='unique_answer_per_attempt_question'
            )
        ]

    def __str__(self) -> str:
        return f"Answer for Q:{self.question.sequence} in Attempt:{self.attempt.id}"


class AnswerHistoryLog(models.Model):
    """
    Audit log anti-tampering untuk setiap kali jawaban di-autosave / diubah.
    Menyimpan payload perubahan beserta timestamp presisi dan IP address.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt_answer = models.ForeignKey(
        AttemptAnswer,
        on_delete=models.CASCADE,
        related_name='history_logs'
    )
    selected_option_id = models.UUIDField(null=True, blank=True)
    essay_text = models.TextField(blank=True)
    saved_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    revision = models.PositiveIntegerField()

    class Meta:
        db_table = 'quiz_answer_history_logs'
        verbose_name = 'Answer History Log'
        verbose_name_plural = 'Answer History Logs'
        ordering = ['-saved_at']

    def __str__(self) -> str:
        return f"Rev {self.revision} - {self.attempt_answer.id} at {self.saved_at}"
