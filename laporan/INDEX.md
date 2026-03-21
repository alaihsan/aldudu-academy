# 📚 Dokumentasi Rasch Model - Aldudu Academy

## 🎯 Selamat Datang di Dokumentasi Rasch Model

Dokumentasi ini berisi panduan lengkap implementasi Rasch Model di Aldudu Academy.

---

## 📖 Daftar Dokumentasi

### 1. [IMPLEMENTASI_LENGKAP.md](01_IMPLEMENTASI_LENGKAP.md)

**Untuk:** Developer, Technical Team  
**Isi:**
- Pendahuluan & latar belakang
- Arsitektur sistem (diagram)
- Database schema detail
- Alur kerja (flow diagrams)
- Implementasi detail (code examples)
- Testing guide
- Deployment guide
- Troubleshooting

**Baca jika:** Anda ingin memahami technical implementation secara mendalam.

---

### 2. [API_REFERENCE.md](02_API_REFERENCE.md)

**Untuk:** Developer, API Consumers  
**Isi:**
- Base URL & authentication
- Threshold & Trigger endpoints
- Analysis Management endpoints
- Results endpoints (persons, items, wright-map)
- Bloom Taxonomy endpoints
- Error responses
- Rate limiting
- Client libraries (Python, JavaScript examples)
- Best practices

**Baca jika:** Anda ingin mengintegrasikan Rasch API ke aplikasi lain.

---

### 3. [USER_GUIDE.md](03_USER_GUIDE.md)

**Untuk:** Guru, Siswa  
**Isi:**
- **Untuk Guru:**
  - Mengenal Rasch Model
  - Memulai Rasch Analysis
  - Membaca hasil analisis (5 tabs)
  - Tindak lanjut berdasarkan hasil
- **Untuk Siswa:**
  - Mengenal ability measure
  - Membaca ability dashboard
  - Fit statistics interpretation
  - Rekomendasi belajar
  - History tracking
- FAQ untuk guru & siswa

**Baca jika:** Anda adalah pengguna (user) sistem Rasch.

---

### 4. [README_RASCH.md](README_RASCH.md)

**Untuk:** Semua pengguna  
**Isi:**
- Panduan lengkap instalasi
- Konfigurasi environment
- Cara menggunakan (step-by-step)
- Interpretasi hasil
- Troubleshooting
- FAQ

**Baca jika:** Anda ingin panduan praktis instalasi & penggunaan.

---

## 🚀 Quick Start

### Untuk Developer

1. **Baca:** [IMPLEMENTASI_LENGKAP.md](01_IMPLEMENTASI_LENGKAP.md) - Bab Arsitektur Sistem
2. **Setup:** Install dependencies & run migration
3. **Test:** Jalankan testing guide
4. **Deploy:** Follow deployment guide

### Untuk Guru

1. **Baca:** [USER_GUIDE.md](03_USER_GUIDE.md) - Bagian 1 (Untuk Guru)
2. **Practice:** Enable Rasch untuk quiz pertama Anda
3. **Monitor:** Check threshold progress
4. **Analyze:** Lihat hasil analisis & interpretasi

### Untuk Siswa

1. **Baca:** [USER_GUIDE.md](03_USER_GUIDE.md) - Bagian 2 (Untuk Siswa)
2. **Access:** Buka "Kemampuan Saya" di course Anda
3. **Understand:** Pelajari ability measure Anda
4. **Improve:** Follow rekomendasi belajar

### Untuk API Developer

1. **Baca:** [API_REFERENCE.md](02_API_REFERENCE.md)
2. **Authenticate:** Login untuk dapat session
3. **Test:** Gunakan curl atau Postman
4. **Integrate:** Gunakan client library examples

---

## 📊 Implementation Overview

### Apa itu Rasch Model?

Rasch Model adalah teori pengukuran modern yang:
- Mengukur **kemampuan siswa** (θ) dan **kesulitan soal** (δ) dalam skala yang sama
- **Objective**: Sample-free (ability tidak tergantung grup siswa)
- **Item-free**: Difficulty tidak tergantung test tertentu
- **Quality Control**: Fit statistics untuk deteksi soal bermasalah

### Kapan Menggunakan Rasch?

**Gunakan Rasch untuk:**
- ✅ Ujian tengah semester (banyak siswa)
- ✅ Ujian akhir semester
- ✅ Quiz dengan ≥30 siswa
- ✅ Analisis kualitas soal
- ✅ Validasi instrumen penilaian

**Tidak perlu Rasch untuk:**
- ❌ Quiz harian dengan <10 siswa
- ❌ Tugas individu
- ❌ Penilaian formatif cepat

### Komponen Utama

```
┌─────────────────────────────────────────────────────────────┐
│                    Rasch System                             │
│                                                             │
│  ┌──────────────────┐    ┌──────────────────┐              │
│  │  Frontend        │    │  Backend         │              │
│  │  ├── Dashboard   │    │  ├── JMLE        │              │
│  │  │   ├── Teacher │    │  ├── Threshold   │              │
│  │  │   └── Student │    │  ├── Celery      │              │
│  │  └── Charts      │    │  └── API         │              │
│  └──────────────────┘    └──────────────────┘              │
│                                                             │
│  ┌──────────────────┐    ┌──────────────────┐              │
│  │  Database        │    │  Infrastructure  │              │
│  │  ├── Analyses    │    │  ├── Redis       │              │
│  │  ├── Persons     │    │  └── MySQL       │              │
│  │  └── Items       │    │                  │              │
│  └──────────────────┘    └──────────────────┘              │
└─────────────────────────────────────────────────────────────┘
```

### Alur Kerja Singkat

```
1. Siswa kerjakan quiz → Submit
2. System hitung classical score (instant)
3. System check threshold (≥30 siswa?)
4. Jika threshold terpenuhi → Auto-trigger Rasch analysis
5. Background worker jalankan JMLE algorithm
6. Simpan hasil (ability θ, difficulty δ)
7. Guru & siswa bisa lihat hasil di dashboard
```

---

## 📁 File Structure

```
aldudu-academy/
├── laporan/
│   ├── INDEX.md                        ← Anda di sini
│   ├── 01_IMPLEMENTASI_LENGKAP.md      ← Technical docs
│   ├── 02_API_REFERENCE.md             ← API docs
│   ├── 03_USER_GUIDE.md                ← User docs
│   └── README_RASCH.md                 ← Installation guide
│
├── app/
│   ├── blueprints/
│   │   ├── rasch.py                    ← API routes
│   │   └── rasch_dashboard.py          ← Dashboard routes
│   ├── services/
│   │   ├── rasch_analysis_service.py   ← JMLE algorithm
│   │   └── rasch_threshold_service.py  ← Auto-trigger
│   ├── workers/
│   │   └── rasch_worker.py             ← Celery tasks
│   ├── models/
│   │   └── rasch.py                    ← SQLAlchemy models
│   └── templates/rasch/
│       ├── teacher_dashboard.html      ← Teacher UI
│       ├── analysis_detail.html        ← Analysis detail UI
│       └── student_ability.html        ← Student UI
│
├── migrations/
│   └── 002_rasch_model_mysql.sql       ← Database migration
│
└── scripts/
    └── run_rasch_migration.py          ← Migration runner
```

---

## 🎓 Referensi Akademis

1. **Rasch, G.** (1960). *Probabilistic Models for Some Intelligence and Attainment Tests*. Copenhagen: Danish Institute for Educational Research.
   - **Foundational work** untuk Rasch Model

2. **Bond, T. G., & Fox, C. M.** (2015). *Applying the Rasch Model: Fundamental Measurement in the Human Sciences* (3rd ed.). Routledge.
   - **Practical guide** untuk aplikasi Rasch

3. **Wright, B. D., & Masters, G. N.** (1982). *Rating Scale Analysis*. Chicago: MESA Press.
   - **Rating Scale Model** untuk rubric-based assessment

4. **Fischer, G. H., & Molenaar, I. W.** (1995). *Rasch Models: Foundations, Recent Developments, and Applications*. Springer.
   - **Comprehensive reference** untuk teori & aplikasi

5. **Linacre, J. M.** (2002). *What do INFIT and OUTFIT Mean-Square and Standardized mean?* Rasch Measurement Transactions, 16(2), 878.
   - **Fit statistics** interpretation guide

---

## 🔧 Support & Troubleshooting

### Dokumentasi Tidak Menjawab Pertanyaan Anda?

1. **Check FAQ** di setiap dokumentasi
2. **Search Issues** di repository
3. **Contact Support** via email/ticket

### Common Issues & Solutions

| Issue | Documentation | Section |
|-------|---------------|---------|
| Migration fails | README_RASCH.md | Installation |
| API 404 error | API_REFERENCE.md | Error Responses |
| Analysis tidak auto-trigger | IMPLEMENTASI_LENGKAP.md | Troubleshooting |
| Wright Map tidak render | USER_GUIDE.md | FAQ |

---

## 📈 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-03-21 | Initial release - Complete implementation |

---

## ✅ Checklist Membaca

### Untuk Developer Baru
- [ ] Baca IMPLEMENTASI_LENGKAP.md - Bab Pendahuluan
- [ ] Baca IMPLEMENTASI_LENGKAP.md - Bab Arsitektur
- [ ] Setup development environment
- [ ] Run migration
- [ ] Test API endpoints

### Untuk Guru
- [ ] Baca USER_GUIDE.md - Bagian 1 (Untuk Guru)
- [ ] Enable Rasch untuk 1 quiz
- [ ] Monitor threshold progress
- [ ] Lihat hasil analisis pertama

### Untuk Siswa
- [ ] Baca USER_GUIDE.md - Bagian 2 (Untuk Siswa)
- [ ] Access "Kemampuan Saya"
- [ ] Pahami ability measure sendiri
- [ ] Follow rekomendasi belajar

### Untuk API Developer
- [ ] Baca API_REFERENCE.md - Authentication
- [ ] Test threshold status endpoint
- [ ] Test get persons endpoint
- [ ] Integrate ke aplikasi lain

---

## 🎯 Next Steps

Setelah membaca dokumentasi:

1. **Practice:** Implementasikan untuk quiz pertama Anda
2. **Share:** Bagikan pengetahuan ke rekan guru/siswa
3. **Feedback:** Berikan feedback untuk improvement
4. **Explore:** Eksplor advanced features (Wright Map, Bloom analysis)

---

**Dokumentasi ini dibuat untuk Aldudu Academy**  
**Version:** 1.0  
**Last Updated:** 2026-03-21

---

## 🔗 Quick Links

- [→ IMPLEMENTASI_LENGKAP.md](01_IMPLEMENTASI_LENGKAP.md)
- [→ API_REFERENCE.md](02_API_REFERENCE.md)
- [→ USER_GUIDE.md](03_USER_GUIDE.md)
- [→ README_RASCH.md](README_RASCH.md)
