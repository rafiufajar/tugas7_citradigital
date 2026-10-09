# Ijazah Verifier – Mini Project Pengolahan Citra

Prototype yang menerima **citra ijazah** dan menghasilkan:

```
Input : ijazah_001.jpg
Output:
Nomor Ijazah : DN-09 DI 0067400
Tanda Tangan : PRESENT
```

1. **Nomor ijazah** dibaca dengan OCR (Tesseract).
2. **Tanda tangan kepala sekolah** dideteksi ada/tidaknya (thresholding + morfologi).

## Pipeline

```
Citra Ijazah
     ↓
Grayscale
     ↓
Image Enhancement (CLAHE)
     ↓
┌──────────────────────────┬─────────────────────────────┐
Area Nomor (ROI)           Area Tanda Tangan (ROI)
     ↓                          ↓
Enhancement                Thresholding (Otsu)
(CLAHE+Denoise+Sharpen)         ↓
     ↓                     Morphology (opening/closing)
OCR (Tesseract)                 ↓
     ↓                     Signature Detection
Nomor Ijazah               (PRESENT / ABSENT)
└──────────────────────────┴─────────────────────────────┘
                    ↓
            Hasil Verifikasi
```


## Cara Menjalankan

### 1. Prasyarat
- Python 3.9+
- **Tesseract OCR** terpasang di sistem (bukan hanya paket Python):

| OS | Perintah |
|---|---|
| Ubuntu/Debian | `sudo apt install tesseract-ocr` |
| macOS | `brew install tesseract` |
| Windows | Unduh installer dari https://github.com/UB-Mannheim/tesseract/wiki, lalu tambahkan folder instalasi ke `PATH` (atau set `pytesseract.pytesseract.tesseract_cmd` di `src/ocr.py`) |

Cek: `tesseract --version`

### 2. Instalasi
```bash
git clone <URL-REPO-ANDA>
cd ijazah-verifier
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Menjalankan prototype
```bash
# satu citra
python main.py data/images/ijazah_001.jpg

# seluruh citra dalam folder
python main.py data/images

# simpan citra tiap tahap (grayscale, enhancement, ROI, hasil morfologi) ke output/debug
python main.py data/images/ijazah_001.jpg --debug

# keluaran JSON (termasuk metrik deteksi tanda tangan)
python main.py data/images/ijazah_001.jpg --json
```

Contoh keluaran:
```
Input: ijazah_001.jpg
Nomor Ijazah : DN-09 DI 0067400
Tanda Tangan : PRESENT
```

### 4. Eksperimen CER (Pertanyaan 2)
```bash
python evaluate_cer.py --seeds 10
```
Menghasilkan `output/cer_table.md`, `output/cer_results.csv`, dan `output/cer_chart.png`.
Untuk memakai dataset sendiri: taruh citra di `data/images/`, isi `data/ground_truth.csv`
(`filename,nomor_ijazah`), lalu jalankan. Tambahkan `--no-degrade` jika citra Anda
sudah beragam kualitasnya dan tidak perlu degradasi buatan.

## Menyesuaikan dengan Ijazah Lain (PENTING)

Area nomor dan tanda tangan ditentukan oleh **ROI berbasis rasio** di `src/config.py`:

```python
ROI_NOMOR = (x, y, lebar, tinggi)   # pecahan 0–1 dari ukuran citra
ROI_TTD   = (x, y, lebar, tinggi)
```

Jalankan dengan `--debug`, buka `output/debug/*_1_roi.jpg` (kotak biru = nomor,
hijau = tanda tangan) dan geser nilainya sampai kotak pas. ROI nomor sebaiknya hanya
memuat baris teks, tanpa ornamen/garis pinggir, karena Tesseract sensitif terhadap hal ini.
Format nomor (`DN-09 DI 0067400`) diatur di `normalize_number()` dalam `src/ocr.py`.

## Keterbatasan

- ROI tetap: berlaku untuk blangko ijazah dengan tata letak serupa dan citra yang sudah lurus (tidak miring/perspektif).
- Deteksi tanda tangan hanya menentukan **ada/tidaknya coretan tinta** di area tanda tangan; **bukan** memverifikasi keaslian atau kecocokan tanda tangan.
- Evaluasi CER memakai satu ijazah dengan degradasi buatan, sehingga bersifat indikatif (lihat `docs/02_analisis_enhancement_cer.md`).
