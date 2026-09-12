---
name: world-class-ui-ux
description: Elite UI/UX Design System, Cyberpunk & Mission-Control aesthetics, micro-animations, and hyper-ergonomic frontend design standards for high-stakes competition platforms.
---

# World-Class UI/UX Design & Engineering Standards

Dokumen standar operasional dan panduan desain pengalaman pengguna (World's #1 UI/UX Design & Frontend Engineering) untuk membangun antarmuka web yang memukau (*visually breathtaking*), berkinerja ultra-responsif, dan memiliki ergonomi kelas atas (*hyper-ergonomic*) khusus untuk kompetisi keamanan siber dan hacker.

---

## 1. Desain Filosofi: "Cyber Mission Control"
Aplikasi lomba hacker bukan sekadar formulir ujian biasa. Antarmuka harus memberikan *feel* seperti **Mission Control / Cyber Defense Terminal**:
1. **Luminous Dark Mode**: Palet latar belakang gelap pekat yang elegan (*Obsidian & Space Cadet*) dipadukan dengan aksen neon berdaya pikat tinggi (*Electric Cyan, Emerald Green, Amber Warning, Crimson Alert*).
2. **Glassmorphism & Depth**: Permukaan kartu semi-transparan dengan efek *backdrop blur*, border tipis berpendar (*subtle 1px border glow*), dan bayangan bertingkat (*layered depth*).
3. **Information Density & Clarity**: Tipografi terstruktur tegas, kontras rasio tinggi (mematuhi WCAG AAA), tanpa distraksi visual yang tidak fungsional.
4. **Micro-Interactions & Liveness**: Setiap interaksi (hover, click, radio selection, autosave pulse, timer warning) memiliki transisi lembut (150ms - 250ms cubic-bezier) yang memberikan feedback instan.

---

## 2. Design System & Design Tokens

### A. Color Palette
```css
:root {
  /* Surface & Background */
  --bg-primary: #07090e;         /* Deep obsidian */
  --bg-secondary: #0d121d;       /* Card background */
  --bg-tertiary: #141c2c;        /* Elevated panels / hover states */
  --bg-glass: rgba(13, 18, 29, 0.75);
  
  /* Borders & Dividers */
  --border-subtle: rgba(255, 255, 255, 0.08);
  --border-accent: rgba(0, 240, 255, 0.3);
  --border-focus: #00f0ff;

  /* Cyber Accents */
  --accent-cyan: #00f0ff;        /* Primary interactive / timer */
  --accent-cyan-glow: rgba(0, 240, 255, 0.25);
  --accent-emerald: #10b981;     /* Answered / Success */
  --accent-emerald-glow: rgba(16, 185, 129, 0.25);
  --accent-amber: #f59e0b;       /* Flagged / Review */
  --accent-crimson: #ef4444;     /* Countdown warning / Danger */

  /* Text & Typography */
  --text-primary: #f8fafc;       /* Highest contrast */
  --text-secondary: #94a3b8;     /* Metadata / labels */
  --text-muted: #64748b;         /* Footers / hints */
  --text-cyan: #38bdf8;
}
```

### B. Typography
- **Display & Headings**: `Outfit`, `Plus Jakarta Sans`, atau `Inter` (font-weight: 600 - 800) dengan tracking rapat.
- **Body UI**: `Inter`, `system-ui` (font-weight: 400, 500) dengan line-height 1.6 untuk keterbacaan soal panjang.
- **Code & Numbers (HUD/Timer)**: `JetBrains Mono`, `Fira Code`, `ui-monospace` (font-variant-numeric: tabular-nums) agar angka tidak bergeser saat detik berubah.

---

## 3. Ergonomi Antarmuka Ujian (Exam Workspace Layout)

### A. Tampilan Layar Pengerjaan Soal (Split-Screen HUD)
```text
┌───────────────────────────────────────────────────────────────────────────┐
│ [LOGO] Babak 1 Hacker Challenge  │ Sisa Waktu: 01:24:39 (Pulsing HUD) │ [Profile] │
├───────────────────────────────────────────────────────────────────────────┤
│                     │                                                     │
│ NAVIGASI SOAL       │ SOAL #04 — REVERSE ENGINEERING (20 PTS)             │
│ [ 1 ][ 2 ][ 3 ][4*] │ ─────────────────────────────────────────────────── │
│ [ 5 ][ 6 ][ 7 ][ 8 ] │ Diberikan binary executable ELF terlampir.          │
│ [ 9 ][10]           │                                                     │
│                     │ [ 📁 challenge_v1.zip (2.4 MB) — Unduh File ]       │
│ Status:             │                                                     │
│ ■ Hijau : Dijawab   │ JAWABAN ANDA:                                       │
│ ■ Kuning: Ragu-ragu │ ( ) A. 0x7F 0x45 0x4C 0x46                          │
│ ■ Abu   : Belum     │ (•) B. 0x4D 0x5A 0x90 0x00                          │
│                     │ ( ) C. 0x89 0x50 0x4E 0x47                          │
│ [✓ Simpan Otomatis] │                                                     │
│                     │ [⬅ Sebelumnya]  [★ Tandai Ragu]  [Selanjutnya ➡]    │
└───────────────────────────────────────────────────────────────────────────┘
```

### B. Fitur Unggulan UI/UX Khusus Kompetisi:
1. **Server-Synchronized Pulsing HUD**:
   - Hijau/Cyan ketika waktu > 30 menit.
   - Amber ketika waktu < 15 menit.
   - Merah berdenyut (*subtle pulse animation*) ketika waktu < 5 menit.
2. **Instant Visual Autosave Feedback**:
   - Status badge berubah secara instan: `Menyimpan...` -> `✓ Tersimpan di Server` dengan timestamp relatif ("baru saja").
3. **Keyboard Accessibility & Shortcuts**:
   - `Alt + N` / `Tombol Panah Kanan`: Soal berikutnya.
   - `Alt + P` / `Tombol Panah Kiri`: Soal sebelumnya.
   - `Alt + R`: Tandai ragu-ragu (*Flag for review*).
   - Tombol `1`, `2`, `3`, `4`: Memilih opsi A, B, C, D langsung dari keyboard.
4. **Zero-Distraction Mode**: Tombol untuk *collapse* sidebar navigasi soal agar peserta dapat fokus penuh menganalisis deskripsi soal.
