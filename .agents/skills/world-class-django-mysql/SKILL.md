---
name: world-class-django-mysql
description: Elite architectural, security, and performance engineering standards for building high-concurrency, ultra-secure web applications using Django and MySQL / MariaDB.
---

# World-Class Django & MySQL Engineering Standards

Standard operasional dan panduan arsitektur rekayasa perangkat lunak kelas dunia (World's #1 Engineer Standards) untuk membangun aplikasi web berskala enterprise yang tangguh, berperforma tinggi, dan memiliki standar keamanan siber tertinggi menggunakan **Django** dan **MySQL (MariaDB)**.

---

## 1. Core Engineering Philosophy
1. **Zero-Trust Architecture**: Asumsikan semua input dari client, browser, atau API pihak ketiga bersifat berbahaya (*malicious*). Jangan pernah memvalidasi status sensitif di sisi client (frontend).
2. **Defense in Depth**: Menerapkan pertahanan berlapis (WAF / Middleware -> Application Logic / Service Layer -> ORM / Model Constraints -> Database Constraints & Triggers).
3. **Clean Architecture & Separation of Concerns**:
   - **Models**: Hanya mendefinisikan skema, relasi, validasi integritas data dasar, dan custom QuerySets.
   - **Services (`services/`)**: Menampung business logic utama, orchestrator transaksi atomik, dan kalkulasi skor.
   - **Selectors (`selectors/`)**: Query data kompleks terisolasi untuk menghindari query leak di views.
   - **Views / API Endpoints**: Hanya menangani parsing request, otorisasi, pemanggilan service, dan serialisasi response.
4. **Resilience & Performance**: Desain database ramah konkurensi tinggi, cegah race condition dengan database row locking (`select_for_update()`), dan optimalkan query dengan indexing serta `select_related`/`prefetch_related`.

---

## 2. Django & MySQL (MariaDB) Setup & Hardening

### A. PyMySQL & MySQL Integration
Di Windows/XAMPP, `PyMySQL` digunakan bersama `cryptography`:
```python
# Di __init__.py dari project root atau settings.py
import pymysql
pymysql.install_as_MySQLdb()
```

### B. Database Configuration Standards
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME', 'secure_quiz_db'),
        'USER': os.environ.get('DB_USER', 'root'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', '127.0.0.1'),
        'PORT': os.environ.get('DB_PORT', '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': (
                "SET sql_mode='STRICT_TRANS_TABLES,NO_ENGINE_SUBSTITUTION,STRICT_ALL_TABLES';"
                "SET default_storage_engine=INNODB;"
            ),
            'connect_timeout': 10,
        },
        'CONN_MAX_AGE': 60,  # Connection reuse for performance
    }
}
```

### C. Concurrency & Race Condition Prevention
Untuk pengerjaan kuis, autosave jawaban, dan scoring serentak:
```python
from django.db import transaction

# Selalu gunakan atomic block dan row-level lock saat memodifikasi data ujian
with transaction.atomic():
    exam_session = ExamSession.objects.select_for_update().get(id=session_id, user=user)
    if exam_session.is_expired():
        raise ExamExpiredException("Waktu ujian telah berakhir.")
    # update jawaban
    exam_session.record_answer(question_id, payload)
```

---

## 3. Top-Tier Security Implementation Checklist

### A. OWASP Top 10 Hardening
- **SQL Injection**: Wajib menggunakan Django ORM parameterization. Jangan pernah memakai `raw()` dengan string formatting.
- **Cross-Site Scripting (XSS)**: Gunakan auto-escaping bawaan Django template engine, terapkan `Content-Security-Policy` (CSP) header via `django-csp`.
- **CSRF Protection**: CSRF cookie dengan flag `HttpOnly`, `SameSite='Lax'` (atau `'Strict'`), dan `CSRF_COOKIE_SECURE=True` pada environment produksi.
- **Session Security**:
  ```python
  SESSION_COOKIE_HTTPONLY = True
  SESSION_COOKIE_SECURE = True  # Production
  SESSION_COOKIE_SAMESITE = 'Lax'
  SESSION_EXPIRE_AT_BROWSER_CLOSE = False
  SESSION_COOKIE_AGE = 60 * 60 * 4  # 4 jam durasi sesi
  ```
- **Rate Limiting & Anti-Bruteforce**:
  Terapkan rate limiting pada endpoint autentikasi, autosave jawaban, dan download challenge attachment (misal menggunakan `django-ratelimit` atau Redis/Cache-backed throttling).

### B. Secure Attachment Sandbox (Hacker Contest Specific)
1. **No Script Execution in Uploads**: Direktori media attachment dilarang mengeksekusi PHP/Python/CGI. Nonaktifkan engine execution melalui `.htaccess` atau Nginx configuration.
2. **Download Token & Pre-signed URL**: File challenge tidak boleh diakses via direct public static path, melainkan melalui endpoint terautentikasi yang memvalidasi hak akses peserta, status aktif kuis, dan audit download log.
3. **MIME Type & Integrity Hash**: Setiap file soal memiliki SHA-256 checksum yang diverifikasi otomatis.

---

## 4. Code Quality & Verification Rules
1. **Type Hints**: Gunakan type annotations di seluruh fungsi dan metode service layer.
2. **Comprehensive Testing**:
   - Model tests: integritas relasi, constraints, dan custom methods.
   - Service tests: skenario batas waktu kuis, concurrency submission, kalkulasi skor.
   - Security tests: uji akses unauthorized, expired token, rate-limit, dan parameter tampering.
3. **Audit Logging**: Catat setiap event penting (Login, Start Exam, Autosave Answer, Download Challenge File, Final Submit, Admin Scoring) dengan timestamp presisi mikrodetik dan IP address/User Agent.
