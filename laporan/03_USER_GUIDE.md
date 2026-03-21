# 📚 Rasch Model - User Guide

## Untuk Guru dan Siswa

---

## 📖 Bagian 1: Untuk Guru

### 1.1 Mengenal Rasch Model

**Apa itu Rasch Model?**

Rasch Model adalah metode pengukuran modern yang memberikan:
- **Kemampuan Siswa (θ)**: Diukur dalam skala logit, bukan hanya persentase
- **Kesulitan Soal (δ)**: Diukur objektif berdasarkan respons semua siswa
- **Kualitas Soal**: Deteksi soal yang bermasalah melalui fit statistics
- **Peta Kemampuan**: Wright Map untuk visualisasi distribusi

**Perbedaan dengan Nilai Klasik:**

| Aspek | Nilai Klasik | Rasch Model |
|-------|--------------|-------------|
| Skor Siswa | Persentase (0-100) | Ability (θ) dalam logit |
| Sulit Soal | % siswa yang benar | Difficulty (δ) dalam logit |
| Ketergantungan | Tergantung siswa yang ikut | Objektif (sample-free) |
| Minimum Siswa | 1 siswa | 30 siswa (recommended) |
| Ketersediaan | Instant | Setelah threshold terpenuhi |

---

### 1.2 Memulai Rasch Analysis

#### Step 1: Enable Rasch untuk Quiz

1. Buka **Gradebook** mata pelajaran Anda
2. Scroll ke bagian **"Quiz dengan Rasch Analysis"**
3. Klik **"Enable Rasch"** pada quiz yang diinginkan
4. Konfirmasi enablement

**Catatan:**
- Quiz harus sudah memiliki grade item
- Rasch akan auto-trigger setelah 30 siswa mengerjakan
- Anda bisa manual trigger jika ingin analisis lebih cepat

#### Step 2: Monitor Threshold Progress

Setelah enable, Anda akan melihat:
- **Progress Bar**: Menunjukkan jumlah siswa yang sudah submit
- **Status**: Pending, Waiting, Queued, Processing, atau Completed
- **Threshold**: Default 30 siswa

**Status Explanation:**
- ⏳ **Pending**: Menunggu quiz dikerjakan
- 🕐 **Waiting**: Menunggu threshold terpenuhi
- 📬 **Queued**: Masuk antrian untuk diproses
- ⚙️ **Processing**: Sedang dianalisis
- ✅ **Completed**: Analisis selesai
- ❌ **Failed**: Analisis gagal (lihat error message)

#### Step 3: Manual Trigger (Optional)

Jika ingin analisis sebelum threshold:

1. Klik tombol **"🚀 Analyze Now (Bypass Threshold)"**
2. Konfirmasi dengan klik OK
3. Analisis akan dimulai meskipun belum 30 siswa

**Peringatan:**
- Hasil mungkin kurang reliable jika siswa < 20
- Disarankan tunggu minimal 20 siswa untuk hasil yang bermakna

---

### 1.3 Membaca Hasil Analisis

#### Dashboard Overview

Setelah analisis selesai, klik **"Lihat Hasil"** untuk melihat detail.

**Tab 1: Overview**

Menampilkan:
- **Person Separation Index**: Daya beda kemampuan siswa
  - ≥ 2.0: Good (dapat membedakan 3 level kemampuan)
  - ≥ 3.0: Excellent (dapat membedakan 4+ level)
  
- **Cronbach's Alpha**: Reliabilitas soal
  - ≥ 0.9: Excellent
  - 0.8 - 0.9: Good
  - 0.7 - 0.8: Acceptable
  - < 0.7: Questionable (perlu review soal)
  
- **Item Separation Index**: Daya beda kesulitan soal
  - ≥ 2.0: Good hierarchy
  - ≥ 3.0: Excellent hierarchy

**Distribution Charts:**
- **Person Ability**: Histogram distribusi kemampuan siswa
- **Item Difficulty**: Histogram distribusi kesulitan soal

#### Tab 2: Wright Map

**Cara Membaca Wright Map:**

```
Logit    Person          Item
  2.5 |           ● S1 (Very High)
  2.0 |        ● S2
  1.5 |     ● S3      ■ Q5 (Difficult)
  1.0 |  ● S4    ■ Q4
  0.5 |────────────■ Q3 (Average)───────── Mean
  0.0 |     ■ Q2
 -0.5 |  ● S5   ■ Q1 (Easy)
 -1.0 | ● S6
 -1.5 | ● S7 (Very Low)

● = Student ability (kemampuan siswa)
■ = Item difficulty (kesulitan soal)
```

**Interpretasi:**
- Siswa di atas soal = Siswa lebih mampu dari kesulitan soal
- Siswa di bawah soal = Soal lebih sulit dari kemampuan siswa
- Matching = Soal appropriately challenging untuk siswa

#### Tab 3: Person Measures

**Kolom dalam Tabel:**

| Kolom | Deskripsi |
|-------|-----------|
| Rank | Peringkat berdasarkan theta |
| Student | Nama siswa |
| Raw Score | Jumlah soal yang dijawab benar |
| Percentage | Persentase jawaban benar |
| Theta (θ) | Ability measure dalam logit |
| Level | Kategori kemampuan (Very Low - Very High) |
| Percentile | Persentase siswa yang lebih rendah |
| Fit Status | Kualitas respons (well_fitted/underfit/overfit) |

**Kemampuan Level:**
- 🟣 **Very High** (θ > 2.0): Top 5% performers
- 🔵 **High** (0.5 < θ ≤ 2.0): Above average
- 🟢 **Average** (-0.5 ≤ θ ≤ 0.5): Typical performance
- 🟡 **Low** (-2.0 ≤ θ < -0.5): Below average
- 🔴 **Very Low** (θ < -2.0): Needs intervention

**Fit Status Interpretation:**
- ✅ **Well Fitted** (0.8 ≤ MNSQ ≤ 1.2): Respons konsisten
- ⚠️ **Marginal** (0.6 ≤ MNSQ < 0.8 atau 1.2 < MNSQ ≤ 1.4): Perlu review
- ❌ **Poor** (MNSQ < 0.5 atau MNSQ > 1.5): Respons tidak predictable

#### Tab 4: Item Measures

**Kolom dalam Tabel:**

| Kolom | Deskripsi |
|-------|-----------|
| Question | Teks soal (truncated) |
| Delta (δ) | Difficulty measure dalam logit |
| Level | Kategori kesulitan |
| P-Value | % siswa yang menjawab benar |
| Point Biserial | Daya beda soal |
| Bloom Level | Level kognitif |
| Fit Status | Kualitas soal |

**Kesulitan Level:**
- 🔴 **Very Easy** (δ < -2.0): > 90% siswa benar
- 🟡 **Easy** (-2.0 ≤ δ < -0.5): 70-90% siswa benar
- 🟢 **Moderate** (-0.5 ≤ δ ≤ 0.5): 30-70% siswa benar
- 🔵 **Difficult** (0.5 < δ ≤ 2.0): 10-30% siswa benar
- 🟣 **Very Difficult** (δ > 2.0): < 10% siswa benar

**Point Biserial Interpretation:**
- ≥ 0.40: Very good discrimination
- 0.30 - 0.39: Reasonably good
- 0.20 - 0.29: Marginal
- < 0.20: Poor (pertimbangkan remove/revise)

#### Tab 5: Bloom Taxonomy

**Distribution Chart:**
- Doughnut chart menunjukkan distribusi soal per level Bloom
- Ideal: Pyramid (lebih banyak di lower order, lebih sedikit di higher order)

**Cognitive Depth:**
- **Low**: Mayoritas soal level remember/understand
- **Moderate**: Seimbang antara lower dan higher order
- **High**: Mayoritas soal level analyze/evaluate/create

**Rekomendasi:**
- Untuk quiz formatif: Low to Moderate cognitive depth
- Untuk sumatif (UTS/UAS): Moderate to High cognitive depth

---

### 1.4 Tindak Lanjut

#### Berdasarkan Ability Siswa

**Siswa Very Low/Low:**
1. Berikan remedial teaching
2. Review materi dasar
3. Berikan soal level mudah dulu
4. Pertimbangkan tutoring sebaya

**Siswa Average:**
1. Pertahankan konsistensi
2. Berikan challenge soal level analyze
3. Dorong diskusi kelompok

**Siswa High/Very High:**
1. Berikan soal challenge level create
2. Libatkan sebagai tutor sebaya
3. Dorong ikut kompetisi

#### Berdasarkan Item Difficulty

**Soal Very Easy:**
- Pertimbangkan remove atau replace dengan soal lebih menantang
- Good untuk confidence building, tapi tidak discriminating

**Soal Very Difficult:**
- Review apakah soal terlalu kompleks atau ambigu
- Pertimbangkan untuk breakdown jadi beberapa soal lebih mudah

**Soal dengan Poor Fit:**
- MNSQ > 1.5: Soal ambigu, siswa pintar salah, siswa kurang bisa benar
- MNSQ < 0.5: Soal terlalu predictable (mungkin hint terlalu jelas)

#### Berdasarkan Bloom Distribution

**Jika terlalu banyak Remember/Understand:**
- Tambahkan soal level Apply/Analyze
- Kurangi soal hafalan murni

**Jika terlalu banyak Evaluate/Create:**
- Pastikan siswa sudah punya foundation yang cukup
- Berikan scaffolding dengan soal level lebih rendah dulu

---

## 📖 Bagian 2: Untuk Siswa

### 2.1 Mengenal Ability Measure

**Apa itu Ability Measure (θ)?**

Ability measure adalah skor kemampuan kamu yang diukur menggunakan Rasch Model. Berbeda dengan nilai persentase biasa:

- **Theta (θ)**: Kemampuan kamu dalam skala logit
- **Percentile**: Persentase siswa yang lebih rendah dari kamu
- **Level**: Kategori kemampuan (Very Low - Very High)

**Mengapa Theta Berbeda dari Persentase?**

Contoh:
- Quiz A: Kamu dapat 85%, Theta = 0.5 (Average)
- Quiz B: Kamu dapat 70%, Theta = 1.2 (High)

Kenapa bisa begitu? Karena Quiz B lebih sulit! Theta memperhitungkan kesulitan soal.

---

### 2.2 Membaca Ability Dashboard

#### Ability Display

**Theta Score:**
```
Kemampuan Terakhir Kamu
Berdasarkan analisis Rasch dari Mid Term Exam

    1.23
    [High]
    
─────├─────────
-3   0        +3
Very     Average    Very
Low                 High
```

**Interpretasi:**
- Angka besar (1.23): Kemampuan kamu di atas rata-rata
- Marker di kanan 0: Kamu above average
- Label "High": Kategori kemampuan kamu

#### Percentile Rank

```
Percentile Rank di Kelas

    🏆 78.5%

Kamu lebih baik dari 78% siswa di kelas
```

**Interpretasi:**
- 78.5% = Kamu lebih baik dari 78% teman sekelas
- Top 22% performers
- Ini ranking relatif, bukan absolut

#### Ability Meter

```
Ability Meter:
[▓▓▓▓▓▓▓▓░░░░░░░░░░] 
     ↑
   Kamu di sini

Very Low ←────────→ Very High
```

**Warna Meter:**
- 🔴 Merah: Very Low
- 🟡 Kuning: Low
- 🟢 Hijau: Average
- 🔵 Biru: High
- 🟣 Ungu: Very High

---

### 2.3 Fit Statistics

**Apa itu Fit Statistics?**

Fit statistics mengukur seberapa konsisten pattern jawaban kamu:

**Outfit MNSQ:**
- Mengukur respons unexpected (outlier)
- Sensitif terhadap "lucky guess" atau "careless mistake"

**Infit MNSQ:**
- Mengukur pattern respons
- Sensitif terhadap consistency

**Interpretasi:**

| MNSQ Range | Status | Artinya |
|------------|--------|---------|
| 0.8 - 1.2 | ✅ Excellent | Jawaban konsisten dan predictable |
| 0.6 - 0.8 | ⚠️ Good | Agak underfit (mungkin careless) |
| 1.2 - 1.4 | ⚠️ Marginal | Agak overfit (mungkin lucky guess) |
| < 0.5 atau > 1.5 | ❌ Poor | Pattern tidak biasa |

**Contoh:**
- Outfit MNSQ = 1.5: Kamu salah soal mudah tapi benar soal sulit (unpredictable)
- Infit MNSQ = 0.6: Jawaban kamu terlalu predictable (mungkin menghafal pattern)

---

### 2.4 Rekomendasi Belajar

#### Jika Ability Level Kamu: Very Low / Low

```
🎯 Fokus Belajar

Kemampuan kamu masih di bawah rata-rata. 
Jangan khawatir, ini saat yang tepat untuk belajar lebih giat!

✅ Review materi dasar terlebih dahulu
✅ Kerjakan soal-soal level mudah dulu
✅ Minta bantuan guru atau teman jika ada yang tidak paham
✅ Belajar kelompok bisa membantu
```

**Action Plan:**
1. **Identifikasi Weak Areas**: Lihat soal mana yang kamu salah
2. **Start Easy**: Kerjakan soal level remember/understand dulu
3. **Build Foundation**: Pahami konsep dasar sebelum lanjut ke aplikasi
4. **Seek Help**: Jangan malu tanya guru atau teman

#### Jika Ability Level Kamu: Average

```
👍 Bagus! Kamu di Rata-rata

Kemampuan kamu sudah cukup baik. 
Tingkatkan lagi untuk mencapai level berikutnya!

✅ Pertahankan konsistensi belajar
✅ Coba kerjakan soal level analyze & evaluate
✅ Diskusikan materi dengan teman
✅ Buat rangkuman materi
```

**Action Plan:**
1. **Maintain Consistency**: Tetap belajar rutin
2. **Challenge Yourself**: Coba soal lebih sulit
3. **Deepen Understanding**: Jangan hanya hafal, pahami konsep
4. **Teach Others**: Ajari teman, ini akan memperkuat pemahamanmu

#### Jika Ability Level Kamu: High / Very High

```
🌟 Excellent! Kamu Above Average

Kemampuan kamu di atas rata-rata! 
Terus pertahankan dan bantu temanmu juga!

✅ Coba kerjakan soal-soal challenge level create
✅ Bantu teman yang masih kesulitan
✅ Eksplor materi lebih dalam lagi
✅ Ikuti kompetisi atau olimpiade
```

**Action Plan:**
1. **Stay Humble**: Jangan cepat puas
2. **Help Others**: Jadi tutor sebaya
3. **Go Deeper**: Eksplor materi beyond curriculum
4. **Compete**: Ikuti lomba/olimpiade untuk challenge

---

### 2.5 History Tracking

**Tabel Riwayat:**

```
Riwayat Kemampuan

| Quiz           | Tanggal    | Score  | Theta | Level  | Percentile |
|----------------|------------|--------|-------|--------|------------|
| Mid Term       | 21 Mar 2026| 85/100 | 1.23  | High   | 78.5%      |
| Quiz 1         | 14 Mar 2026| 70/100 | 0.15  | Average| 52.3%      |
| Quiz 2         | 07 Mar 2026| 0.45  | Average| 48.1%  |
```

**Cara Membaca Trend:**

**Improving:**
```
Quiz 1: θ = 0.2 (Average)
Quiz 2: θ = 0.8 (High)
Quiz 3: θ = 1.5 (High)

📈 Trend: Increasing! Bagus, terus tingkatkan!
```

**Stable:**
```
Quiz 1: θ = 0.5 (Average)
Quiz 2: θ = 0.4 (Average)
Quiz 3: θ = 0.6 (Average)

➡️ Trend: Stable. Pertahankan, coba tingkatkan!
```

**Declining:**
```
Quiz 1: θ = 1.2 (High)
Quiz 2: θ = 0.5 (Average)
Quiz 3: θ = -0.2 (Average)

📉 Trend: Decreasing. Evaluasi cara belajar!
```

**Tips:**
- Gunakan history untuk track progress
- Jika declining, evaluasi:
  - Apakah materi semakin sulit?
  - Apakah cara belajar perlu diubah?
  - Apakah ada faktor eksternal (sakit, masalah pribadi)?

---

## ❓ FAQ - Pertanyaan Umum

### Untuk Guru

**Q: Berapa minimal siswa untuk Rasch?**
A: Idealnya 30 siswa. Bisa lebih rendah (20) tapi interpretasi harus lebih hati-hati.

**Q: Apakah Rasch wajib untuk semua quiz?**
A: Tidak. Gunakan untuk quiz penting (mid term, final exam). Quiz harian tidak perlu Rasch.

**Q: Berapa lama proses analisis?**
A: Tergantung jumlah siswa dan soal:
- 30 students × 20 questions: ~1-2 menit
- 100 students × 50 questions: ~5-10 menit

**Q: Apakah siswa bisa lihat hasil Rasch?**
A: Tergantung setting `show_rasch_to_students`. Jika TRUE, siswa bisa lihat ability level dan percentile.

**Q: Bagaimana jika item misfit?**
A: Review item tersebut:
- MNSQ > 1.5: Item ambigu, pertimbangkan revisi
- MNSQ < 0.5: Item terlalu predictable, pertimbangkan remove

### Untuk Siswa

**Q: Apakah theta saya akan berubah?**
A: Ya, theta bisa berubah tergantung quiz yang kamu kerjakan. Quiz lebih sulit dengan score sama bisa hasilkan theta lebih tinggi.

**Q: Mengapa percentile saya turun padahal score naik?**
A: Percentile relatif terhadap teman sekelas. Jika teman-temanmu juga improve, percentile kamu bisa turun meskipun score naik.

**Q: Apakah fit statistics mempengaruhi nilai saya?**
A: Tidak langsung. Fit statistics untuk quality control, bukan untuk grading.

**Q: Berapa theta yang bagus?**
A: Tidak ada angka "bagus". Yang penting adalah progress. Jika theta kamu increasing dari waktu ke waktu, itu bagus!

**Q: Apakah saya bisa compare theta dengan kelas lain?**
A: Tidak langsung. Theta hanya comparable dalam analisis yang sama (quiz yang sama).

---

## 📞 Bantuan

Jika ada pertanyaan atau masalah:

1. **Check Documentation**: Lihat dokumentasi lengkap di `laporan/README_RASCH.md`
2. **Ask Teacher**: Guru kamu bisa akses hasil detail dan bisa bantu interpretasi
3. **Technical Support**: Untuk masalah teknis, hubungi IT support

---

**User Guide ini dibuat untuk Aldudu Academy**  
**Version:** 1.0  
**Last Updated:** 2026-03-21
