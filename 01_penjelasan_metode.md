# Pertanyaan 1 – Penjelasan Metode yang Digunakan

Sistem memproses citra ijazah melalui satu **tahap bersama** (grayscale dan enhancement global),
lalu bercabang menjadi dua: **cabang OCR nomor ijazah** dan **cabang deteksi tanda tangan**.
Hasil kedua cabang digabung menjadi hasil verifikasi.

## 1. Grayscale
Citra RGB (3 kanal) diubah menjadi satu kanal intensitas:

`Gray = 0.299·R + 0.587·G + 0.114·B` (`cv2.cvtColor`, `COLOR_BGR2GRAY`)

**Alasan:** OCR dan thresholding hanya membutuhkan informasi terang–gelap. Warna (ornamen
biru, pita oranye) justru menambah variasi yang tidak berguna, dan komputasi menjadi lebih ringan.

## 2. Image Enhancement (global): CLAHE
*Contrast Limited Adaptive Histogram Equalization* (`clipLimit=2.5`, `tileGridSize=8×8`).
Citra dibagi menjadi petak kecil, histogram tiap petak diratakan, dengan batas penguatan (clip)
agar noise tidak meledak. Cocok untuk hasil scan/foto dengan pencahayaan tidak merata.

## 3. Cabang A – Nomor Ijazah

| Tahap | Metode | Penjelasan |
|---|---|---|
| Area Nomor | **Cropping ROI berbasis rasio** | Area nomor dipotong memakai koordinat relatif (`ROI_NOMOR`), sehingga tidak bergantung resolusi. ROI hanya memuat baris teks. |
| Enhancement | **Upscale ×3 (bicubic) → CLAHE → Non-Local Means Denoising → Unsharp Masking** | Upscale membuat tinggi huruf mendekati ukuran ideal Tesseract; CLAHE menaikkan kontras; NLM menekan noise sambil menjaga tepi; unsharp masking (`1.8·I − 0.8·Gaussian(I)`) mempertegas tepi huruf. |
| OCR | **Tesseract** (LSTM), `whitelist = A–Z 0–9 - spasi` | Pembatasan karakter mencegah keluaran liar. Dijalankan pada beberapa kandidat (psm 7 dan 13 × dua ukuran padding) lalu **voting**; kandidat yang sesuai pola nomor diprioritaskan. |
| Normalisasi | **Aturan berbasis posisi + regex** | Format `HH-DD HH DDDDDDD`: posisi huruf dipaksa huruf, posisi digit dipaksa digit (koreksi O↔0, I↔1, S↔5, B↔8). Prefix yang meleset ≤1 karakter dari `DN` dikoreksi (dapat dimatikan di `config.py`). |

Ukuran kesalahan OCR: **CER (Character Error Rate)**

`CER = (S + D + I) / N`

dengan S = substitusi, D = penghapusan, I = penyisipan (jarak Levenshtein), N = jumlah karakter referensi.
CER 0 berarti sempurna; makin kecil makin baik.

## 4. Cabang B – Tanda Tangan

| Tahap | Metode | Penjelasan |
|---|---|---|
| Area Tanda Tangan | **Cropping ROI berbasis rasio** | `ROI_TTD` dipasang pada area coretan, di atas nama cetak kepala sekolah. |
| Thresholding | **Gaussian blur 5×5 + Otsu (inverse)** | Otsu mencari ambang optimal secara otomatis dari histogram; mode *inverse* membuat tinta menjadi piksel putih (foreground). Jika kontras ROI sangat rendah (ROI kosong), masker dikosongkan agar noise tidak dibaca sebagai tinta. |
| Morphology | **(a)** Opening horizontal panjang → dikurangkan; **(b)** Opening elips 2×2; **(c)** Closing elips 7×7 | (a) membuang garis lurus horizontal (garis titik-titik, garis bawah); (b) membuang bintik noise; (c) menyambung goresan yang putus sehingga satu tanda tangan menjadi satu komponen. |
| Signature Detection | **Connected Component Analysis + aturan keputusan** | Dihitung: rasio tinta, jumlah komponen (luas ≥ 150 px), dan *extent* (lebar & tinggi gabungan komponen terhadap ROI). **PRESENT** jika ketiganya memenuhi ambang di `config.py`; selain itu **ABSENT**. |

## 5. Hasil Verifikasi
Keluaran akhir berupa dua baris: `Nomor Ijazah` dan `Tanda Tangan`.

## 6. Hasil Pengujian pada Prototype

| Citra uji | Nomor Ijazah | Tanda Tangan | Keterangan |
|---|---|---|---|
| `ijazah_001.jpg` (ijazah asli) | `DN-09 DI 0067400` ✔ | PRESENT ✔ | |
| `ijazah_002_tanpa_ttd.jpg` | `DN-09 DI 0067400` ✔ | ABSENT ✔ | tanda tangan dihapus (diputihkan) secara digital |
| `ijazah_003_degradasi.jpg` | `DN-09 DI 0067400` ✔ | PRESENT ✔ | kontras diturunkan + blur + noise |

**Catatan keterbatasan:** pengujian ini memakai satu ijazah dan dua turunannya, jadi belum
cukup untuk mengklaim akurasi umum. Deteksi tanda tangan memeriksa keberadaan tinta,
bukan keaslian tanda tangan. Teks cetak atau stempel yang masuk ke ROI dapat menyebabkan
PRESENT palsu, sehingga ROI harus dipasang rapat pada area coretan.
