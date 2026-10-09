"""Deteksi tanda tangan: thresholding -> morphology -> analisis komponen."""
import cv2
import numpy as np
from . import config as C


def detect_signature(roi_gray, return_debug=False):
    g = cv2.GaussianBlur(roi_gray, (5, 5), 0)

    # 1. Thresholding: tinta (gelap) -> putih. Otsu inverse.
    _, bw = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    # ROI kosong: Otsu akan memecah noise, jadi pastikan kontras cukup
    if int(g.max()) - int(g.min()) < 40:
        bw = np.zeros_like(bw)

    # 2. Morphology
    h, w = bw.shape
    #   a) buang garis horizontal panjang (garis bawah/kop) via opening horizontal
    hk = cv2.getStructuringElement(cv2.MORPH_RECT, (max(w // 3, 15), 1))
    bw = cv2.subtract(bw, cv2.morphologyEx(bw, cv2.MORPH_OPEN, hk))
    #   b) opening kecil: buang bintik noise
    bw = cv2.morphologyEx(bw, cv2.MORPH_OPEN,
                          cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2)))
    #   c) closing: sambungkan goresan yang putus
    bw = cv2.morphologyEx(bw, cv2.MORPH_CLOSE,
                          cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))

    # 3. Analisis komponen terhubung
    _, _, stats, _ = cv2.connectedComponentsWithStats(bw, connectivity=8)
    comps = [s for s in stats[1:] if s[cv2.CC_STAT_AREA] >= C.TTD_MIN_COMPONENT_AREA]
    ink_ratio = float(np.count_nonzero(bw)) / bw.size
    largest = max((s[cv2.CC_STAT_AREA] for s in comps), default=0)

    if comps:
        x0 = min(s[cv2.CC_STAT_LEFT] for s in comps)
        y0 = min(s[cv2.CC_STAT_TOP] for s in comps)
        x1 = max(s[cv2.CC_STAT_LEFT] + s[cv2.CC_STAT_WIDTH] for s in comps)
        y1 = max(s[cv2.CC_STAT_TOP] + s[cv2.CC_STAT_HEIGHT] for s in comps)
        extent = ((x1 - x0) / w + (y1 - y0) / h) / 2
    else:
        extent = 0.0

    present = (ink_ratio >= C.TTD_MIN_INK_RATIO
               and len(comps) >= C.TTD_MIN_COMPONENTS
               and extent >= C.TTD_MIN_EXTENT)
    info = {"ink_ratio": round(ink_ratio, 4), "components": len(comps),
            "largest_area": int(largest), "extent": round(extent, 3)}
    status = "PRESENT" if present else "ABSENT"
    return (status, info, bw) if return_debug else (status, info)
