import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone


class CompetitionStatus(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft'
    PUBLISHED = 'PUBLISHED', 'Published (Akan Datang)'
    FROZEN = 'FROZEN', 'Frozen (Soal Dikunci)'
    OPEN = 'OPEN', 'Open (Sedang Berlangsung)'
    CLOSED = 'CLOSED', 'Closed (Selesai)'
    ARCHIVED = 'ARCHIVED', 'Archived'


class Competition(models.Model):
    """
    Model Kompetisi / Babak Ujian Lomba Hacker.
    Menyimpan konfigurasi jadwal, durasi, status freeze, dan aturan ujian.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    
    start_time = models.DateTimeField(help_text="Jadwal kompetisi mulai dibuka")
    end_time = models.DateTimeField(help_text="Batas waktu kompetisi berakhir")
    duration_minutes = models.PositiveIntegerField(
        default=90,
        help_text="Durasi pengerjaan per attempt dalam menit"
    )
    
    status = models.CharField(
        max_length=20,
        choices=CompetitionStatus.choices,
        default=CompetitionStatus.DRAFT,
        db_index=True
    )
    
    max_attempts = models.PositiveIntegerField(
        default=1,
        help_text="Jumlah maksimal attempt yang diizinkan per peserta"
    )
    is_randomized_questions = models.BooleanField(
        default=False,
        help_text="Acak urutan soal untuk setiap peserta"
    )
    is_randomized_options = models.BooleanField(
        default=False,
        help_text="Acak pilihan jawaban MCQ untuk setiap peserta"
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_competitions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'quiz_competitions'
        verbose_name = 'Competition'
        verbose_name_plural = 'Competitions'
        ordering = ['-start_time']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_time__gt=models.F('start_time')),
                name='check_competition_end_after_start'
            )
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.get_status_display()})"

    @property
    def is_currently_open(self) -> bool:
        now = timezone.now()
        return self.status == CompetitionStatus.OPEN and self.start_time <= now <= self.end_time


class ParticipantEnrollment(models.Model):
    """
    Tabel relasi pendaftaran peserta ke dalam kompetisi tertentu.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    competition = models.ForeignKey(
        Competition,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    participant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='competition_enrollments'
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)
    is_disqualified = models.BooleanField(default=False)
    disqualification_reason = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'quiz_participant_enrollments'
        constraints = [
            models.UniqueConstraint(
                fields=['competition', 'participant'],
                name='unique_participant_per_competition'
            )
        ]

    def __str__(self) -> str:
        return f"{self.participant.username} -> {self.competition.title}"
