import uuid
from django.conf import settings
from django.db import models


class AttemptGrade(models.Model):
    """
    Model Akumulasi Nilai Ujian Peserta.
    Menggabungkan auto-scoring pilihan ganda dan penilaian manual essay oleh juri.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt = models.OneToOneField(
        'attempts.ExamAttempt',
        on_delete=models.CASCADE,
        related_name='grade'
    )
    mcq_score = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        default=0.00,
        help_text="Total nilai pilihan ganda dari auto-scoring"
    )
    essay_score = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        default=0.00,
        help_text="Total nilai essay dari juri"
    )
    total_score = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        default=0.00,
        help_text="Total skor gabungan"
    )
    is_finalized = models.BooleanField(
        default=False,
        help_text="Status finalisasi nilai oleh organizer/panitia"
    )
    finalized_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='finalized_grades'
    )
    graded_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'quiz_attempt_grades'
        verbose_name = 'Attempt Grade'
        verbose_name_plural = 'Attempt Grades'
        ordering = ['-total_score']

    def __str__(self) -> str:
        return f"Grade for {self.attempt}: Total {self.total_score} (Final: {self.is_finalized})"

    def recalculate_total(self) -> None:
        """Kalkulasi ulang total skor."""
        from decimal import Decimal
        mcq = Decimal(str(self.mcq_score or '0.00'))
        essay = Decimal(str(self.essay_score or '0.00'))
        self.total_score = mcq + essay


class EssayEvaluation(models.Model):
    """
    Model Penilaian Manual Jawaban Essay oleh Juri.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt_answer = models.ForeignKey(
        'attempts.AttemptAnswer',
        on_delete=models.CASCADE,
        related_name='essay_evaluations'
    )
    judge = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='judged_evaluations'
    )
    score_awarded = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        help_text="Nilai yang diberikan juri"
    )
    feedback = models.TextField(blank=True, help_text="Catatan atau feedback juri (dapat dilihat oleh peserta jika diizinkan)")
    internal_notes = models.TextField(blank=True, default='', help_text="Catatan rahasia dewan juri / deliberasi internal (hanya juri & panitia)")
    is_flagged_for_review = models.BooleanField(default=False, help_text="Tandai jika jawaban perlu didiskusikan / dieskalasi ke juri kepala")
    dispute_reason = models.CharField(max_length=255, blank=True, default='', help_text="Alasan eskalasi / sengketa penilaian")
    evaluated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'quiz_essay_evaluations'
        verbose_name = 'Essay Evaluation'
        verbose_name_plural = 'Essay Evaluations'
        constraints = [
            models.UniqueConstraint(
                fields=['attempt_answer', 'judge'],
                name='unique_judge_evaluation_per_answer'
            )
        ]

    def __str__(self) -> str:
        return f"Judge {self.judge.username} gave {self.score_awarded} to Answer {self.attempt_answer.id}"
