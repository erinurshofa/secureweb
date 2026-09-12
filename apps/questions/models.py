import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone


class QuestionType(models.TextChoices):
    MCQ = 'MCQ', 'Pilihan Ganda'
    ESSAY = 'ESSAY', 'Essay'


class QuestionStatus(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft'
    IN_REVIEW = 'IN_REVIEW', 'In Review'
    APPROVED = 'APPROVED', 'Approved'
    INVALIDATED = 'INVALIDATED', 'Invalidated (Dibatalkan)'


class Question(models.Model):
    """
    Model Bank Soal Ujian (Pilihan Ganda & Essay).
    Mendukung versioning untuk audit integritas dan recalculation.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    competition = models.ForeignKey(
        'competitions.Competition',
        on_delete=models.CASCADE,
        related_name='questions'
    )
    type = models.CharField(
        max_length=10,
        choices=QuestionType.choices,
        default=QuestionType.MCQ,
        db_index=True
    )
    title = models.CharField(max_length=255)
    body = models.TextField(help_text="Konten soal (mendukung formatting teks/markdown)")
    points = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=10.00,
        help_text="Bobot nilai soal"
    )
    rubric_guidelines = models.TextField(
        blank=True,
        default='',
        help_text="Pedoman rubrik penilaian, poin kunci eksploitasi, dan kunci jawaban bagi dewan juri"
    )
    sequence = models.PositiveIntegerField(
        default=1,
        help_text="Urutan tampilan default soal"
    )
    status = models.CharField(
        max_length=15,
        choices=QuestionStatus.choices,
        default=QuestionStatus.DRAFT,
        db_index=True
    )
    version = models.PositiveIntegerField(
        default=1,
        help_text="Nomor versi soal jika terjadi revisi sebelum kuis freeze"
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_questions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'quiz_questions'
        verbose_name = 'Question'
        verbose_name_plural = 'Questions'
        ordering = ['competition', 'sequence']
        indexes = [
            models.Index(fields=['competition', 'status']),
        ]

    def __str__(self) -> str:
        return f"[{self.get_type_display()}] {self.title} ({self.competition.title})"


class QuestionOption(models.Model):
    """
    Model Pilihan Jawaban untuk Soal Pilihan Ganda (MCQ).
    Field is_correct HANYA boleh diakses oleh backend / admin, dilarang bocor ke API peserta.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='options'
    )
    option_text = models.TextField()
    is_correct = models.BooleanField(
        default=False,
        help_text="Kunci jawaban benar (DILINDUNGI DARI CLIENT)"
    )
    order = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = 'quiz_question_options'
        verbose_name = 'Question Option'
        verbose_name_plural = 'Question Options'
        ordering = ['order']

    def __str__(self) -> str:
        return f"Option for {self.question.title[:30]}: {self.option_text[:40]}"


class QuestionAttachment(models.Model):
    """
    Model Attachment / File Tantangan Soal (PCAP, Binary, Source Code, ZIP).
    Disimpan di storage sandbox terisolasi, divalidasi checksum SHA256.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file = models.FileField(
        upload_to='quarantine/%Y/%m/',
        help_text="File challenge yang disimpan di quarantine sandbox"
    )
    original_filename = models.CharField(max_length=255)
    display_filename = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=100, default='application/octet-stream')
    file_size = models.BigIntegerField(help_text="Ukuran file dalam bytes")
    sha256_hash = models.CharField(max_length=64, help_text="SHA-256 integrity checksum")
    download_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'quiz_question_attachments'
        verbose_name = 'Question Attachment'
        verbose_name_plural = 'Question Attachments'

    def __str__(self) -> str:
        return f"{self.display_filename} ({self.file_size} bytes)"


class AttachmentDownloadToken(models.Model):
    """
    Token berbatas waktu untuk otorisasi download attachment soal.
    Mencegah direct URL traversal / link sharing tanpa izin aktif.
    """
    token = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attachment = models.ForeignKey(
        QuestionAttachment,
        on_delete=models.CASCADE,
        related_name='download_tokens'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='download_tokens'
    )
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'quiz_attachment_tokens'
        indexes = [
            models.Index(fields=['token', 'expires_at', 'is_used']),
        ]

    def is_valid(self) -> bool:
        return not self.is_used and timezone.now() <= self.expires_at
