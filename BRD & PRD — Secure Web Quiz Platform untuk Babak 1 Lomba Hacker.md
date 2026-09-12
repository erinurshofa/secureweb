# Secure Web Quiz Platform — Babak 1 Lomba Hacker

## 1. Classification of Information

| Kategori | Pernyataan |
|---|---|
| **Fact** | Sistem akan digunakan untuk babak 1 lomba hacker. |
| **Fact** | Sistem berbasis web. |
| **Fact** | Soal harus mendukung pilihan ganda. |
| **Fact** | Soal harus mendukung essay. |
| **Fact** | Soal dapat memiliki file yang dapat diunduh peserta untuk dianalisis. |
| **Assumption** | Babak dilakukan secara serentak dengan batas waktu tertentu. |
| **Assumption** | Pilihan ganda dapat dinilai otomatis. |
| **Assumption** | Essay dinilai manual oleh juri/admin. |
| **Assumption** | Peserta memiliki akun masing-masing. |
| **Assumption** | Sistem diakses melalui internet publik. |
| **Recommendation** | Semua kontrol penting harus ditegakkan oleh backend/server, bukan frontend. |
| **Recommendation** | Attachment disimpan pada private object storage yang terpisah dari application server. |
| **Recommendation** | Admin menggunakan MFA/2FA. |
| **Open Question** | Apakah peserta individu atau berupa tim? |
| **Open Question** | Berapa estimasi jumlah peserta dan concurrent users? |
| **Open Question** | Apakah attachment dapat berupa executable, binary, PCAP, ZIP, source code, atau malware sample? |
| **Open Question** | Apakah soal setiap peserta sama atau akan diacak? |
| **Open Question** | Apakah peserta diperbolehkan membuka internet selama lomba? |
| **Open Question** | Apakah satu akun diperbolehkan berpindah perangkat? |

---

# BAGIAN A — BRD

## 2. Business Context

Panitia membutuhkan platform ujian berbasis web untuk melakukan seleksi babak pertama lomba hacker.

Berbeda dengan sistem kuis umum, pengguna platform merupakan peserta dengan kompetensi keamanan siber. Karena itu client/browser tidak dapat dianggap trusted.

Platform harus menjaga tiga aspek utama:

**Confidentiality:** soal tidak dapat diakses sebelum waktu lomba atau oleh peserta yang tidak berhak.

**Integrity:** jawaban, nilai, waktu ujian, dan status submission tidak dapat dimanipulasi dari browser/API.

**Availability:** sistem tetap dapat digunakan oleh seluruh peserta selama periode lomba.

---

## 3. Problem Statement

Panitia membutuhkan mekanisme terpusat untuk:

1. Membuat dan mengelola soal.
2. Menyelenggarakan kuis dengan waktu yang terkontrol.
3. Menyediakan attachment untuk analisis peserta.
4. Menyimpan jawaban secara aman.
5. Melakukan penilaian otomatis dan manual.
6. Memantau jalannya lomba.
7. Memastikan peserta tidak dapat memperoleh soal atau memodifikasi hasil melalui manipulasi client/API.

---

## 4. Business Objective

| ID | Objective |
|---|---|
| BO-001 | Menyelenggarakan babak seleksi secara online dengan proses yang konsisten untuk seluruh peserta. |
| BO-002 | Menjamin soal hanya tersedia dalam periode kompetisi yang ditentukan. |
| BO-003 | Menjamin jawaban peserta tersimpan dan dapat diaudit. |
| BO-004 | Mengurangi pekerjaan manual melalui automatic scoring pilihan ganda. |
| BO-005 | Mendukung penilaian manual untuk essay. |
| BO-006 | Melindungi sistem dari manipulasi teknis oleh peserta. |
| BO-007 | Menyediakan hasil kompetisi yang traceable dan dapat diverifikasi panitia. |

---

## 5. Scope

### In Scope

Pengelolaan peserta, autentikasi, manajemen event/lomba, bank soal, pilihan ganda, essay, attachment soal, konfigurasi waktu lomba, pengerjaan ujian, autosave jawaban, final submission, auto scoring pilihan ganda, manual grading essay, leaderboard/result internal, audit log, monitoring ujian, serta export hasil.

### Out of Scope — Versi Awal

Proctoring menggunakan webcam, AI plagiarism detection, browser lockdown penuh, remote desktop monitoring, payment, sertifikat, forum peserta, chat peserta, serta platform CTF yang menjalankan vulnerable machines/container per peserta.

Jika challenge membutuhkan target mesin yang benar-benar dieksploitasi, **target tersebut sebaiknya menjadi platform/lingkungan terpisah dari quiz application**.

---

## 6. Stakeholder

| Stakeholder | Kepentingan |
|---|---|
| Organizer | Mengatur kompetisi secara keseluruhan. |
| Question Author | Membuat soal dan attachment. |
| Reviewer | Memeriksa soal sebelum dipublikasikan. |
| Judge | Menilai jawaban essay. |
| Participant | Mengerjakan kuis. |
| Technical Admin | Mengelola deployment dan operasional sistem. |
| Security Administrator | Monitoring keamanan dan incident handling. |

---

## 7. As-Is Process

**Assumption karena proses saat ini belum diberikan.**

Diasumsikan proses sebelumnya menggunakan form, spreadsheet, LMS umum, atau mekanisme manual sehingga terdapat risiko pengaturan timer, distribusi attachment, penilaian, dan audit trail yang tidak terintegrasi.

Informasi proses saat ini perlu dikonfirmasi sebelum BRD dianggap final.

---

## 8. To-Be Process

```text
Organizer membuat Competition
        ↓
Author membuat soal
        ↓
Reviewer memeriksa soal
        ↓
Soal dipublish/freeze
        ↓
Peserta login
        ↓
Sebelum waktu mulai → soal tidak tersedia
        ↓
Competition OPEN
        ↓
Peserta mulai attempt
        ↓
Soal + attachment tersedia sesuai permission
        ↓
Jawaban autosave
        ↓
Peserta submit / waktu habis
        ↓
Attempt dikunci
        ↓
MCQ dinilai otomatis
        ↓
Essay dinilai Judge
        ↓
Final score dihitung
        ↓
Organizer melakukan finalisasi hasil
```

---

# 9. Business Requirements

| ID | Requirement | Priority |
|---|---|---|
| BR-001 | Sistem harus mendukung kompetisi dengan tanggal dan waktu mulai serta selesai. | Must |
| BR-002 | Sistem harus mendukung soal pilihan ganda. | Must |
| BR-003 | Sistem harus mendukung soal essay. | Must |
| BR-004 | Soal harus dapat memiliki satu atau lebih attachment untuk dianalisis peserta. | Must |
| BR-005 | Peserta hanya dapat mengakses kompetisi yang diberikan kepadanya. | Must |
| BR-006 | Soal tidak boleh dapat diakses sebelum kompetisi dibuka. | Must |
| BR-007 | Sistem harus menyimpan jawaban peserta secara reliable selama pengerjaan. | Must |
| BR-008 | Sistem harus melakukan final submission ketika peserta menekan Submit. | Must |
| BR-009 | Sistem harus dapat melakukan auto-submit ketika waktu pengerjaan berakhir. | Must |
| BR-010 | Pilihan ganda dapat dinilai otomatis berdasarkan answer key. | Must |
| BR-011 | Essay dapat diberikan score dan komentar oleh Judge. | Must |
| BR-012 | Aktivitas administratif penting harus memiliki audit trail. | Must |
| BR-013 | Organizer harus dapat melihat dan mengekspor hasil kompetisi. | Must |
| BR-014 | Sistem harus menerapkan role dan permission berbeda untuk peserta dan administrator. | Must |
| BR-015 | Sistem harus menyediakan mekanisme penanganan soal bermasalah tanpa menghilangkan audit trail. | Should |

---

# 10. Business Rules

| ID | Rule |
|---|---|
| BRULE-001 | Waktu resmi kompetisi ditentukan oleh server. |
| BRULE-002 | Clock pada browser peserta tidak menjadi sumber waktu resmi. |
| BRULE-003 | Peserta tidak dapat memulai attempt sebelum waktu kompetisi. |
| BRULE-004 | Setelah waktu habis, backend menolak perubahan jawaban. |
| BRULE-005 | Setelah final submission berhasil, jawaban peserta menjadi read-only. |
| BRULE-006 | Peserta hanya dapat membaca attempt miliknya sendiri. |
| BRULE-007 | Peserta tidak boleh mendapatkan answer key melalui API sebelum hasil secara resmi dibuka. |
| BRULE-008 | Perubahan soal setelah kompetisi dimulai dilarang kecuali melalui emergency correction workflow yang tercatat. |
| BRULE-009 | Download attachment hanya diperbolehkan apabila peserta mempunyai active/authorized attempt. |
| BRULE-010 | Score final berasal dari data server, bukan score yang dihitung browser. |
| BRULE-011 | Administrative action yang memengaruhi soal, jawaban, nilai, atau status peserta harus tercatat dalam audit log. |
| BRULE-012 | Direct object identifier tidak boleh sekaligus menjadi bukti authorization. |

---

# 11. Constraints

Sistem harus berjalan melalui HTTPS.

Database dan storage tidak boleh dapat diakses langsung dari internet publik.

Server harus tetap menjadi authoritative source untuk time, permission, status attempt, jawaban, dan scoring.

Browser peserta dianggap lingkungan yang dapat dimodifikasi menggunakan DevTools, proxy seperti Burp Suite, custom HTTP client, script, atau automation.

Security baseline direkomendasikan mengacu pada OWASP ASVS 5.0.0.

---

# 12. Risk & Dependency

| Risiko | Dampak | Mitigasi |
|---|---|---|
| Peserta menebak ID soal peserta lain / IDOR | Kebocoran soal/jawaban | Authorization pada setiap object request |
| API dipanggil langsung tanpa frontend | Manipulasi workflow | Server-side validation |
| Manipulasi JavaScript timer | Waktu ujian bertambah | Server-authoritative deadline |
| Session dicuri | Account takeover | Secure session cookie, TLS, expiration |
| Attachment URL dibagikan | Kebocoran challenge | Short-lived authorization/signed download |
| Attachment berbahaya | Compromise server/client | Isolated object storage + controlled upload pipeline |
| Admin account diambil alih | Kebocoran seluruh soal | MFA + RBAC + audit log |
| SQL injection | Data compromise | Parameterized query/ORM + validation |
| XSS pada soal essay | Session/admin compromise | Output encoding/sanitization + CSP |
| Request flood | Availability turun | CDN/WAF/rate limiting |
| Banyak peserta submit bersamaan | DB overload | Capacity/load testing |
| Browser/network peserta terputus | Kehilangan jawaban | Autosave + retry + idempotency |
| Insider membocorkan soal | Integritas kompetisi | Least privilege + audit + publication controls |

---

# 13. Success Metrics

Target numerik harus dikonfirmasi setelah jumlah peserta diketahui.

| Metric | Target Awal / Status |
|---|---|
| Jawaban yang berhasil tersimpan | Recommendation: ≥ 99.99% accepted saves |
| Availability selama lomba | Recommendation: ≥ 99.9% |
| Kehilangan jawaban karena sistem | Target: 0 |
| Peserta dapat menyelesaikan submit | Target: 100% peserta yang memiliki koneksi valid |
| Unauthorized question access | Target: 0 |
| Unauthorized answer modification | Target: 0 |
| Administrative changes without audit trail | Target: 0 |
| Response time API normal | Open Question: ditentukan setelah target concurrency tersedia |

---

# BAGIAN B — PRD

## 14. Product Objective

Membangun aplikasi ujian berbasis web yang dapat digunakan untuk babak seleksi kompetisi keamanan siber dengan penekanan pada **security, integrity, traceability, reliability, dan controlled access**.

---

# 15. Persona / User Role

| Role | Fungsi |
|---|---|
| Super Admin | Mengelola seluruh sistem dan administrative users. |
| Organizer | Membuat event dan mengelola peserta serta hasil. |
| Author | Membuat/edit soal sebelum freeze. |
| Reviewer | Mereview dan approve soal. |
| Judge | Menilai essay. |
| Participant | Mengerjakan kompetisi. |
| Auditor / Observer | Read-only monitoring dan audit apabila dibutuhkan. |

---

# 16. Recommended Architecture

```text
                    Internet
                       │
                CDN / DDoS Protection
                       │
                      WAF
                       │
                Load Balancer
                       │
              ┌────────┴────────┐
              │  Web/API App   │
              │ authentication │
              │ authorization  │
              │ quiz engine    │
              └───────┬────────┘
                      │
       ┌──────────────┼───────────────┐
       │              │               │
 PostgreSQL        Redis          Queue/Worker
       │
       │
 Private Object Storage
 (Question Attachments)

       │
 Separate download hostname/domain
 tanpa application session cookie
```

### Architecture Recommendation

Untuk versi pertama, **modular monolith** lebih disarankan daripada microservices.

Alasannya adalah attack surface, distributed state, operational complexity, dan consistency problem menjadi lebih kecil.

Komponen logis tetap dipisahkan:

```text
Identity
Competition
Participant
Question Bank
Attempt
Answer
Scoring
Attachment
Audit
Reporting
```

---

# 17. User Journey

## Participant

```text
Login
 ↓
Dashboard
 ↓
Competition tersedia
 ↓
Menunggu OPEN
 ↓
Start Attempt
 ↓
Mengerjakan soal
 ├─ MCQ
 ├─ Essay
 └─ Download attachment
 ↓
Autosave
 ↓
Review Answers
 ↓
Submit
 ↓
Confirmation
 ↓
Attempt Locked
```

## Organizer

```text
Login + MFA
 ↓
Create Competition
 ↓
Configure Schedule
 ↓
Import Participants
 ↓
Create / Assign Questions
 ↓
Review
 ↓
Freeze
 ↓
Monitor Competition
 ↓
Close
 ↓
Essay Grading
 ↓
Finalize Score
 ↓
Export Results
```

---

# 18. Functional Requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-001 | User dapat melakukan login menggunakan credential yang diberikan. | Must |
| FR-002 | Admin dapat membuat Competition. | Must |
| FR-003 | Competition memiliki start time dan end time. | Must |
| FR-004 | Admin dapat membuat soal tipe single-answer multiple choice. | Must |
| FR-005 | Admin dapat membuat soal tipe essay. | Must |
| FR-006 | Admin dapat menambahkan attachment pada soal. | Must |
| FR-007 | Participant dapat mengunduh attachment dari soal yang berhak diakses. | Must |
| FR-008 | Participant dapat memilih jawaban pilihan ganda. | Must |
| FR-009 | Participant dapat mengisi jawaban essay. | Must |
| FR-010 | Sistem melakukan autosave jawaban. | Must |
| FR-011 | Participant dapat berpindah soal tanpa kehilangan jawaban tersimpan. | Must |
| FR-012 | Sistem menampilkan timer berdasarkan server deadline. | Must |
| FR-013 | Participant dapat melakukan final submission. | Must |
| FR-014 | Sistem melakukan auto-submit ketika deadline tercapai. | Must |
| FR-015 | Sistem menolak update jawaban setelah submission/deadline. | Must |
| FR-016 | Sistem melakukan automatic scoring untuk pilihan ganda. | Must |
| FR-017 | Judge dapat menilai jawaban essay. | Must |
| FR-018 | Organizer dapat melihat hasil peserta. | Must |
| FR-019 | Organizer dapat mengekspor hasil. | Must |
| FR-020 | Sistem mencatat security-relevant dan administrative activity. | Must |
| FR-021 | Admin dapat melihat status peserta: belum mulai, mengerjakan, submitted. | Should |
| FR-022 | Admin dapat melakukan invalidate question dan recalculate score dengan audit record. | Should |
| FR-023 | Sistem dapat randomize urutan soal per participant. | Could |
| FR-024 | Sistem dapat randomize pilihan jawaban MCQ. | Could |
| FR-025 | Participant dapat menandai soal untuk direview sebelum submit. | Should |
| FR-026 | Sistem dapat menampilkan download checksum attachment. | Should |

---

# 19. Question Data Requirement

Contoh model konseptual:

```text
Question
--------
id
competition_id
type
title
body
points
sequence
status
created_by
created_at
updated_at
version

QuestionOption
--------------
id
question_id
option_text
is_correct
display_order

QuestionAttachment
------------------
id
question_id
object_key
original_filename
display_filename
mime_type
size
sha256
status

Answer
------
id
attempt_id
question_id
question_version
selected_option_id
essay_text
saved_at
revision
```

`is_correct` tidak boleh dikirim melalui Participant API.

---

# 20. Attachment Security

Attachment menjadi komponen yang sangat sensitif pada sistem ini.

OWASP merekomendasikan validasi tipe/extension, filename yang dikontrol aplikasi, batas ukuran, penyimpanan di server terpisah atau di luar web root, authorization, dan scanning bila relevan.

### Recommended Download Flow

```text
Participant
    │
GET /questions/{id}/attachments/{id}/download
    │
    ▼
Quiz API
    │
    ├─ validate authentication
    ├─ validate competition
    ├─ validate participant enrollment
    ├─ validate attempt status
    ├─ validate competition time
    └─ audit download
    │
    ▼
Generate short-lived download authorization
    │
    ▼
Private Object Storage
```

Requirement keamanan attachment:

| ID | Requirement |
|---|---|
| NFR-ATT-001 | Storage bucket harus private. |
| NFR-ATT-002 | Object tidak dapat diakses melalui predictable public URL. |
| NFR-ATT-003 | Download hanya diberikan setelah authorization check. |
| NFR-ATT-004 | Download authorization harus memiliki expiry pendek. |
| NFR-ATT-005 | Storage object key harus generated/random dan tidak memakai original filename sebagai path. |
| NFR-ATT-006 | Original filename diperlakukan sebagai untrusted input. |
| NFR-ATT-007 | Download harus dikirim sebagai attachment dan tidak dieksekusi pada origin aplikasi. |
| NFR-ATT-008 | Download domain direkomendasikan terpisah dari application origin. |
| NFR-ATT-009 | Attachment mempunyai size limit configurable. |
| NFR-ATT-010 | Attachment mempunyai SHA-256 checksum. |
| NFR-ATT-011 | Upload attachment hanya diperbolehkan bagi authorized administrator. |

**Open Question penting:** bila panitia memang ingin mendistribusikan malware sample atau intentionally malicious executable sebagai challenge, workflow scanning dan distribusinya harus dirancang terpisah. Antivirus biasa justru dapat menghapus/quarantine artifact tersebut.

---

# 21. Role & Permission Matrix

| Capability | Participant | Judge | Author | Organizer | Super Admin |
|---|---:|---:|---:|---:|---:|
| View active question | ✓ | - | ✓ | ✓ | ✓ |
| View answer key | - | Limited | ✓* | ✓ | ✓ |
| Submit answer | ✓ | - | - | - | - |
| Download challenge file | ✓ | ✓ | ✓ | ✓ | ✓ |
| Create question | - | - | ✓ | ✓ | ✓ |
| Publish question | - | - | - | ✓ | ✓ |
| Grade essay | - | ✓ | - | ✓ | ✓ |
| Modify score | - | Limited | - | ✓ | ✓ |
| View audit log | - | - | - | ✓ | ✓ |
| Manage admin roles | - | - | - | - | ✓ |

`*` akses Author terhadap answer key setelah competition freeze dapat dibatasi sesuai kebijakan panitia.

Semua authorization harus dilakukan backend. Authentication saja tidak cukup untuk menentukan akses resource.

---

# 22. Validation

Contoh server-side validations:

| Area | Validation |
|---|---|
| Start Attempt | Participant terdaftar + competition OPEN + belum melewati batas attempt |
| Get Question | Participant memiliki authorized attempt |
| Save Answer | Attempt IN_PROGRESS + belum deadline + question termasuk competition |
| MCQ | Option harus berasal dari question yang sedang dijawab |
| Essay | Character/byte limit |
| Attachment | Question authorization + event state |
| Submit | Attempt milik authenticated participant |
| Grade | User mempunyai Judge permission |
| Change Score | Authorized role + reason wajib |
| Publish | Semua mandatory question data valid |

Frontend validation hanya untuk UX dan **tidak dianggap security control**.

---

# 23. Attempt State Lifecycle

```text
NOT_STARTED
     │
     │ Start
     ▼
IN_PROGRESS
   │      │
   │      └── server deadline ──► AUTO_SUBMITTED
   │
   └── participant submit ──────► SUBMITTED

SUBMITTED / AUTO_SUBMITTED
              │
              ▼
        PENDING_GRADING
              │
              ▼
            GRADED
              │
              ▼
          FINALIZED
```

Status harus mempunyai allowed transition yang eksplisit.

Request seperti:

```text
FINALIZED → IN_PROGRESS
SUBMITTED → IN_PROGRESS
```

harus ditolak kecuali terdapat privileged administrative recovery workflow dengan audit trail.

---

# 24. Question Lifecycle

```text
DRAFT
  ↓
IN_REVIEW
  ↓
APPROVED
  ↓
FROZEN
  ↓
ACTIVE
  ↓
CLOSED
  ↓
ARCHIVED
```

Setelah `FROZEN`, perubahan konten soal tidak boleh dilakukan melalui edit biasa.

Hal ini mencegah pertanyaan yang diterima peserta pertama berbeda diam-diam dengan peserta berikutnya.

---

# 25. Autosave Design

Recommendation:

```text
User changes answer
        ↓
debounce 1–3 seconds
        ↓
PUT /attempts/{attempt}/answers/{question}
        ↓
server validates attempt
        ↓
save answer revision
        ↓
return:
{
    revision,
    saved_at,
    server_time
}
```

UI menampilkan:

```text
Saving...
Saved 14:03:21
Connection lost
Retrying...
```

Endpoint save harus idempotent atau memiliki revision/idempotency protection sehingga retry karena jaringan tidak menghasilkan state yang tidak konsisten.

---

# 26. Submission Integrity

Submission direkomendasikan berupa transaction di server:

```text
BEGIN

lock attempt

validate:
- owner
- current status
- server deadline
- competition status

set submitted_at
set status

freeze answers

COMMIT
```

Endpoint submission harus idempotent.

Jika browser mengirim `Submit` dua kali, hasilnya tetap satu submission.

---

# 27. Timer Design

Jangan menggunakan:

```javascript
remainingTime = 60 * 60
```

sebagai sumber aturan bisnis.

Gunakan:

```text
server:
started_at
expires_at
```

Browser hanya menghitung tampilan:

```text
remaining = expires_at - estimated_server_time
```

Setiap write request tetap diperiksa server:

```text
if server_time > expires_at:
    reject update
    auto-submit/finalize attempt
```

Dengan demikian perubahan JavaScript/local clock tidak menambah durasi ujian.

---

# 28. Non-Functional Requirements

| ID | Requirement | Priority |
|---|---|---|
| NFR-001 | Seluruh traffic menggunakan HTTPS. | Must |
| NFR-002 | Authentication/session mengikuti secure framework mechanisms. | Must |
| NFR-003 | Session cookie harus Secure dan HttpOnly serta menggunakan SameSite yang sesuai. | Must |
| NFR-004 | Session ID tidak boleh berada di URL. | Must |
| NFR-005 | Password disimpan dengan modern password hashing algorithm. | Must |
| NFR-006 | Administrator menggunakan MFA. | Must |
| NFR-007 | Authorization diverifikasi pada setiap protected resource. | Must |
| NFR-008 | Semua query database menggunakan parameterized query/secure ORM. | Must |
| NFR-009 | Sistem menerapkan output encoding/sanitization terhadap user-generated content. | Must |
| NFR-010 | CSRF protection diterapkan untuk state-changing browser requests bila menggunakan cookie session. | Must |
| NFR-011 | API memiliki rate limiting. | Must |
| NFR-012 | Application secret tidak disimpan dalam source repository. | Must |
| NFR-013 | Database tidak exposed langsung ke internet. | Must |
| NFR-014 | Audit log harus append-oriented dan hanya dapat diakses authorized users. | Must |
| NFR-015 | Backup database dibuat dan restore process diuji. | Must |
| NFR-016 | Infrastruktur harus memiliki monitoring dan alerting. | Must |
| NFR-017 | Dependency harus dipantau dan diperbarui terhadap security vulnerability. | Must |
| NFR-018 | Production environment dipisahkan dari development/testing. | Must |
| NFR-019 | Security testing dilakukan sebelum competition. | Must |
| NFR-020 | Load test dilakukan sesuai expected concurrency. | Must |

OWASP merekomendasikan session identifier yang unpredictable, penggunaan HTTPS, secure cookie attributes, session regeneration, server-side expiration, dan lifecycle logging tanpa mencatat raw session token.

---

# 29. Authentication & Session Recommendation

Participant:

```text
username / participant ID
+
password/random access credential
```

Admin:

```text
username/email
+
password
+
MFA
```

Recommendation tambahan:

```text
Participant session ≠ Admin session security policy
```

Admin interface dapat ditempatkan pada route/origin administratif terpisah bila dibutuhkan.

Akun database, middleware, atau service account tidak boleh digunakan untuk login ke frontend. OWASP secara eksplisit memperingatkan pemakaian sensitive/internal accounts pada frontend authentication.

---

# 30. Edge Cases / Error States

| Case | Expected Behavior |
|---|---|
| Refresh browser | Attempt dilanjutkan dari server state. |
| Browser crash | Jawaban terakhir yang acknowledged server tetap tersedia. |
| Network hilang | UI memberi indikator dan melakukan controlled retry. |
| Submit ditekan dua kali | Submission tetap satu kali. |
| Deadline terjadi saat save | Backend menentukan apakah save diterima berdasarkan authoritative timestamp. |
| Download URL expired | Participant meminta authorization URL baru melalui application API. |
| Peserta mengubah question ID | Authorization menghasilkan 403/404 tanpa kebocoran data. |
| Peserta mengirim option ID dari question lain | Request ditolak. |
| Participant membuka API devtools | Tidak memberikan privilege tambahan. |
| Admin mengubah nilai | Reason + actor + timestamp tercatat. |
| Soal ditemukan salah | Organizer menggunakan invalidate-question workflow. |
| Server restart | Attempt tetap tersedia karena state utama tidak hanya berada di memory server. |

---

# 31. Notifications

Untuk MVP, notification bersifat in-app.

Contoh:

```text
Competition starts in ...
Competition has started
10 minutes remaining
5 minutes remaining
Answer saved
Connection interrupted
Submission successful
Competition ended
```

Warning timer merupakan UX saja. Berakhirnya attempt tetap ditentukan backend.

---

# 32. Reporting / Dashboard

Organizer Dashboard:

```text
Total participants
Not Started
In Progress
Submitted
Auto-Submitted
Pending Essay Grading
Graded
Finalized
```

Monitoring tambahan:

```text
submission rate
API error rate
authentication failures
abnormal request rate
attachment download volume
application latency
database health
```

Security dashboard tidak perlu memperlihatkan raw password, token, session identifier, atau answer key secara tidak perlu.

---

# 33. Audit Requirements

Minimal event yang dicatat:

```text
login success/failure
logout
participant attempt start
final submission
auto submission
attachment download
question create/update/publish/freeze
grading action
score adjustment
competition status change
participant account administrative change
role/permission change
```

Contoh event:

```json
{
  "event": "SCORE_UPDATED",
  "actor_id": "...",
  "participant_id": "...",
  "competition_id": "...",
  "old_value": 75,
  "new_value": 80,
  "reason": "...",
  "timestamp": "...",
  "request_id": "..."
}
```

Jangan mencatat raw session token atau password dalam log. OWASP menyarankan penggunaan session-specific correlation value seperti hash daripada session ID mentah.

---

# 34. Integration

MVP tidak membutuhkan external integration selain infrastructure services.

Potential future integrations:

```text
Email provider
SSO
WhatsApp notification
SIEM
Object storage/CDN
External CTF platform
Identity provider
```

Semua merupakan **Could**, bukan requirement saat ini.

---

# 35. User Stories & Acceptance Criteria

## US-001 — Mengerjakan Pilihan Ganda

**Sebagai Participant, saya ingin menjawab soal pilihan ganda, sehingga jawaban saya dapat dinilai secara otomatis.**

Acceptance Criteria:

```text
AC-001
GIVEN attempt berstatus IN_PROGRESS
WHEN participant memilih option valid
THEN sistem menyimpan answer pada attempt miliknya.

AC-002
GIVEN option berasal dari question lain
WHEN participant memanipulasi request
THEN server menolak request.

AC-003
GIVEN deadline telah lewat
WHEN participant mengirim perubahan jawaban
THEN server menolak perubahan tersebut.

AC-004
GIVEN answer berhasil disimpan
THEN server mengembalikan saved timestamp/revision.
```

Priority: **Must**

---

## US-002 — Essay

**Sebagai Participant, saya ingin mengisi jawaban essay, sehingga saya dapat memberikan analisis yang tidak dapat direpresentasikan dengan pilihan ganda.**

Acceptance Criteria:

```text
AC-005
Essay dapat disimpan selama attempt IN_PROGRESS.

AC-006
Jawaban tetap tersedia setelah page refresh.

AC-007
Input yang mengandung HTML/script tidak boleh menyebabkan executable XSS ketika dilihat participant maupun judge.

AC-008
Essay tidak dapat dimodifikasi setelah submission.
```

Priority: **Must**

---

## US-003 — Download Attachment

**Sebagai Participant, saya ingin mengunduh file yang terkait dengan soal, sehingga saya dapat melakukan analisis terhadap artifact tersebut.**

Acceptance Criteria:

```text
AC-009
Participant authorized dapat mengunduh attachment selama competition mengizinkan akses.

AC-010
Participant yang tidak terdaftar pada competition tidak mendapatkan attachment.

AC-011
Direct object-storage URL permanen tidak tersedia secara publik.

AC-012
Download authorization memiliki expiration.

AC-013
Manipulasi attachment ID tidak memberikan file dari question/event yang tidak berhak diakses.

AC-014
Setiap download dicatat pada audit log.
```

Priority: **Must**

---

## US-004 — Final Submit

**Sebagai Participant, saya ingin mengirim jawaban final, sehingga pengerjaan saya resmi tercatat.**

Acceptance Criteria:

```text
AC-015
Submit valid menghasilkan submitted_at di server.

AC-016
Setelah submit, endpoint perubahan jawaban menolak perubahan.

AC-017
Repeated submit tidak membuat duplicate submission.

AC-018
Participant mendapatkan confirmation submission.
```

Priority: **Must**

---

## US-005 — Automatic Deadline

**Sebagai Organizer, saya ingin pengerjaan otomatis ditutup saat batas waktu habis, sehingga seluruh peserta mendapat aturan waktu yang konsisten.**

Acceptance Criteria:

```text
AC-019
Deadline dihitung menggunakan waktu server.

AC-020
Manipulasi jam pada client tidak mengubah deadline.

AC-021
Setelah deadline server tidak menerima perubahan jawaban.

AC-022
Attempt yang belum disubmit berpindah menjadi AUTO_SUBMITTED.
```

Priority: **Must**

---

## US-006 — Essay Grading

**Sebagai Judge, saya ingin memberikan nilai untuk jawaban essay, sehingga jawaban non-objektif dapat diperhitungkan dalam nilai akhir.**

Acceptance Criteria:

```text
AC-023
Hanya Judge/authorized role yang dapat melakukan grading.

AC-024
Score harus berada pada range yang diizinkan question.

AC-025
Setiap perubahan grading mencatat actor, timestamp, previous value, dan new value.

AC-026
Participant tidak dapat mengakses grading endpoint.
```

Priority: **Must**

---

# 36. Release Priority

## MVP — Must

```text
Authentication
RBAC
Competition management
Participant management
MCQ
Essay
Question attachment
Secure download
Attempt
Autosave
Server timer
Submission
Auto-submit
MCQ scoring
Essay grading
Audit log
Results/export
Security controls
Monitoring
Backup
```

## Should

```text
Question review/approval
Question freeze
Flag-for-review
Random question order
Attachment checksum
Invalidate-question/recalculate workflow
Competition monitoring dashboard
```

## Could

```text
Question pool
Different question sets
Randomized options
Email notifications
Advanced analytics
SSO
SIEM integration
```

## Won't for now

```text
Webcam proctoring
Full browser lockdown
AI cheating detection
Integrated vulnerable VM/container environment
Payment
Certificate
```

---

# 37. Security Testing Before Competition

Minimum recommended testing:

```text
Authentication testing
Authorization / IDOR testing
Privilege escalation testing
Session management testing
CSRF testing
XSS testing
SQL injection testing
File access testing
Rate-limit testing
Business-logic bypass testing
Timer manipulation testing
Submission race-condition testing
Mass-assignment testing
API parameter tampering
Load/stress testing
Backup/restore test
```

Karena pesertanya hacker, business-logic testing menjadi sama pentingnya dengan conventional vulnerability scanning.

---

# 38. Critical Security Principle

Aplikasi harus dirancang berdasarkan asumsi:

> Apa pun yang dikirim browser dapat dibaca, diubah, dihapus, direplay, atau dikirim ulang oleh peserta.

Karena itu jangan pernah mempercayai:

```text
role dari frontend
participant_id dari frontend
score dari frontend
timer dari frontend
is_correct dari frontend
question access dari frontend
submitted status dari frontend
filename/path dari frontend
```

Server harus melakukan authorization dan validation secara independen pada setiap operasi sensitif.

---

# 39. Open Questions Sebelum Technical Design Final

| ID | Open Question | Dampak |
|---|---|---|
| OQ-001 | Berapa jumlah peserta maksimal? | Sizing/load test |
| OQ-002 | Individual atau tim? | Account/data model |
| OQ-003 | Berapa durasi babak? | Attempt/timer rules |
| OQ-004 | Satu atau multiple attempts? | Lifecycle |
| OQ-005 | Semua peserta mulai bersamaan atau timer dihitung sejak klik Start? | Business rule |
| OQ-006 | Apakah soal diacak? | Quiz generation |
| OQ-007 | Apakah opsi MCQ diacak? | Answer mapping |
| OQ-008 | Apakah nilai langsung terlihat? | Information disclosure |
| OQ-009 | Apakah peserta bisa kembali ke soal sebelumnya? | Workflow |
| OQ-010 | Apakah attachment dapat berupa EXE/binary/malware sample? | File security architecture |
| OQ-011 | Berapa maksimum ukuran attachment? | Storage/bandwidth |
| OQ-012 | Apakah satu akun boleh login dari lebih dari satu device? | Session policy |
| OQ-013 | Apakah IP peserta dibatasi? | Access policy |
| OQ-014 | Apakah ada passing grade/ranking/tie-breaker? | Scoring rules |
| OQ-015 | Apakah essay memiliki rubric per soal? | Grading model |
| OQ-016 | Apakah peserta dapat melihat hasil/review jawaban setelah lomba? | Data disclosure |
| OQ-017 | Apakah challenge membutuhkan server/container yang bisa dieksploitasi? | Scope/architecture |

---

# 40. Quality Check

**Contradiction:** tidak ditemukan pada requirement yang sudah diketahui.

**Duplicate requirement:** functional requirements yang mirip telah dipisahkan antara business capability dan technical/security control.

**Non-testable requirement:** terminology seperti "aman" telah diterjemahkan menjadi kontrol yang dapat diuji; target performance masih membutuhkan jumlah peserta.

**Missing actor:** actor utama telah diidentifikasi, tetapi role Reviewer/Auditor masih recommendation.

**Missing state:** lifecycle Competition masih perlu didefinisikan pada technical specification berikutnya.

**Missing permission:** baseline RBAC tersedia; detail answer-key visibility perlu keputusan organizer.

**Missing data:** target participant concurrency, attachment type/size, grading rubric, dan competition policy masih belum diketahui.

**Missing dependency:** hosting/cloud provider, email provider, dan external CTF infrastructure belum ditentukan.

---

# 41. Recommended Next Architecture Detail

Setelah open question utama dijawab, rancangan dapat diturunkan menjadi:

```text
1. Database ERD
2. API contract lengkap
3. Sequence diagram login/start/save/submit/download
4. Detailed RBAC matrix
5. Competition state machine
6. Threat model
7. Infrastructure/deployment architecture
8. Admin UI specification
9. Participant UI wireflow
10. QA test cases dan security test cases
```

Dokumen ini merupakan **baseline requirement**, bukan keputusan final terhadap teknologi implementasi.