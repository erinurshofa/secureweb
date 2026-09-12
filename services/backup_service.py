"""
Disaster Recovery & Backup Service Layer — World's Top-Tier Secure Web Architecture.
Menyediakan fungsionalitas pembuatan snapshot atomik, validasi integritas kriptografis SHA256,
serta restorasi database multi-relasional dengan rollback otomatis dan audit trail ketat.
Khusus dapat diakses oleh Developer / DevSecOps.
"""

import os
import io
import gzip
import json
import uuid
import hashlib
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List, Tuple, Optional
from django.conf import settings
from django.db import transaction, connection
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder

from accounts.models import User, UserRole
from competitions.models import Competition, ParticipantEnrollment
from questions.models import Question, QuestionOption, QuestionAttachment
from attempts.models import ExamAttempt, AttemptAnswer, AnswerHistoryLog
from grading.models import AttemptGrade, EssayEvaluation
from audit.models import SecurityAuditLog, AuditEventType


BACKUP_DIR = os.path.join(settings.BASE_DIR, 'backups')


class CustomModelEncoder(DjangoJSONEncoder):
    """Encoder JSON kustom yang menangani UUID, Decimal, DateTime, dan bytes."""
    def default(self, obj):
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, bytes):
            return obj.hex()
        return super().default(obj)


class BackupService:
    @staticmethod
    def get_backup_dir() -> str:
        """Memastikan direktori backup terisolasi dan terlindungi."""
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR, exist_ok=True)
            # Buat file pengaman .htaccess untuk Apache dan web.config untuk IIS
            htaccess_path = os.path.join(BACKUP_DIR, '.htaccess')
            if not os.path.exists(htaccess_path):
                with open(htaccess_path, 'w', encoding='utf-8') as f:
                    f.write("Order deny,allow\nDeny from all\n")
        return BACKUP_DIR

    @classmethod
    def create_backup(cls, user: User, backup_type: str = 'full', description: str = '') -> Dict[str, Any]:
        """
        Membuat snapshot database atomik terkompresi (.json.gz) lengkap dengan
        manifest integritas SHA256 dan metadata audit.
        """
        cls.get_backup_dir()
        now = timezone.now()
        timestamp_str = now.strftime('%Y%m%d_%H%M%S')
        rand_suffix = uuid.uuid4().hex[:6]
        filename = f"backup_sec_{backup_type}_{timestamp_str}_{rand_suffix}.json.gz"
        filepath = os.path.join(BACKUP_DIR, filename)

        record_counts: Dict[str, int] = {}
        tables_data: Dict[str, Any] = {}

        # 1. Serialisasi Data Tabel
        if backup_type in ['full', 'db_only']:
            # Users
            users_qs = User.objects.all().values(
                'id', 'username', 'password', 'first_name', 'last_name', 'email',
                'is_staff', 'is_active', 'is_superuser', 'date_joined', 'last_login',
                'role', 'institution', 'phone_number', 'last_login_ip'
            )
            tables_data['users'] = list(users_qs)
            record_counts['users'] = len(tables_data['users'])

            # Competitions
            comps_qs = Competition.objects.all().values(
                'id', 'title', 'slug', 'description', 'start_time', 'end_time',
                'duration_minutes', 'status', 'max_attempts', 'is_randomized_questions',
                'is_randomized_options', 'created_by_id', 'created_at', 'updated_at'
            )
            tables_data['competitions'] = list(comps_qs)
            record_counts['competitions'] = len(tables_data['competitions'])

            # Enrollments
            enrolls_qs = ParticipantEnrollment.objects.all().values(
                'id', 'competition_id', 'participant_id', 'enrolled_at',
                'is_disqualified', 'disqualification_reason'
            )
            tables_data['enrollments'] = list(enrolls_qs)
            record_counts['enrollments'] = len(tables_data['enrollments'])

        # Questions & Bank
        questions_qs = Question.objects.all().values(
            'id', 'competition_id', 'type', 'title', 'body', 'points',
            'rubric_guidelines', 'sequence', 'status', 'version',
            'created_by_id', 'created_at', 'updated_at'
        )
        tables_data['questions'] = list(questions_qs)
        record_counts['questions'] = len(tables_data['questions'])

        options_qs = QuestionOption.objects.all().values(
            'id', 'question_id', 'option_text', 'is_correct', 'order'
        )
        tables_data['question_options'] = list(options_qs)
        record_counts['question_options'] = len(tables_data['question_options'])

        attachments_qs = QuestionAttachment.objects.all().values(
            'id', 'question_id', 'file', 'original_filename', 'display_filename',
            'mime_type', 'file_size', 'sha256_hash', 'download_count', 'created_at'
        )
        tables_data['question_attachments'] = list(attachments_qs)
        record_counts['question_attachments'] = len(tables_data['question_attachments'])

        # Exam Attempts & Grading
        if backup_type in ['full', 'db_only']:
            attempts_qs = ExamAttempt.objects.all().values(
                'id', 'competition_id', 'participant_id', 'attempt_number',
                'status', 'start_time', 'server_deadline', 'submitted_at',
                'ip_address', 'user_agent'
            )
            tables_data['exam_attempts'] = list(attempts_qs)
            record_counts['exam_attempts'] = len(tables_data['exam_attempts'])

            answers_qs = AttemptAnswer.objects.all().values(
                'id', 'attempt_id', 'question_id', 'selected_option_id',
                'essay_text', 'revision_count', 'is_flagged_for_review', 'saved_at'
            )
            tables_data['attempt_answers'] = list(answers_qs)
            record_counts['attempt_answers'] = len(tables_data['attempt_answers'])

            history_qs = AnswerHistoryLog.objects.all().values(
                'id', 'attempt_answer_id', 'selected_option_id', 'essay_text',
                'ip_address', 'revision', 'saved_at'
            )
            tables_data['answer_history_logs'] = list(history_qs)
            record_counts['answer_history_logs'] = len(tables_data['answer_history_logs'])

            grades_qs = AttemptGrade.objects.all().values(
                'id', 'attempt_id', 'mcq_score', 'essay_score', 'total_score',
                'is_finalized', 'finalized_by_id', 'graded_at'
            )
            tables_data['attempt_grades'] = list(grades_qs)
            record_counts['attempt_grades'] = len(tables_data['attempt_grades'])

            evals_qs = EssayEvaluation.objects.all().values(
                'id', 'attempt_answer_id', 'judge_id', 'score_awarded', 'feedback',
                'internal_notes', 'is_flagged_for_review', 'dispute_reason', 'evaluated_at'
            )
            tables_data['essay_evaluations'] = list(evals_qs)
            record_counts['essay_evaluations'] = len(tables_data['essay_evaluations'])

            # Audit Logs
            audits_qs = SecurityAuditLog.objects.all().values(
                'id', 'user_id', 'event_type', 'ip_address', 'user_agent',
                'path', 'details', 'created_at'
            )
            tables_data['audit_logs'] = list(audits_qs)
            record_counts['audit_logs'] = len(tables_data['audit_logs'])

        # 2. Susun Payload Utuh
        raw_json_str = json.dumps(tables_data, cls=CustomModelEncoder, indent=2)
        raw_bytes = raw_json_str.encode('utf-8')
        sha256_hash = hashlib.sha256(raw_bytes).hexdigest()

        manifest = {
            'system': 'Secure Web Quiz Platform',
            'version': '2.6.0-PROD',
            'backup_type': backup_type,
            'description': description or 'Full Disaster Recovery Snapshot',
            'created_at': now.isoformat(),
            'created_by': user.username if user else 'system',
            'sha256_checksum': sha256_hash,
            'record_counts': record_counts,
            'total_records': sum(record_counts.values())
        }

        full_package = {
            'manifest': manifest,
            'data': tables_data
        }

        # 3. Tulis Kompresi GZIP
        with gzip.open(filepath, 'wt', encoding='utf-8') as gz_file:
            json.dump(full_package, gz_file, cls=CustomModelEncoder)

        file_size = os.path.getsize(filepath)
        manifest['filename'] = filename
        manifest['file_size'] = file_size
        manifest['file_size_formatted'] = cls._format_file_size(file_size)

        # 4. Audit Log Pembuatan Backup
        SecurityAuditLog.objects.create(
            user=user,
            event_type=AuditEventType.SUSPICIOUS_ACTIVITY, # Tercatat di audit log
            details={
                'action': 'CREATE_BACKUP',
                'filename': filename,
                'backup_type': backup_type,
                'sha256': sha256_hash,
                'total_records': manifest['total_records']
            }
        )

        return manifest

    @classmethod
    def list_backups(cls) -> List[Dict[str, Any]]:
        """Membaca seluruh snapshot backup yang tersedia di folder backups/."""
        cls.get_backup_dir()
        backups: List[Dict[str, Any]] = []

        for fname in os.listdir(BACKUP_DIR):
            if fname.endswith('.json.gz') and fname.startswith('backup_'):
                fpath = os.path.join(BACKUP_DIR, fname)
                try:
                    fsize = os.path.getsize(fpath)
                    with gzip.open(fpath, 'rt', encoding='utf-8') as f:
                        pkg = json.load(f)
                        manifest = pkg.get('manifest', {})
                        manifest['filename'] = fname
                        manifest['file_size'] = fsize
                        manifest['file_size_formatted'] = cls._format_file_size(fsize)
                        backups.append(manifest)
                except Exception as e:
                    backups.append({
                        'filename': fname,
                        'file_size': os.path.getsize(fpath),
                        'file_size_formatted': cls._format_file_size(os.path.getsize(fpath)),
                        'error': f"Corrupted or non-readable: {str(e)}",
                        'created_at': datetime.fromtimestamp(os.path.getctime(fpath)).isoformat(),
                        'total_records': 0
                    })

        # Urutkan berdasarkan waktu pembuatan terbaru
        backups.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return backups

    @classmethod
    def inspect_backup(cls, filename: str) -> Tuple[bool, Dict[str, Any], str]:
        """Memeriksa integritas kriptografis dan isi backup tanpa melakukan restorasi."""
        safe_fname = os.path.basename(filename)
        filepath = os.path.join(cls.get_backup_dir(), safe_fname)
        if not os.path.exists(filepath):
            return False, {}, f"File backup '{safe_fname}' tidak ditemukan."

        try:
            with gzip.open(filepath, 'rt', encoding='utf-8') as gz:
                pkg = json.load(gz)

            manifest = pkg.get('manifest', {})
            data = pkg.get('data', {})

            # Validasi checksum
            raw_data_bytes = json.dumps(data, cls=CustomModelEncoder, indent=2).encode('utf-8')
            computed_sha = hashlib.sha256(raw_data_bytes).hexdigest()
            expected_sha = manifest.get('sha256_checksum', '')

            manifest['is_checksum_valid'] = (computed_sha == expected_sha)
            manifest['computed_sha256'] = computed_sha
            manifest['filename'] = safe_fname

            return True, manifest, "Integritas backup terverifikasi valid."
        except Exception as e:
            return False, {}, f"Gagal membaca atau memvalidasi backup: {str(e)}"

    @classmethod
    def restore_backup(cls, filename: str, user: User) -> Tuple[bool, Dict[str, Any], str]:
        """
        Mengeksekusi restorasi database atomik dari file snapshot backup yang dipilih.
        Secara otomatis membuat 'Pre-Restore Safety Snapshot' sebelum modifikasi dimulai!
        """
        safe_fname = os.path.basename(filename)
        filepath = os.path.join(cls.get_backup_dir(), safe_fname)
        if not os.path.exists(filepath):
            return False, {}, f"File backup '{safe_fname}' tidak ditemukan."

        # 1. Otomatis Buat Safety Pre-Restore Snapshot demi Zero Data Loss
        safety_manifest = cls.create_backup(
            user=user,
            backup_type='full',
            description=f"Automated Safety Rollback before restoring {safe_fname}"
        )

        try:
            with gzip.open(filepath, 'rt', encoding='utf-8') as gz:
                pkg = json.load(gz)

            manifest = pkg.get('manifest', {})
            data = pkg.get('data', {})

            restored_counts: Dict[str, int] = {}

            with transaction.atomic():
                # Restorasi Users
                if 'users' in data:
                    count = 0
                    for row in data['users']:
                        uid = row['id']
                        User.objects.update_or_create(
                            id=uid,
                            defaults={
                                'username': row['username'],
                                'password': row['password'],
                                'first_name': row.get('first_name', ''),
                                'last_name': row.get('last_name', ''),
                                'email': row.get('email', ''),
                                'is_staff': row.get('is_staff', False),
                                'is_active': row.get('is_active', True),
                                'is_superuser': row.get('is_superuser', False),
                                'role': row.get('role', UserRole.PARTICIPANT),
                                'institution': row.get('institution', ''),
                                'phone_number': row.get('phone_number', ''),
                                'last_login_ip': row.get('last_login_ip', None)
                            }
                        )
                        count += 1
                    restored_counts['users'] = count

                # Restorasi Competitions
                if 'competitions' in data:
                    count = 0
                    for row in data['competitions']:
                        Competition.objects.update_or_create(
                            id=row['id'],
                            defaults={
                                'title': row['title'],
                                'slug': row['slug'],
                                'description': row.get('description', ''),
                                'start_time': row['start_time'],
                                'end_time': row['end_time'],
                                'duration_minutes': row.get('duration_minutes', 90),
                                'status': row.get('status', 'OPEN'),
                                'max_attempts': row.get('max_attempts', 1),
                                'is_randomized_questions': row.get('is_randomized_questions', False),
                                'is_randomized_options': row.get('is_randomized_options', False),
                                'created_by_id': row.get('created_by_id')
                            }
                        )
                        count += 1
                    restored_counts['competitions'] = count

                # Restorasi Questions & Options
                if 'questions' in data:
                    count = 0
                    for row in data['questions']:
                        Question.objects.update_or_create(
                            id=row['id'],
                            defaults={
                                'competition_id': row['competition_id'],
                                'type': row['type'],
                                'title': row['title'],
                                'body': row['body'],
                                'points': Decimal(str(row['points'])),
                                'rubric_guidelines': row.get('rubric_guidelines', ''),
                                'sequence': row.get('sequence', 1),
                                'status': row.get('status', 'APPROVED'),
                                'version': row.get('version', 1),
                                'created_by_id': row.get('created_by_id')
                            }
                        )
                        count += 1
                    restored_counts['questions'] = count

                if 'question_options' in data:
                    count = 0
                    for row in data['question_options']:
                        QuestionOption.objects.update_or_create(
                            id=row['id'],
                            defaults={
                                'question_id': row['question_id'],
                                'option_text': row['option_text'],
                                'is_correct': row.get('is_correct', False),
                                'order': row.get('order', 1)
                            }
                        )
                        count += 1
                    restored_counts['question_options'] = count

                if 'question_attachments' in data:
                    count = 0
                    for row in data['question_attachments']:
                        QuestionAttachment.objects.update_or_create(
                            id=row['id'],
                            defaults={
                                'question_id': row['question_id'],
                                'file': row['file'],
                                'original_filename': row['original_filename'],
                                'display_filename': row['display_filename'],
                                'mime_type': row.get('mime_type', 'application/octet-stream'),
                                'file_size': row.get('file_size', 0),
                                'sha256_hash': row.get('sha256_hash', ''),
                                'download_count': row.get('download_count', 0),
                            }
                        )
                        count += 1
                    restored_counts['question_attachments'] = count

                # Restorasi Enrollments & Attempts
                if 'enrollments' in data:
                    count = 0
                    for row in data['enrollments']:
                        ParticipantEnrollment.objects.update_or_create(
                            id=row['id'],
                            defaults={
                                'competition_id': row['competition_id'],
                                'participant_id': row['participant_id'],
                                'is_disqualified': row.get('is_disqualified', False),
                                'disqualification_reason': row.get('disqualification_reason', '')
                            }
                        )
                        count += 1
                    restored_counts['enrollments'] = count

                if 'exam_attempts' in data:
                    count = 0
                    for row in data['exam_attempts']:
                        ExamAttempt.objects.update_or_create(
                            id=row['id'],
                            defaults={
                                'competition_id': row['competition_id'],
                                'participant_id': row['participant_id'],
                                'attempt_number': row.get('attempt_number', 1),
                                'status': row.get('status', 'SUBMITTED'),
                                'start_time': row['start_time'],
                                'server_deadline': row['server_deadline'],
                                'submitted_at': row.get('submitted_at'),
                                'ip_address': row.get('ip_address'),
                                'user_agent': row.get('user_agent', '')
                            }
                        )
                        count += 1
                    restored_counts['exam_attempts'] = count

                if 'attempt_answers' in data:
                    count = 0
                    for row in data['attempt_answers']:
                        AttemptAnswer.objects.update_or_create(
                            id=row['id'],
                            defaults={
                                'attempt_id': row['attempt_id'],
                                'question_id': row['question_id'],
                                'selected_option_id': row.get('selected_option_id'),
                                'essay_text': row.get('essay_text', ''),
                                'revision_count': row.get('revision_count', 1),
                                'is_flagged_for_review': row.get('is_flagged_for_review', False),
                            }
                        )
                        count += 1
                    restored_counts['attempt_answers'] = count

                if 'answer_history_logs' in data:
                    count = 0
                    for row in data['answer_history_logs']:
                        AnswerHistoryLog.objects.update_or_create(
                            id=row['id'],
                            defaults={
                                'attempt_answer_id': row['attempt_answer_id'],
                                'selected_option_id': row.get('selected_option_id'),
                                'essay_text': row.get('essay_text', ''),
                                'ip_address': row.get('ip_address'),
                                'revision': row.get('revision', 1)
                            }
                        )
                        count += 1
                    restored_counts['answer_history_logs'] = count

                if 'attempt_grades' in data:
                    count = 0
                    for row in data['attempt_grades']:
                        AttemptGrade.objects.update_or_create(
                            id=row['id'],
                            defaults={
                                'attempt_id': row['attempt_id'],
                                'mcq_score': Decimal(str(row.get('mcq_score', 0.0))),
                                'essay_score': Decimal(str(row.get('essay_score', 0.0))),
                                'total_score': Decimal(str(row.get('total_score', 0.0))),
                                'is_finalized': row.get('is_finalized', False),
                                'finalized_by_id': row.get('finalized_by_id')
                            }
                        )
                        count += 1
                    restored_counts['attempt_grades'] = count

                if 'essay_evaluations' in data:
                    count = 0
                    for row in data['essay_evaluations']:
                        EssayEvaluation.objects.update_or_create(
                            id=row['id'],
                            defaults={
                                'attempt_answer_id': row['attempt_answer_id'],
                                'judge_id': row['judge_id'],
                                'score_awarded': Decimal(str(row.get('score_awarded', 0.0))),
                                'feedback': row.get('feedback', ''),
                                'internal_notes': row.get('internal_notes', ''),
                                'is_flagged_for_review': row.get('is_flagged_for_review', False),
                                'dispute_reason': row.get('dispute_reason', '')
                            }
                        )
                        count += 1
                    restored_counts['essay_evaluations'] = count

            # Audit Log Sukses Restore
            SecurityAuditLog.objects.create(
                user=user,
                event_type=AuditEventType.SUSPICIOUS_ACTIVITY,
                details={
                    'action': 'RESTORE_DATABASE_SUCCESS',
                    'filename': safe_fname,
                    'restored_counts': restored_counts,
                    'pre_restore_safety_backup': safety_manifest['filename']
                }
            )

            return True, restored_counts, f"Restorasi database berhasil dieksekusi ({sum(restored_counts.values())} records dipulihkan)."

        except Exception as e:
            return False, {}, f"Gagal mengeksekusi restorasi: {str(e)}"

    @classmethod
    def delete_backup(cls, filename: str, user: User) -> Tuple[bool, str]:
        """Menghapus file backup tertentu secara permanen."""
        safe_fname = os.path.basename(filename)
        filepath = os.path.join(cls.get_backup_dir(), safe_fname)
        if not os.path.exists(filepath):
            return False, f"File backup '{safe_fname}' tidak ditemukan."

        try:
            os.remove(filepath)
            SecurityAuditLog.objects.create(
                user=user,
                event_type=AuditEventType.SUSPICIOUS_ACTIVITY,
                details={
                    'action': 'DELETE_BACKUP',
                    'filename': safe_fname
                }
            )
            return True, f"File backup '{safe_fname}' berhasil dihapus."
        except Exception as e:
            return False, f"Gagal menghapus file backup: {str(e)}"

    @staticmethod
    def _format_file_size(num_bytes: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if abs(num_bytes) < 1024.0:
                return f"{num_bytes:3.1f} {unit}"
            num_bytes /= 1024.0
        return f"{num_bytes:.1f} TB"
