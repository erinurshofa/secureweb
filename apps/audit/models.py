import uuid
from django.conf import settings
from django.db import models


class AuditEventType(models.TextChoices):
    LOGIN = 'LOGIN', 'User Login'
    LOGOUT = 'LOGOUT', 'User Logout'
    START_EXAM = 'START_EXAM', 'Start Exam Attempt'
    AUTOSAVE_ANSWER = 'AUTOSAVE_ANSWER', 'Autosave Answer'
    FINAL_SUBMIT = 'FINAL_SUBMIT', 'Final Submit Exam'
    DOWNLOAD_ATTACHMENT = 'DOWNLOAD_ATTACHMENT', 'Download Challenge Attachment'
    QUESTION_CREATE = 'QUESTION_CREATE', 'Create Question'
    QUESTION_UPDATE = 'QUESTION_UPDATE', 'Update Question'
    QUESTION_INVALIDATE = 'QUESTION_INVALIDATE', 'Invalidate Question'
    GRADE_ESSAY = 'GRADE_ESSAY', 'Grade Essay Answer'
    FINALIZE_SCORE = 'FINALIZE_SCORE', 'Finalize Score'
    SUSPICIOUS_ACTIVITY = 'SUSPICIOUS_ACTIVITY', 'Suspicious Activity Detected'


class SecurityAuditLog(models.Model):
    """
    Log Audit Keamanan dan Aktivitas Ujian yang Tidak Dapat Diubah (Immutable).
    Mencatat jejak digital setiap aksi kritis untuk pembuktian forensik dan integritas lomba.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    event_type = models.CharField(
        max_length=30,
        choices=AuditEventType.choices,
        db_index=True
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default='')
    path = models.CharField(max_length=255, blank=True, default='')
    details = models.JSONField(
        default=dict,
        help_text="Metadata terstruktur seputar aksi (IDs, hash, previous values, delta)"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'quiz_security_audit_logs'
        verbose_name = 'Security Audit Log'
        verbose_name_plural = 'Security Audit Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event_type', 'created_at']),
            models.Index(fields=['user', 'event_type']),
        ]

    def __str__(self) -> str:
        username = self.user.username if self.user else 'Anonymous'
        return f"[{self.created_at:%Y-%m-%d %H:%M:%S}] {self.get_event_type_display()} by {username} ({self.ip_address})"
