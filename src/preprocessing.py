"""Grayscale + berbagai metode image enhancement."""
import cv2
import numpy as np


def to_gray(img: np.ndarray) -> np.ndarray:
    if img.ndim == 2:
        return img
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


# ---- Metode enhancement (input & output: grayscale uint8) -------------------
def enh_none(g):
    return g


def enh_hist_eq(g):
    return cv2.equalizeHist(g)


def enh_clahe(g):
    return cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8)).apply(g)


def enh_gamma(g, gamma=0.7):
    table = ((np.arange(256) / 255.0) ** gamma * 255).astype("uint8")
    return cv2.LUT(g, table)


def enh_denoise(g):
    return cv2.fastNlMeansDenoising(g, None, h=10, templateWindowSize=7, searchWindowSize=21)


def enh_sharpen(g):
    blur = cv2.GaussianBlur(g, (0, 0), 2.0)
    return cv2.addWeighted(g, 1.8, blur, -0.8, 0)  # unsharp masking


def enh_clahe_denoise_sharpen(g):
    return enh_sharpen(enh_denoise(enh_clahe(g)))


def enh_otsu(g):
    return cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]


def enh_adaptive(g):
    return cv2.adaptiveThreshold(g, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                 cv2.THRESH_BINARY, 31, 15)


ENHANCERS = {
    "none": enh_none,
    "hist_eq": enh_hist_eq,
    "clahe": enh_clahe,
    "gamma": enh_gamma,
    "denoise": enh_denoise,
    "sharpen": enh_sharpen,
    "clahe+denoise+sharpen": enh_clahe_denoise_sharpen,
    "otsu": enh_otsu,
    "adaptive": enh_adaptive,
}

# Enhancement umum untuk seluruh citra (tahap "Image Enhancement" di pipeline)
GLOBAL_ENHANCE = "clahe"
# Enhancement khusus area nomor (cabang OCR). Ubah sesuai hasil evaluate_cer.py
NUMBER_ENHANCE = "clahe+denoise+sharpen"
