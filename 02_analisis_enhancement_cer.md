# Pertanyaan 2 – Metode Enhancement Mana yang Paling Efektif Berdasarkan CER?

## Jawaban singkat
Pada eksperimen ini, **`clahe+denoise+sharpen`** (CLAHE → Non-Local Means Denoising → Unsharp Masking)
memberi **rata-rata CER terendah (0,164)**, disusul **`clahe`** saja (0,181).
Metode terburuk adalah **`hist_eq`** (0,450) dan **`adaptive`** (0,304).

> Selisih peringkat 1 dan 2 (0,017) kecil, sehingga yang bisa disimpulkan dengan cukup
> yakin adalah *keluarga CLAHE unggul*, bukan bahwa kombinasi tiga tahap pasti lebih baik daripada CLAHE saja.

## Rancangan eksperimen
- **Objek:** area nomor ijazah dari `ijazah_001.jpg`. Referensi: `DN-09 DI 0067400`.
- **Kondisi uji (6):** asli; kontras rendah; noise Gaussian (σ=28); blur (σ=1,6); pencahayaan tidak merata (gradien); kombinasi (kontras turun + blur ringan + noise sedang).
  Kondisi acak (noise, kombinasi) diulang dengan **10 seed**.
- **Metode (9):** `none`, `hist_eq`, `clahe`, `gamma`, `denoise`, `sharpen`, `clahe+denoise+sharpen`, `otsu`, `adaptive`.
- **Kontrol:** semua metode memakai ROI, upscale ×3, mesin OCR, dan skema voting yang sama, sehingga perbedaan CER hanya berasal dari metode enhancement.
- **Metrik:** CER (jarak Levenshtein / panjang referensi), dihitung pada keluaran OCR mentah dengan spasi diabaikan.
  Peringkat memakai rata-rata CER dari 6 kondisi. Skrip: `evaluate_cer.py`.

## Hasil

| Peringkat | Metode | original | low_contrast | noise | blur | uneven_light | combined | **Rata-rata CER** |
|---|---|---|---|---|---|---|---|---|
| 1 | `clahe+denoise+sharpen` | 0.071 | 0.000 | 0.257 | 0.143 | 0.143 | 0.371 | **0.164** |
| 2 | `clahe` | 0.071 | 0.071 | 0.236 | 0.214 | 0.000 | 0.493 | **0.181** |
| 3 | `otsu` | 0.000 | 0.000 | 0.107 | 0.286 | 0.500 | 0.271 | **0.194** |
| 4 | `denoise` | 0.071 | 0.071 | 0.114 | 0.357 | 0.429 | 0.129 | **0.195** |
| 5 | `gamma` | 0.143 | 0.071 | 0.100 | 0.214 | 0.286 | 0.393 | **0.201** |
| 6 | `none` | 0.071 | 0.071 | 0.114 | 0.214 | 0.429 | 0.350 | **0.208** |
| 7 | `sharpen` | 0.143 | 0.143 | 0.179 | 0.214 | 0.286 | 0.336 | **0.217** |
| 8 | `adaptive` | 0.071 | 0.071 | 0.300 | 0.714 | 0.214 | 0.450 | **0.304** |
| 9 | `hist_eq` | 0.500 | 0.071 | 0.493 | 0.500 | 0.500 | 0.636 | **0.450** |

Grafik: `output/cer_chart.png`. Data mentah: `output/cer_results.csv`.

## Analisis

1. **`clahe+denoise+sharpen` paling konsisten.** Ia tidak menjadi yang terburuk pada satu kondisi pun
   dan unggul pada kontras rendah (0,000) dan blur (0,143). Urutannya masuk akal: CLAHE memperbaiki kontras
   lokal, denoising menahan noise yang diperkuat CLAHE, dan sharpening mempertegas tepi huruf yang kabur.
2. **CLAHE saja unggul pada pencahayaan tidak merata** (CER 0,000), karena kerjanya per petak lokal.
   Namun CLAHE **memperkuat noise**: pada kondisi `noise` CER-nya (0,236) jauh lebih buruk daripada `none` (0,114) atau `gamma` (0,100).
3. **Pada noise tinggi, enhancement yang lebih sederhana lebih baik.** `gamma`, `otsu`, `denoise`, dan `none`
   lebih rendah CER-nya pada kondisi noise. Pada kondisi `combined`, `denoise` terbaik (0,129).
   Jadi tidak ada satu metode yang menang di semua kondisi.
4. **`hist_eq` terburuk.** Pemerataan histogram *global* meregangkan kontras seluruh ROI, termasuk
   pita dan ornamen di sekitar teks, sehingga latar menjadi kasar dan Tesseract salah membaca
   (CER 0,500 bahkan pada citra asli).
5. **`adaptive` threshold rapuh terhadap blur** (CER 0,714): binarisasi lokal memutus goresan tipis.
   `otsu` baik saat pencahayaan rata, tetapi gagal saat pencahayaan tidak merata (0,500), karena satu ambang global tidak cocok untuk seluruh area.
6. **Keterkaitan dengan prototype.** Enhancement area nomor di `src/preprocessing.py` (`NUMBER_ENHANCE`) memakai
   `clahe+denoise+sharpen` sesuai temuan ini.

## Keterbatasan (harap dicantumkan dalam laporan)
- **Hanya satu ijazah** dan **degradasi buatan**, bukan foto/scan nyata beragam. Hasil bersifat indikatif, bukan bukti umum.
- **Referensi pendek** (14 karakter tanpa spasi): satu kesalahan karakter = CER 0,071, sehingga nilai bergerak dalam "anak tangga" besar. Selisih < ~0,03 antar metode sebaiknya dianggap setara.
- Tesseract sangat sensitif terhadap batas crop dan mode segmentasi; ROI yang lebih longgar atau ketat dapat mengubah hasil. Skema voting dipakai untuk meredam hal ini, tetapi tidak menghilangkannya.
- Pada kondisi `original`, CER 0,071 pada sebagian besar metode setara dengan satu karakter salah dari 14; jenis kesalahannya belum dianalisis per karakter.

## Cara memperkuat analisis
Kumpulkan 30+ citra ijazah (atau foto/scan dengan kualitas berbeda), isi `data/ground_truth.csv`,
lalu jalankan `python evaluate_cer.py --no-degrade`. Dengan dataset nyata, laporkan rata-rata dan simpangan baku CER
per metode, dan uji apakah selisih antar metode bermakna.
