"""Konfigurasi ROI dan parameter. Sesuaikan ROI dengan layout ijazah Anda.

ROI dinyatakan sebagai pecahan (x, y, w, h) terhadap lebar/tinggi citra,
sehingga tidak bergantung pada resolusi citra.
"""

# Area nomor ijazah (biasanya di bagian atas / bawah dokumen)
ROI_NOMOR = (0.365, 0.911, 0.265, 0.029)   # baris teks nomor di kotak bawah (tanpa ornamen)

# Area tanda tangan kepala sekolah (biasanya kanan bawah)
ROI_TTD = (0.527, 0.712, 0.110, 0.054)     # coretan tanda tangan (di atas nama cetak kepala sekolah)

# Pola nomor ijazah: prefix huruf + digit, contoh DN-123456789
PREFIX_LEN = (1, 3)
DIGIT_LEN = (6, 12)

# Parameter OCR
OCR_SCALE = 3                       # upscale ROI sebelum OCR
OCR_WHITELIST = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789- "
OCR_PSM = 7                         # 7 = satu baris teks

# Parameter deteksi tanda tangan
TTD_MIN_INK_RATIO = 0.010           # minimal rasio piksel tinta pada ROI
TTD_MIN_COMPONENT_AREA = 150        # minimal luas komponen (px)
TTD_MIN_COMPONENTS = 1
TTD_MIN_EXTENT = 0.20               # bounding box goresan thd ROI (rasio)

# Prefix resmi blangko ijazah. Hasil OCR yang berbeda <=1 karakter akan dikoreksi.
# Kosongkan tuple ini ( () ) jika tidak ingin koreksi domain.
KNOWN_PREFIXES = ("DN",)
