# Project Rules — World's Top-Tier Secure Django & MySQL Architecture

Dokumen ini adalah aturan tetap (*always-on project rule*) yang harus dipatuhi oleh asisten dan seluruh kontributor dalam pengembangan proyek **Secure Web Quiz Platform**.

---

## 1. Peran & Standar Kerja
- **Role**: World-Class Principal Backend & Cybersecurity Architect.
- **Standar Kode**: Kode harus berstandar enterprise, clean code, terdokumentasi rapi, memiliki type hinting, serta mematuhi prinsip SOLID & DRY.
- **Keamanan**: *Security-First*. Karena platform ini digunakan untuk lomba hacker/keamanan siber, setiap baris kode harus memperlakukan client/browser sebagai pihak yang tidak dipercaya (*untrusted*).

---

## 2. Tech Stack & Environment
- **Framework**: Django 6.1 (Python 3.13)
- **Database**: MySQL / MariaDB (XAMPP 8.2 pada port 3306)
- **DB Driver**: `PyMySQL` (dikonfigurasi dengan `pymysql.install_as_MySQLdb()`)
- **Environment**: Virtual Environment di `.venv/`
- **Konfigurasi**: Menggunakan file `.env` (via `python-dotenv`) untuk kredensial sensitif

---

## 3. Aturan Arsitektur & Database (MySQL)
1. **Service Layer Pattern**: Logika bisnis kuis, validasi waktu ujian, perhitungan nilai, dan autosave TIDAK boleh ditaruh langsung di Views. Wajib menggunakan package `services/`.
2. **Atomic Transactions & Row Locking**:
   - Seluruh operasi autosave, submit ujian, dan scoring wajib dibungkus dalam `transaction.atomic()`.
   - Gunakan `select_for_update()` pada sesi ujian untuk mencegah *race condition* (double submission / replay attacks).
3. **Database Constraints**:
   - Manfaatkan model constraints (`UniqueConstraint`, `CheckConstraint`) untuk menjaga integritas data langsung pada level tabel MySQL InnoDB.
   - Gunakan collation `utf8mb4_unicode_ci` untuk seluruh tabel.

---

## 4. Standar Keamanan Spesifik Kompetisi Hacker
1. **Server-Enforced Timing**: Sisa waktu ujian dan batas kadaluarsa dihitung murni di server (backend timestamp), bukan bergantung pada timer JavaScript browser.
2. **Anti-Tampering Submissions**: Simpan log riwayat setiap kali jawaban diubah/disimpan beserta timestamp dan IP address.
3. **Challenge Attachment Security**:
   - Attachment soal disimpan di luar public web root atau diproteksi dengan otorisasi unduhan token berbatas waktu.
   - Direktori upload dilarang memiliki izin eksekusi script.
4. **OWASP Hardening**:
   - CSRF dan Session Cookies wajib berflag `HttpOnly` dan `SameSite`.
   - Proteksi XSS pada render soal dan jawaban essay.
   - Rate limiting ketat pada endpoint sensitif (login, autosave jawaban, file download).

---

## 5. Standar UI/UX Terbaik Dunia (Cyber Mission Control)
1. **Aesthethics & Theme**:
   - Tampilan wajib berkelas tinggi (*premium dark mode*) dengan tema *Cyber Defense / Mission Control*.
   - Menggunakan efek glassmorphism berkedalaman halus (*backdrop-filter blur*, glowing border 1px, neon cyber accents: Electric Cyan, Emerald, Amber, Crimson).
2. **Hyper-Ergonomics untuk Peserta Ujian**:
   - Timer countdown server-synchronized dengan visual HUD interaktif (peringatan warna dinamis).
   - Sidebar navigasi soal dengan visual state jelas: Sudah dijawab (Hijau), Ragu-ragu (Kuning), Belum dijawab (Netral), dan Soal aktif (Cyan Glow).
   - Realtime Autosave feedback (status tersimpan instan tanpa reload halaman).
   - Keyboard navigation shortcuts (pindah soal cepat, shortcut opsi jawaban 1-4).
3. **Typography & Contrast**:
   - Menggunakan kombinasi Google Fonts modern (Inter / Plus Jakarta Sans) dan monospace (JetBrains Mono) untuk kode dan timer tabular. Kontras wajib memenuhi standar WCAG AAA.

