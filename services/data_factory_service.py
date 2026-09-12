"""
Cyber Data Factory & Seeder Layer — World's Top-Tier Secure Web Quiz Platform.
Menyediakan fungsionalitas pembuatan data dummy siber (CTF/Lomba Hacker) yang ultra-relevan,
serta reset transaksional dan reset penuh yang aman (zero-data-loss protection).
Khusus untuk Lead Developer / DevSecOps dan Automated Testing.
"""

import uuid
from decimal import Decimal
from datetime import timedelta
from typing import Dict, Any, List, Optional
from django.db import transaction
from django.utils import timezone

from accounts.models import User, UserRole
from competitions.models import Competition, CompetitionStatus, ParticipantEnrollment
from questions.models import Question, QuestionType, QuestionStatus, QuestionOption
from attempts.models import ExamAttempt, AttemptStatus, AttemptAnswer, AnswerHistoryLog
from grading.models import AttemptGrade, EssayEvaluation
from audit.models import SecurityAuditLog, AuditEventType
from services.scoring_service import ScoringService


class CyberDataFactoryService:
    """Service manajemen data dummy siber dan pembersihan (reset) aman."""

    @classmethod
    def reset_attempts_and_scores(cls, user: Optional[User] = None) -> Dict[str, int]:
        """
        Membersihkan seluruh sesi ujian, lembar jawaban, audit autosave, dan nilai.
        Kompetisi, bank soal, dan user akun tetap UTUH.
        Berguna untuk memulai turnamen baru dari kondisi bersih (Fresh Tournament).
        """
        with transaction.atomic():
            eval_count = EssayEvaluation.objects.all().delete()[0]
            grade_count = AttemptGrade.objects.all().delete()[0]
            hist_count = AnswerHistoryLog.objects.all().delete()[0]
            ans_count = AttemptAnswer.objects.all().delete()[0]
            att_count = ExamAttempt.objects.all().delete()[0]

            SecurityAuditLog.objects.create(
                user=user,
                event_type=AuditEventType.SUSPICIOUS_ACTIVITY,
                details={
                    'action': 'RESET_ATTEMPTS_AND_SCORES',
                    'deleted_attempts': att_count,
                    'deleted_answers': ans_count,
                    'deleted_grades': grade_count,
                    'deleted_evaluations': eval_count,
                    'timestamp': timezone.now().isoformat()
                }
            )

            return {
                'exam_attempts': att_count,
                'attempt_answers': ans_count,
                'answer_history_logs': hist_count,
                'attempt_grades': grade_count,
                'essay_evaluations': eval_count,
            }

    @classmethod
    def reset_all_competition_data(cls, user: Optional[User] = None, preserve_superusers: bool = True) -> Dict[str, int]:
        """
        Mereset seluruh data kompetisi, soal, dan akun peserta pengujian.
        Akun penting (DEVELOPER, SUPER_ADMIN) DIJAMIN TETAP AMAN dan TIDAK AKAN TERHAPUS!
        """
        with transaction.atomic():
            # 1. Bersihkan transaksi ujian
            txn_counts = cls.reset_attempts_and_scores(user=user)

            # 2. Bersihkan enrollments
            enroll_count = ParticipantEnrollment.objects.all().delete()[0]

            # 3. Bersihkan opsi dan soal
            opt_count = QuestionOption.objects.all().delete()[0]
            q_count = Question.objects.all().delete()[0]

            # 4. Bersihkan kompetisi
            comp_count = Competition.objects.all().delete()[0]

            # 5. Bersihkan akun peserta saja (pertahankan developer & admin)
            users_qs = User.objects.filter(role=UserRole.PARTICIPANT)
            if preserve_superusers:
                users_qs = users_qs.filter(is_superuser=False, is_staff=False)
            user_count = users_qs.delete()[0]

            SecurityAuditLog.objects.create(
                user=user,
                event_type=AuditEventType.SUSPICIOUS_ACTIVITY,
                details={
                    'action': 'RESET_ALL_COMPETITION_DATA',
                    'deleted_competitions': comp_count,
                    'deleted_questions': q_count,
                    'deleted_options': opt_count,
                    'deleted_enrollments': enroll_count,
                    'deleted_participants': user_count,
                    'timestamp': timezone.now().isoformat()
                }
            )

            result = {
                **txn_counts,
                'enrollments': enroll_count,
                'questions': q_count,
                'question_options': opt_count,
                'competitions': comp_count,
                'participants': user_count,
            }
            return result

    @classmethod
    def seed_realistic_cyber_data(cls, operator: Optional[User] = None) -> Dict[str, Any]:
        """
        Menyuntikkan (seed) dataset kompetisi siber / CTF lengkap berstandar dunia.
        Mencakup User, Kompetisi, Bank Soal (MCQ & Essay dengan rubrik), Sesi Live,
        Jawaban, Evaluasi Juri Multi-Judge, dan Audit Trail.
        """
        with transaction.atomic():
            now = timezone.now()

            # -------------------------------------------------------------
            # 1. CORE ACCOUNTS & JUDGES
            # -------------------------------------------------------------
            # Developer
            dev_user, _ = User.objects.get_or_create(
                username='developer',
                defaults={
                    'email': 'dev@cybercomp.id',
                    'first_name': 'Lead',
                    'last_name': 'DevSecOps',
                    'role': UserRole.DEVELOPER,
                    'institution': 'Core Infrastructure Team',
                    'is_staff': True,
                    'is_superuser': True,
                }
            )
            dev_user.role = UserRole.DEVELOPER
            dev_user.is_staff = True
            dev_user.is_superuser = True
            dev_user.save()

            # Super Admin
            admin_user, _ = User.objects.get_or_create(
                username='admin',
                defaults={
                    'email': 'admin@cybercomp.id',
                    'first_name': 'Chief',
                    'last_name': 'Organizer',
                    'role': UserRole.SUPER_ADMIN,
                    'institution': 'National Cyber Competition Board',
                    'is_staff': True,
                    'is_superuser': True,
                }
            )
            admin_user.set_password('Adm!nCyber#2026')
            admin_user.role = UserRole.SUPER_ADMIN
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.save()

            # Judges
            juri1, _ = User.objects.get_or_create(
                username='juri_siber',
                defaults={
                    'email': 'juri1@cybercomp.id',
                    'first_name': 'Ahmad',
                    'last_name': 'Fauzi, M.Kom',
                    'role': UserRole.JUDGE,
                    'institution': 'Badan Siber dan Sandi Negara (BSSN)',
                    'is_staff': True,
                }
            )
            juri1.set_password('Jur!S1ber#2026')
            juri1.role = UserRole.JUDGE
            juri1.is_staff = True
            juri1.save()

            juri2, _ = User.objects.get_or_create(
                username='dr_sec_lead',
                defaults={
                    'email': 'lead_forensics@cybercomp.id',
                    'first_name': 'Dr. Rian',
                    'last_name': 'Kurniawan, CISSP',
                    'role': UserRole.JUDGE,
                    'institution': 'Indonesia CERT & Cyber Forensics Lab',
                    'is_staff': True,
                }
            )
            juri2.set_password('DrSec#Lead2026!')
            juri2.role = UserRole.JUDGE
            juri2.is_staff = True
            juri2.save()

            # -------------------------------------------------------------
            # 2. DIVERSE HACKER PARTICIPANTS
            # -------------------------------------------------------------
            participants_data = [
                ('pwn_master', 'Defensive Blue Team - Univ. Indonesia', '10.10.14.33', 'PwnM@ster2026!'),
                ('byte_ninja', 'Red Team Research Lab - ITB Bandung', '10.10.14.45', 'ByteN!nja2026#'),
                ('cipher_queen', 'Applied Cryptography Club - UGM', '10.10.14.68', 'C!pherQue3n2026'),
                ('null_pointer', 'Digital Forensics Lab - Telkom Univ.', '10.10.14.52', 'NullP0inter2026!'),
                ('zero_day_hunter', 'Binus Cyber Security Community', '10.10.14.77', 'Z3roDay#Hunt2026'),
                ('packet_sniffer', 'Independen Bug Hunter', '10.10.14.89', 'Pack3tSn!ff2026'),
                ('kernel_panic', 'Politeknik Siber dan Sandi Negara (PSSN)', '10.10.14.99', 'K3rnelPanic2026!'),
                ('hacker_one', 'Cyber Defense Academy', '10.10.14.101', 'H@ck3rOne2026!'),
            ]

            participants: Dict[str, User] = {}
            for uname, inst, ip, pwd in participants_data:
                p, _ = User.objects.get_or_create(
                    username=uname,
                    defaults={
                        'email': f"{uname}@cyber.test",
                        'role': UserRole.PARTICIPANT,
                        'institution': inst,
                        'last_login_ip': ip,
                        'is_active': True,
                    }
                )
                p.set_password(pwd)
                p.institution = inst
                p.last_login_ip = ip
                p.save()
                participants[uname] = p

            # -------------------------------------------------------------
            # 3. COMPETITIONS (OPEN, CLOSED, UPCOMING)
            # -------------------------------------------------------------
            comp_open, _ = Competition.objects.get_or_create(
                slug='penyisihan-siber-nasional-2026',
                defaults={
                    'title': 'Penyisihan Nasional: National Cyber Warfare & Defense 2026',
                    'description': (
                        'Babak resmi penyisihan kompetisi keamanan siber tingkat nasional. '
                        'Menguji keahlian exploit analysis, secure code review, network forensics, '
                        'dan mitigasi insiden siber pada infrastruktur kritikal.'
                    ),
                    'status': CompetitionStatus.OPEN,
                    'start_time': now - timedelta(hours=1),
                    'end_time': now + timedelta(days=2),
                    'duration_minutes': 120,
                    'max_attempts': 1,
                    'created_by': admin_user,
                }
            )
            comp_open.status = CompetitionStatus.OPEN
            comp_open.save()

            comp_closed, _ = Competition.objects.get_or_create(
                slug='babak-kualifikasi-ctf',
                defaults={
                    'title': 'Babak Kualifikasi: CTF & Basic Web Exploitation',
                    'description': 'Penyisihan awal mencakup fundamental SQL injection, XSS, dan network packet analysis.',
                    'status': CompetitionStatus.CLOSED,
                    'start_time': now - timedelta(days=7),
                    'end_time': now - timedelta(days=6),
                    'duration_minutes': 90,
                    'max_attempts': 1,
                    'created_by': admin_user,
                }
            )

            comp_upcoming, _ = Competition.objects.get_or_create(
                slug='babak-final-live-defense',
                defaults={
                    'title': 'Babak Final: Red vs Blue Live Attack & Defense',
                    'description': 'Babak puncak perlombaan hacker waktu nyata, mitigasi active zero-day, dan kernel hardening.',
                    'status': CompetitionStatus.PUBLISHED,
                    'start_time': now + timedelta(days=3),
                    'end_time': now + timedelta(days=3, hours=5),
                    'duration_minutes': 300,
                    'max_attempts': 1,
                    'created_by': admin_user,
                }
            )

            # -------------------------------------------------------------
            # 4. ENROLL PARTICIPANTS
            # -------------------------------------------------------------
            for p in participants.values():
                ParticipantEnrollment.objects.get_or_create(competition=comp_open, participant=p)
                ParticipantEnrollment.objects.get_or_create(competition=comp_closed, participant=p)
                ParticipantEnrollment.objects.get_or_create(competition=comp_upcoming, participant=p)

            # -------------------------------------------------------------
            # 5. REALISTIC CYBER QUESTION BANK (MCQ & ESSAY)
            # -------------------------------------------------------------
            mcq_data = [
                (
                    "Teknik Ekstraksi Blind SQL Injection Berbasis Waktu (Time-Based)",
                    "Pada pengujian penetrasi aplikasi web yang memfilter error message database, penyerang mengirim payload: "
                    "`' UNION SELECT IF(ASCII(SUBSTRING((SELECT database()),1,1))=115, SLEEP(5), 0)-- -`. "
                    "Apa fungsi utama dari fungsi SLEEP(5) dalam skenario tersebut?",
                    Decimal('5.00'),
                    [
                        ("Mengukur latensi respon HTTP server untuk menyimpulkan kebenaran karakter yang ditebak secara inferensial.", True),
                        ("Menghindari deteksi signature-based firewall WAF dengan memperlambat request.", False),
                        ("Memaksa database engine MySQL melakukan flush cache disk secara berkala.", False),
                        ("Mendapatkan dump seluruh tabel secara instan tanpa autentikasi admin.", False),
                    ]
                ),
                (
                    "Eksploitasi SSRF pada Lingkungan AWS Cloud (IMDSv1 vs IMDSv2)",
                    "Penyerang menemukan kerentanan Server-Side Request Forgery (SSRF) pada microservice backend AWS. "
                    "Perlindungan paling efektif untuk memitigasi pencurian kredensial IAM Role dari 169.254.169.254 adalah:",
                    Decimal('5.00'),
                    [
                        ("Mewajibkan Instance Metadata Service Version 2 (IMDSv2) dengan token HTTP PUT dan menyetel hop-limit = 1.", True),
                        ("Mengganti port default metadata service 80 menjadi port privat 8080.", False),
                        ("Melakukan base64 encoding pada setiap URL sebelum dikirimkan oleh backend.", False),
                        ("Menggunakan IAM User access key statis di dalam file konfigurasi aplikasi.", False),
                    ]
                ),
                (
                    "Bypass Format String Vulnerability pada Linux x86-64",
                    "Ketika fungsi `printf(user_input)` dipanggil tanpa format specifier, specifier manakah yang dapat "
                    "digunakan penyerang untuk menuliskan nilai integer arbitrer ke alamat memori tertentu?",
                    Decimal('5.00'),
                    [
                        ("%n atau %hn / %hhn", True),
                        ("%s dan %ls", False),
                        ("%p dan %lx", False),
                        ("%d dan %ld", False),
                    ]
                ),
                (
                    "Kelemahan Implementasi JWT (JSON Web Token) None Algorithm",
                    "Dalam audit keamanan API RESTful, token JWT ditemukan memiliki header `{\"alg\": \"none\", \"typ\": \"JWT\"}`. "
                    "Apa implikasi keamanan paling kritis dari konfigurasi tersebut jika diverifikasi secara ceroboh oleh backend?",
                    Decimal('5.00'),
                    [
                        ("Penyerang dapat memalsukan payload identitas (misal role admin) tanpa memerlukan signature kriptografis.", True),
                        ("Waktu expired token (exp) menjadi permanen dan tidak akan pernah kadaluarsa.", False),
                        ("Kunci privat RSA server akan bocor ke dalam response HTTP header.", False),
                        ("Database MySQL rentan terhadap serangan Cross-Site Request Forgery (CSRF).", False),
                    ]
                ),
                (
                    "Padding Oracle Attack pada Mode Operasi AES-CBC",
                    "Padding Oracle Attack mengeksploitasi respon error server yang membedakan kegagalan padding PKCS#7 "
                    "dengan kegagalan integritas MAC. Mekanisme mitigasi utama untuk mencegah serangan ini adalah:",
                    Decimal('5.00'),
                    [
                        ("Menerapkan Authenticated Encryption (AEAD) seperti AES-GCM atau skema Encrypt-then-MAC (HMAC-SHA256).", True),
                        ("Menggunakan kunci simetris 512-bit sebagai pengganti AES 256-bit.", False),
                        ("Mengacak urutan blok ciphertext sebelum dikirimkan ke client.", False),
                        ("Menghapus padding PKCS#7 dan menggantinya dengan zero padding statis.", False),
                    ]
                ),
                (
                    "Analisis Memori Forensik Menggunakan Framework Volatility 3",
                    "Plugin Volatility 3 manakah yang digunakan penyelidik digital forensik untuk mendeteksi injeksi kode "
                    "tersembunyi dalam memori proses (seperti DLL unlinked atau VirtualAlloc RWX memory regions)?",
                    Decimal('5.00'),
                    [
                        ("windows.malfind", True),
                        ("windows.pslist", False),
                        ("windows.handles", False),
                        ("windows.netstat", False),
                    ]
                ),
                (
                    "Privilege Escalation via Container Socket Escape",
                    "Jika container Docker dijalankan dengan mounting volume `-v /var/run/docker.sock:/var/run/docker.sock`, "
                    "vektor apa yang memungkinkan penyerang memperoleh root shell pada Host OS?",
                    Decimal('5.00'),
                    [
                        ("Membuat container baru dengan flag `--privileged` dan mounting root filesystem host `/`.", True),
                        ("Menjalankan binary setuid /bin/ping di dalam container.", False),
                        ("Melakukan brute-force password user docker di dalam /etc/shadow.", False),
                        ("Mengirimkan paket ICMP flood ke interface docker0.", False),
                    ]
                ),
                (
                    "Mitigasi Kerentanan Prototype Pollution pada Node.js",
                    "Metode manakah yang paling direkomendasikan untuk mencegah eksploitasi Object Prototype Pollution "
                    "pada parsing payload JSON yang tidak dipercaya?",
                    Decimal('5.00'),
                    [
                        ("Menggunakan `Object.create(null)` atau `Map` serta membekukan Object.prototype via `Object.freeze()`.", True),
                        ("Mengonversi semua string input menjadi integer sebelum digabungkan.", False),
                        ("Menjalankan Node.js dengan flag `--expose-gc`.", False),
                        ("Mengganti runtime JavaScript dengan WebAssembly engine.", False),
                    ]
                ),
                (
                    "Mekanisme Proteksi Stack Canary pada Kompiler GCC",
                    "Bagaimana cara kerja Stack Smashing Protector (Canary) pada fungsi bahasa C di Linux ELF x86-64?",
                    Decimal('5.00'),
                    [
                        ("Menyisipkan nilai acak (fs:0x28) di antara local buffer dan saved base pointer / return address.", True),
                        ("Mengenkripsi seluruh stack frame menggunakan AES hardware instruction.", False),
                        ("Memindahkan alamat memori stack ke segmen kernel secara dinamis.", False),
                        ("Menghapus return address dan menggantinya dengan instruksi jump langsung.", False),
                    ]
                ),
                (
                    "Kriptoanalisis Nonce Reuse pada Skema Tanda Tangan Digital ECDSA",
                    "Apa konsekuensi matematis fatal jika sebuah kunci privat ECC menandatangani dua pesan berbeda "
                    "menggunakan nilai ephemeral key (nonce) `k` yang sama?",
                    Decimal('5.00'),
                    [
                        ("Kunci privat penandatangan dapat dihitung dan dipulihkan secara instan melalui penyelesaian aljabar sederhana.", True),
                        ("Kedua pesan akan menghasilkan nilai hash SHA-256 yang identik (collision).", False),
                        ("Public key penandatangan akan terhapus dari certificate revocation list.", False),
                        ("Tanda tangan digital akan ditolak oleh algoritma verification deterministik RFC 6979.", False),
                    ]
                ),
            ]

            created_questions: List[Question] = []
            seq = 1

            for title, body, pts, options in mcq_data:
                q, _ = Question.objects.get_or_create(
                    competition=comp_open,
                    sequence=seq,
                    defaults={
                        'type': QuestionType.MCQ,
                        'title': f"Soal #{seq}: {title}",
                        'body': body,
                        'points': pts,
                        'status': QuestionStatus.APPROVED,
                        'created_by': admin_user,
                    }
                )
                q.title = f"Soal #{seq}: {title}"
                q.body = body
                q.points = pts
                q.status = QuestionStatus.APPROVED
                q.save()
                created_questions.append(q)

                # Update opsi
                q.options.all().delete()
                for opt_idx, (opt_txt, is_corr) in enumerate(options, 1):
                    QuestionOption.objects.create(
                        question=q,
                        option_text=opt_txt,
                        is_correct=is_corr,
                        order=opt_idx
                    )
                seq += 1

            # -------------------------------------------------------------
            # ESSAY CHALLENGES (DENGAN RUBRIK & MITIGASI MENDALAM)
            # -------------------------------------------------------------
            essay_data = [
                (
                    "Forensik Insiden: Investigasi Nginx Access Log & Webshell Bypass",
                    (
                        "Ditemukan anomali pada access log server web produksi Nginx:\n"
                        "```\n"
                        "185.220.101.5 - - [12/Sep/2026:03:14:22 +0700] \"POST /api/v1/profile/upload-avatar HTTP/1.1\" 200 458 \"-\" \"curl/7.68.0\"\n"
                        "185.220.101.5 - - [12/Sep/2026:03:14:55 +0700] \"GET /uploads/avatars/cache_404.php?cmd=cat+/etc/passwd HTTP/1.1\" 200 2489 \"-\" \"Mozilla/5.0\"\n"
                        "```\n"
                        "Tugas Analisis:\n"
                        "1. Identifikasi root cause eksploitasi dan mekanisme bypass Magic Bytes.\n"
                        "2. Jelaskan bahaya webshell tersebut dan perintah yang dieksekusi.\n"
                        "3. Tuliskan rekomendasi hardening arsitektur server secara komprehensif."
                    ),
                    Decimal('15.00'),
                    (
                        "1. Identifikasi Root Cause & Endpoint (4.0 Poin): Menyebutkan IP penyerang 185.220.101.5 dan upload avatar tanpa validasi ekstensi.\n"
                        "2. Deteksi Bypass Magic Bytes (4.0 Poin): Membongkar header palsu GIF89a dan eksekusi payload PHP eval($_POST['cmd']).\n"
                        "3. Rekomendasi Hardening Efektif (7.0 Poin): Matikan PHP engine di direktori upload Nginx, simpan di bucket S3 terisolasi tanpa eksekusi."
                    )
                ),
                (
                    "Linux Advanced Persistence: Analisis Injeksi /etc/ld.so.preload",
                    (
                        "Pada investigasi server Linux, proses kueri CPU mencapai 100%, namun perintah `ps aux`, `top`, dan `htop` "
                        "tidak menampilkan proses yang mencurigakan. Ditemukan berkas `/etc/ld.so.preload` berisi entri `/lib/libprocesshide.so`.\n"
                        "Tugas Analisis:\n"
                        "1. Jelaskan mekanisme kerja Userland Rootkit via dynamic linker preload.\n"
                        "2. Syscall libc mana yang di-hook untuk menyembunyikan PID proses dan port C2?\n"
                        "3. Rincikan langkah remediasi, verifikasi integritas paket, dan audit rule auditd."
                    ),
                    Decimal('15.00'),
                    (
                        "1. Mekanisme Hooking (4.0 Poin): Menjelaskan injeksi /etc/ld.so.preload dan overriding library libc sebelum biner dijalankan.\n"
                        "2. Deteksi Syscall Hooking (4.0 Poin): Mengidentifikasi hook readdir() dan getdents64() untuk memfilter direktori /proc/.\n"
                        "3. Hardening & Auditd (7.0 Poin): Menghapus entri, menyetel chattr +i, debsums -c, dan rule auditd pemantauan /etc/ld.so.preload."
                    )
                ),
                (
                    "Cloud Security Architecture: Blind SSRF pada AWS Kubernetes (IMDSv2)",
                    (
                        "Sebuah microservice PDF Converter menerima parameter `url=http://169.254.169.254/latest/meta-data/`. "
                        "Jelaskan arsitektur mitigasi Zero Trust untuk melindungi Instance Metadata Service pada cluster EKS "
                        "menggunakan kombinasi IMDSv2, hop-limit network, dan Kubernetes NetworkPolicy."
                    ),
                    Decimal('15.00'),
                    (
                        "1. Vektor Penetrasi (4.0 Poin): Mengidentifikasi Blind SSRF pada webhook service menuju link-local address 169.254.169.254.\n"
                        "2. Ekstraksi Metadata Kritis (4.0 Poin): Menjelaskan pencurian AWS IAM STS token sementara.\n"
                        "3. Mitigasi Zero Trust (7.0 Poin): Mewajibkan IMDSv2 token session, hop-limit=1, dan NetworkPolicy egress deny ke 169.254.169.254."
                    )
                ),
            ]

            essay_questions: List[Question] = []
            for title, body, pts, rubric in essay_data:
                q, _ = Question.objects.get_or_create(
                    competition=comp_open,
                    sequence=seq,
                    defaults={
                        'type': QuestionType.ESSAY,
                        'title': f"Tantangan Essay #{seq}: {title}",
                        'body': body,
                        'points': pts,
                        'rubric_guidelines': rubric,
                        'status': QuestionStatus.APPROVED,
                        'created_by': admin_user,
                    }
                )
                q.title = f"Tantangan Essay #{seq}: {title}"
                q.body = body
                q.points = pts
                q.rubric_guidelines = rubric
                q.status = QuestionStatus.APPROVED
                q.save()
                essay_questions.append(q)
                created_questions.append(q)
                seq += 1

            # -------------------------------------------------------------
            # 6. EXAM ATTEMPTS (DIVERSE STATES)
            # -------------------------------------------------------------
            # A. LIVE IN_PROGRESS: pwn_master (Live countdown ~95 menit)
            p_pwn = participants['pwn_master']
            att_pwn, _ = ExamAttempt.objects.get_or_create(
                participant=p_pwn,
                competition=comp_open,
                attempt_number=1,
                defaults={
                    'status': AttemptStatus.IN_PROGRESS,
                    'start_time': now - timedelta(minutes=25),
                    'server_deadline': now + timedelta(minutes=95),
                    'ip_address': p_pwn.last_login_ip,
                }
            )
            att_pwn.status = AttemptStatus.IN_PROGRESS
            att_pwn.start_time = now - timedelta(minutes=25)
            att_pwn.server_deadline = now + timedelta(minutes=95)
            att_pwn.save()

            for q_mcq in created_questions[:7]:
                if q_mcq.type == QuestionType.MCQ:
                    corr = q_mcq.options.filter(is_correct=True).first()
                    if corr:
                        ans, _ = AttemptAnswer.objects.get_or_create(attempt=att_pwn, question=q_mcq)
                        ans.selected_option = corr
                        ans.save()

            # B. LIVE IN_PROGRESS: byte_ninja (Live countdown ~110 menit)
            p_ninja = participants['byte_ninja']
            att_ninja, _ = ExamAttempt.objects.get_or_create(
                participant=p_ninja,
                competition=comp_open,
                attempt_number=1,
                defaults={
                    'status': AttemptStatus.IN_PROGRESS,
                    'start_time': now - timedelta(minutes=10),
                    'server_deadline': now + timedelta(minutes=110),
                    'ip_address': p_ninja.last_login_ip,
                }
            )
            att_ninja.status = AttemptStatus.IN_PROGRESS
            att_ninja.save()

            for q_mcq in created_questions[:4]:
                if q_mcq.type == QuestionType.MCQ:
                    opt = q_mcq.options.first()
                    ans, _ = AttemptAnswer.objects.get_or_create(attempt=att_ninja, question=q_mcq)
                    ans.selected_option = opt
                    ans.save()

            # C. SUBMITTED: null_pointer (Lengkap Essay + Discrepancy Alert Juri + Dispute Eskalasi)
            p_null = participants['null_pointer']
            att_null, _ = ExamAttempt.objects.get_or_create(
                participant=p_null,
                competition=comp_open,
                attempt_number=1,
                defaults={
                    'status': AttemptStatus.SUBMITTED,
                    'start_time': now - timedelta(minutes=115),
                    'server_deadline': now - timedelta(minutes=5),
                    'submitted_at': now - timedelta(minutes=10),
                    'ip_address': p_null.last_login_ip,
                }
            )
            att_null.status = AttemptStatus.SUBMITTED
            att_null.submitted_at = now - timedelta(minutes=10)
            att_null.save()

            # MCQ null_pointer
            for q_mcq in created_questions:
                if q_mcq.type == QuestionType.MCQ:
                    corr = q_mcq.options.filter(is_correct=True).first()
                    ans, _ = AttemptAnswer.objects.get_or_create(attempt=att_null, question=q_mcq)
                    ans.selected_option = corr
                    ans.save()

            # Essay null_pointer
            if len(essay_questions) >= 3:
                # Essay 1: Discrepancy Alert (9.5 vs 5.0)
                ans_e1, _ = AttemptAnswer.objects.get_or_create(attempt=att_null, question=essay_questions[0])
                ans_e1.essay_text = (
                    "Berdasarkan analisis baris access log Nginx:\n"
                    "1. IP Penyerang 185.220.101.5 mengeksploitasi endpoint /api/v1/profile/upload-avatar tanpa validasi MIME-type.\n"
                    "2. Magic bytes file dipalsukan dengan signature GIF89a namun berisi kode eksekusi PHP eval($_POST['cmd']).\n"
                    "3. File tersimpan sebagai /uploads/avatars/cache_404.php dan dieksekusi dengan parameter 'cat /etc/passwd'.\n"
                    "Rekomendasi Penanganan:\n"
                    "- Nonaktifkan eksekusi PHP pada direktori upload menggunakan konfigurasi Nginx: location ^~ /uploads/ { php_flag engine off; }\n"
                    "- Validasi MIME type berbasis libmagic mendalam dan simpan file di storage terisolasi S3."
                )
                ans_e1.revision_count = 3
                ans_e1.save()

                EssayEvaluation.objects.update_or_create(
                    attempt_answer=ans_e1,
                    judge=juri1,
                    defaults={
                        'score_awarded': Decimal('9.50'),
                        'feedback': 'Analisis log sangat presisi dan sistematis. Mitigasi Nginx sangat akurat.',
                        'internal_notes': 'Kandidat memahami bypass magic bytes secara mendalam.'
                    }
                )
                EssayEvaluation.objects.update_or_create(
                    attempt_answer=ans_e1,
                    judge=juri2,
                    defaults={
                        'score_awarded': Decimal('5.00'),
                        'feedback': 'Langkah mitigasi belum menyertakan WAF rule CRS ModSecurity.',
                        'internal_notes': 'Perlu klarifikasi standar WAF pada deliberasi juri.'
                    }
                )

                # Essay 2: Menunggu Penilaian Juri (Unjudged)
                ans_e2, _ = AttemptAnswer.objects.get_or_create(attempt=att_null, question=essay_questions[1])
                ans_e2.essay_text = (
                    "Analisis Host Linux Rootkit:\n"
                    "1. Injeksi dilakukan via dynamic linker preload /etc/ld.so.preload memuat libprocesshide.so.\n"
                    "2. Hooking pada libc readdir() menyembunyikan PID penyerang dari utility ps dan top.\n"
                    "3. Remediasi: Hapus entri, kunci dengan chattr +i, dan pasang audit rule auditd."
                )
                ans_e2.revision_count = 2
                ans_e2.save()

                # Essay 3: Eskalasi / Dispute (Flagged for Review)
                ans_e3, _ = AttemptAnswer.objects.get_or_create(attempt=att_null, question=essay_questions[2])
                ans_e3.essay_text = (
                    "Arsitektur Remediasi SSRF:\n"
                    "1. Mengharuskan IMDSv2 token session dengan HTTP PUT.\n"
                    "2. Menyetel hop-limit = 1 agar container overlay network tidak dapat menjangkau 169.254.169.254.\n"
                    "3. NetworkPolicy default deny egress ke subnet link-local."
                )
                ans_e3.save()

                EssayEvaluation.objects.update_or_create(
                    attempt_answer=ans_e3,
                    judge=juri1,
                    defaults={
                        'score_awarded': Decimal('12.00'),
                        'feedback': 'Solusi arsitektur enterprise Zero Trust.',
                        'internal_notes': 'Eskalasi: Verifikasi apakah hop-limit=1 memblokir container CNI pod.',
                        'is_flagged_for_review': True,
                        'dispute_reason': 'Verifikasi keefektifan hop-limit=1 pada EKS CNI'
                    }
                )

            ScoringService.evaluate_and_score_attempt(att_null.id)

            # D. SUBMITTED & FINALIZED: zero_day_hunter (Leaderboard Rank #1, Skor 98.0)
            p_hunter = participants['zero_day_hunter']
            att_hunter, _ = ExamAttempt.objects.get_or_create(
                participant=p_hunter,
                competition=comp_open,
                attempt_number=1,
                defaults={
                    'status': AttemptStatus.SUBMITTED,
                    'start_time': now - timedelta(minutes=130),
                    'server_deadline': now - timedelta(minutes=10),
                    'submitted_at': now - timedelta(minutes=15),
                    'ip_address': p_hunter.last_login_ip,
                }
            )
            att_hunter.status = AttemptStatus.SUBMITTED
            att_hunter.submitted_at = now - timedelta(minutes=15)
            att_hunter.save()

            for q_mcq in created_questions:
                if q_mcq.type == QuestionType.MCQ:
                    corr = q_mcq.options.filter(is_correct=True).first()
                    ans, _ = AttemptAnswer.objects.get_or_create(attempt=att_hunter, question=q_mcq)
                    ans.selected_option = corr
                    ans.save()

            if len(essay_questions) >= 3:
                for q_ess in essay_questions:
                    ans, _ = AttemptAnswer.objects.get_or_create(attempt=att_hunter, question=q_ess)
                    ans.essay_text = f"Analisis Teknis Komprehensif oleh Zero Day Hunter: Solusi arsitektur dan exploit POC lengkap untuk {q_ess.title}."
                    ans.save()
                    EssayEvaluation.objects.update_or_create(
                        attempt_answer=ans,
                        judge=juri2,
                        defaults={
                            'score_awarded': Decimal(str(q_ess.points)) - Decimal('0.50'),
                            'feedback': 'Jawaban sempurna, penjelasan mitigasi kelas enterprise.',
                        }
                    )

            ScoringService.evaluate_and_score_attempt(att_hunter.id)
            grade_h = getattr(att_hunter, 'grade', None)
            if grade_h:
                grade_h.is_finalized = True
                grade_h.finalized_by = admin_user
                grade_h.save(update_fields=['is_finalized', 'finalized_by'])

            # E. SUBMITTED: hacker_one (Rank #2, Skor 84.0)
            p_h1 = participants['hacker_one']
            att_h1, _ = ExamAttempt.objects.get_or_create(
                participant=p_h1,
                competition=comp_open,
                attempt_number=1,
                defaults={
                    'status': AttemptStatus.SUBMITTED,
                    'start_time': now - timedelta(minutes=140),
                    'server_deadline': now - timedelta(minutes=20),
                    'submitted_at': now - timedelta(minutes=25),
                    'ip_address': p_h1.last_login_ip,
                }
            )
            att_h1.status = AttemptStatus.SUBMITTED
            att_h1.submitted_at = now - timedelta(minutes=25)
            att_h1.save()

            for idx, q_mcq in enumerate(created_questions):
                if q_mcq.type == QuestionType.MCQ:
                    corr = q_mcq.options.filter(is_correct=True).first() if idx % 3 != 0 else q_mcq.options.filter(is_correct=False).first()
                    ans, _ = AttemptAnswer.objects.get_or_create(attempt=att_h1, question=q_mcq)
                    ans.selected_option = corr or q_mcq.options.first()
                    ans.save()

            ScoringService.evaluate_and_score_attempt(att_h1.id)

            # F. AUTO_SUBMITTED: kernel_panic (Simulasi waktu server habis)
            p_panic = participants['kernel_panic']
            att_panic, _ = ExamAttempt.objects.get_or_create(
                participant=p_panic,
                competition=comp_open,
                attempt_number=1,
                defaults={
                    'status': AttemptStatus.AUTO_SUBMITTED,
                    'start_time': now - timedelta(minutes=150),
                    'server_deadline': now - timedelta(minutes=30),
                    'submitted_at': now - timedelta(minutes=30),
                    'ip_address': p_panic.last_login_ip,
                }
            )
            att_panic.status = AttemptStatus.AUTO_SUBMITTED
            att_panic.submitted_at = now - timedelta(minutes=30)
            att_panic.save()

            # -------------------------------------------------------------
            # 7. SECURITY AUDIT LOGS
            # -------------------------------------------------------------
            audit_events = [
                (AuditEventType.LOGIN, p_pwn, '10.10.14.33', '/accounts/login/', {'msg': 'Autentikasi peserta pwn_master berhasil'}),
                (AuditEventType.START_EXAM, p_pwn, '10.10.14.33', f'/attempts/{att_pwn.id}/start/', {'msg': 'Sesi ujian dimulai secara sah'}),
                (AuditEventType.AUTOSAVE_ANSWER, p_pwn, '10.10.14.33', '/api/attempts/answers/save/', {'msg': 'Jawaban Soal #1 (MCQ) tersimpan aman di server'}),
                (AuditEventType.FINAL_SUBMIT, p_null, '10.10.14.52', f'/attempts/{att_null.id}/submit/', {'msg': 'Sesi ujian null_pointer disubmit final'}),
                (AuditEventType.GRADE_ESSAY, juri1, '192.168.1.50', '/manage/grading/', {'msg': 'Juri menilai essay Soal #11: 9.5 Poin'}),
                (AuditEventType.SUSPICIOUS_ACTIVITY, p_pwn, '10.10.14.33', '/api/attempts/answers/save/', {'msg': 'Deteksi 5 request autosave dalam 200ms (Rate Limiter Actived)'}),
            ]

            for ev, u, ip, pth, det in audit_events:
                SecurityAuditLog.objects.create(
                    event_type=ev,
                    user=u,
                    ip_address=ip,
                    path=pth,
                    details=det,
                )

            summary = {
                'users_count': User.objects.count(),
                'competitions_count': Competition.objects.count(),
                'questions_count': Question.objects.count(),
                'attempts_count': ExamAttempt.objects.count(),
                'live_in_progress': ExamAttempt.objects.filter(status=AttemptStatus.IN_PROGRESS).count(),
                'submitted': ExamAttempt.objects.filter(status=AttemptStatus.SUBMITTED).count(),
                'auto_submitted': ExamAttempt.objects.filter(status=AttemptStatus.AUTO_SUBMITTED).count(),
                'grades_count': AttemptGrade.objects.count(),
                'essay_evaluations_count': EssayEvaluation.objects.count(),
                'audit_logs_count': SecurityAuditLog.objects.count(),
            }

            return summary
