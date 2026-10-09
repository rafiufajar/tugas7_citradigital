"""Pipeline: citra -> grayscale -> enhancement -> (OCR | signature) -> hasil."""
import os
import cv2
from . import config as C
from .preprocessing import to_gray, ENHANCERS, GLOBAL_ENHANCE, NUMBER_ENHANCE
from .roi import crop_ratio
from .ocr import read_number, prepare_for_ocr
from .signature import detect_signature


def verify(image_path: str, debug_dir: str = None) -> dict:
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Tidak dapat membaca citra: {image_path}")

    gray = to_gray(img)                                   # 1. Grayscale
    enhanced = ENHANCERS[GLOBAL_ENHANCE](gray)            # 2. Image enhancement

    # --- Cabang A: nomor ijazah
    roi_no, box_no = crop_ratio(enhanced, C.ROI_NOMOR)    # area nomor
    nomor, raw = read_number(roi_no, NUMBER_ENHANCE)      # enhancement + OCR

    # --- Cabang B: tanda tangan
    roi_ttd, box_ttd = crop_ratio(enhanced, C.ROI_TTD)    # area tanda tangan
    status, info, bw = detect_signature(roi_ttd, return_debug=True)  # thr + morph + deteksi

    result = {"file": os.path.basename(image_path), "nomor_ijazah": nomor,
              "nomor_raw": raw, "tanda_tangan": status, "ttd_info": info}

    if debug_dir:
        os.makedirs(debug_dir, exist_ok=True)
        stem = os.path.splitext(os.path.basename(image_path))[0]
        vis = img.copy()
        cv2.rectangle(vis, box_no[:2], box_no[2:], (255, 0, 0), 3)
        cv2.rectangle(vis, box_ttd[:2], box_ttd[2:], (0, 160, 0), 3)
        cv2.imwrite(f"{debug_dir}/{stem}_1_roi.jpg", vis)
        cv2.imwrite(f"{debug_dir}/{stem}_2_gray.jpg", gray)
        cv2.imwrite(f"{debug_dir}/{stem}_3_enhanced.jpg", enhanced)
        cv2.imwrite(f"{debug_dir}/{stem}_4_nomor_ocr_input.jpg", prepare_for_ocr(roi_no, NUMBER_ENHANCE))
        cv2.imwrite(f"{debug_dir}/{stem}_5_ttd_morph.jpg", bw)
    return result
