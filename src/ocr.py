"""OCR nomor ijazah (Tesseract) + post-processing + CER."""
import re
from collections import Counter
import cv2
import pytesseract
from . import config as C
from .preprocessing import ENHANCERS


def prepare_for_ocr(roi_gray, method: str = "clahe+denoise+sharpen", pad: int = 15):
    """Upscale -> enhancement -> padding agar Tesseract lebih stabil."""
    big = cv2.resize(roi_gray, None, fx=C.OCR_SCALE, fy=C.OCR_SCALE,
                     interpolation=cv2.INTER_CUBIC)
    out = ENHANCERS[method](big)
    return cv2.copyMakeBorder(out, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=255)


def run_ocr(img, psm: int = None) -> str:
    cfg = f"--psm {psm or C.OCR_PSM} -c tessedit_char_whitelist={C.OCR_WHITELIST}"
    return pytesseract.image_to_string(img, config=cfg).strip()


_L2D = str.maketrans({"O": "0", "Q": "0", "D": "0", "I": "1", "L": "1",
                      "Z": "2", "S": "5", "B": "8", "G": "6"})
_D2L = str.maketrans({"0": "O", "1": "I", "5": "S", "8": "B", "2": "Z", "6": "G"})


def _snap_prefix(a: str) -> str:
    for k in C.KNOWN_PREFIXES:
        if len(a) == len(k) and sum(x != y for x, y in zip(a, k)) <= 1:
            return k
    return a


def normalize_number(raw: str) -> str:
    """Rapikan hasil OCR menjadi format nomor ijazah.

    Format utama (blangko ijazah SMP/SMA): 'DN-09 DI 0067400'
        = 2 huruf - 2 digit + 2 huruf + 6..8 digit
    Posisi huruf dipaksa huruf & posisi digit dipaksa digit (koreksi O/0, I/1, S/5, B/8).
    Jika pola tidak cocok, fallback ke 'PREFIX-DIGIT' (mis. DN-123456789).
    """
    s = re.sub(r"[^A-Z0-9]", "", raw.upper())
    if not s:
        return ""
    if 12 <= len(s) <= 14:
        a = _snap_prefix(s[0:2].translate(_D2L))
        b = s[2:4].translate(_L2D)
        c = s[4:6].translate(_D2L)
        d = s[6:].translate(_L2D)
        return f"{a}-{b} {c} {d}"
    lo, hi = C.PREFIX_LEN
    m = re.match(rf"^([A-Z]{{{lo},{hi}}})(.*)$", s)
    if not m:
        return s
    prefix, rest = m.groups()
    rest = re.sub(r"\D", "", rest.translate(_L2D))
    return f"{prefix}-{rest}" if rest else prefix


_VALID = re.compile(r"^[A-Z]{2}-\d{2} [A-Z]{2} \d{6,8}$")


def read_number_raw(roi_gray, method: str = "clahe+denoise+sharpen") -> str:
    """OCR multi-kandidat: psm {7,13} x padding {15,45}, lalu voting.

    Kandidat yang cocok pola nomor ijazah diprioritaskan; sisanya dipilih
    berdasar frekuensi. Mengembalikan teks MENTAH pemenang.
    """
    cands = []
    for pad in (15, 45):
        img = prepare_for_ocr(roi_gray, method, pad)
        for psm in (7, 13):
            raw = run_ocr(img, psm)
            if raw:
                cands.append((raw, normalize_number(raw)))
    if not cands:
        return ""
    freq = Counter(n for _, n in cands)
    best = max(cands, key=lambda c: (bool(_VALID.match(c[1])) * 10 + freq[c[1]], len(c[1])))
    return best[0]


def read_number(roi_gray, method: str = "clahe+denoise+sharpen"):
    raw = read_number_raw(roi_gray, method)
    return normalize_number(raw), raw


# ---- Evaluasi ---------------------------------------------------------------
def levenshtein(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def cer(ref: str, hyp: str) -> float:
    """Character Error Rate = (S + D + I) / N."""
    return levenshtein(ref, hyp) / max(len(ref), 1)
