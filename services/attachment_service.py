"""
Attachment Service Layer — Otorisasi Unduh Berbatas Waktu & Sandbox Keamanan File.
Mencegah direct URL traversal dan membatasi akses file challenge khusus peserta terotorisasi.
"""

from datetime import timedelta
from typing import Optional
from django.utils import timezone
from django.core.exceptions import PermissionDenied, ValidationError

from accounts.models import User, UserRole
from questions.models import QuestionAttachment, AttachmentDownloadToken
from attempts.models import ExamAttempt, AttemptStatus
from audit.models import SecurityAuditLog, AuditEventType


class AttachmentService:
    TOKEN_LIFETIME_MINUTES = 5

    @classmethod
    def generate_download_token(
        cls,
        user: User,
        attachment_id: str,
        ip_address: Optional[str] = None
    ) -> AttachmentDownloadToken:
        """
        Membuat token unduhan sementara (5 menit) setelah memvalidasi otorisasi peserta.
        """
        attachment = QuestionAttachment.objects.select_related(
            'question',
            'question__competition'
        ).get(id=attachment_id)
        competition = attachment.question.competition

        # 1. Bypass otorisasi untuk staff / juri / author
        if user.role not in (UserRole.PARTICIPANT,):
            pass
        else:
            # 2. Peserta wajib memiliki attempt aktif
            has_active_attempt = ExamAttempt.objects.filter(
                competition=competition,
                participant=user,
                status=AttemptStatus.IN_PROGRESS
            ).exists()
            
            if not has_active_attempt:
                raise PermissionDenied("Anda harus memiliki sesi ujian aktif untuk mengunduh attachment ini.")

        now = timezone.now()
        token = AttachmentDownloadToken.objects.create(
            attachment=attachment,
            user=user,
            expires_at=now + timedelta(minutes=cls.TOKEN_LIFETIME_MINUTES)
        )

        return token

    @classmethod
    def consume_download_token(
        cls,
        token_str: str,
        user: User,
        ip_address: Optional[str] = None
    ) -> QuestionAttachment:
        """
        Memvalidasi token unduhan dan mencatat riwayat audit download file.
        """
        try:
            token = AttachmentDownloadToken.objects.select_related(
                'attachment',
                'attachment__question'
            ).get(token=token_str, user=user)
        except AttachmentDownloadToken.DoesNotExist:
            raise PermissionDenied("Token unduhan tidak valid.")

        if not token.is_valid():
            raise ValidationError("Token unduhan telah kadaluarsa atau sudah digunakan.")

        # Tandai token digunakan
        token.is_used = True
        token.save(update_fields=['is_used'])

        # Increment download counter
        attachment = token.attachment
        attachment.download_count += 1
        attachment.save(update_fields=['download_count'])

        # Catat audit log forensik
        SecurityAuditLog.objects.create(
            user=user,
            event_type=AuditEventType.DOWNLOAD_ATTACHMENT,
            ip_address=ip_address,
            details={
                'attachment_id': str(attachment.id),
                'filename': attachment.original_filename,
                'sha256': attachment.sha256_hash,
                'token': str(token.token),
            }
        )

        return attachment
