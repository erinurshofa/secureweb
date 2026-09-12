import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class UserRole(models.TextChoices):
    DEVELOPER = 'DEVELOPER', 'Lead Developer / DevSecOps'
    SUPER_ADMIN = 'SUPER_ADMIN', 'Super Admin'
    ORGANIZER = 'ORGANIZER', 'Organizer'
    AUTHOR = 'AUTHOR', 'Question Author'
    REVIEWER = 'REVIEWER', 'Reviewer'
    JUDGE = 'JUDGE', 'Judge'
    PARTICIPANT = 'PARTICIPANT', 'Participant'
    AUDITOR = 'AUDITOR', 'Auditor / Observer'


class User(AbstractUser):
    """
    Custom User Model untuk Secure Web Quiz Platform.
    Mendukung Role-Based Access Control (RBAC) ketat untuk kompetisi hacker.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.PARTICIPANT,
        db_index=True,
        help_text="Peran pengguna dalam ekosistem lomba."
    )
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    institution = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        help_text="Asal instansi/kampus/sekolah/tim"
    )
    last_login_ip = models.GenericIPAddressField(
        blank=True,
        null=True,
        help_text="IP address login terakhir untuk audit trail"
    )

    class Meta:
        db_table = 'auth_users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['role', 'is_active']),
        ]

    def __str__(self) -> str:
        return f"{self.username} [{self.get_role_display()}]"

    @property
    def is_participant(self) -> bool:
        return self.role == UserRole.PARTICIPANT

    @property
    def is_judge(self) -> bool:
        return self.role == UserRole.JUDGE or self.is_superuser

    @property
    def is_author(self) -> bool:
        return self.role in (UserRole.AUTHOR, UserRole.ORGANIZER) or self.is_superuser

    @property
    def is_organizer(self) -> bool:
        return self.role == UserRole.ORGANIZER or self.is_superuser
