import numpy as np


def crop_ratio(img: np.ndarray, roi):
    h, w = img.shape[:2]
    x, y, rw, rh = roi
    x0, y0 = int(x * w), int(y * h)
    x1, y1 = int((x + rw) * w), int((y + rh) * h)
    return img[y0:y1, x0:x1], (x0, y0, x1, y1)
