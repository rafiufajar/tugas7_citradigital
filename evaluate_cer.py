"""Eksperimen CER: bandingkan metode enhancement untuk OCR nomor ijazah.

Pemakaian:
    python evaluate_cer.py                       # pakai data/ground_truth.csv
    python evaluate_cer.py --seeds 10            # jumlah ulangan degradasi acak
    python evaluate_cer.py --no-degrade          # hanya citra asli (dataset sendiri)

Setiap citra di ground_truth.csv diuji pada beberapa kondisi (asli + degradasi
terkontrol). Untuk tiap metode enhancement dihitung rata-rata CER.
CER dihitung pada keluaran OCR MENTAH (sebelum normalisasi) dengan spasi dibuang,
agar yang terukur murni pengaruh enhancement, bukan post-processing.
"""
import argparse
import csv
import os
import cv2
import numpy as np
from src import config as C
from src.preprocessing import to_gray, ENHANCERS
from src.roi import crop_ratio
from src.ocr import read_number_raw, cer


# ---- Degradasi terkontrol (simulasi kondisi scan/foto yang buruk) ------------
def d_original(g, rng):      return g
def d_low_contrast(g, rng):  return (g.astype(np.float32) * 0.45 + 110).clip(0, 255).astype(np.uint8)
def d_noise(g, rng):         return (g + rng.normal(0, 28, g.shape)).clip(0, 255).astype(np.uint8)
def d_blur(g, rng):          return cv2.GaussianBlur(g, (0, 0), 1.6)
def d_uneven(g, rng):
    h, w = g.shape
    grad = np.tile(np.linspace(0.45, 1.0, w, dtype=np.float32), (h, 1))
    return (g.astype(np.float32) * grad).clip(0, 255).astype(np.uint8)
def d_combined(g, rng):
    """Kontras turun + blur ringan + noise sedang (kombinasi realistis, tidak ekstrem)."""
    x = (g.astype(np.float32) * 0.6 + 80)
    x = cv2.GaussianBlur(x, (0, 0), 1.0) + rng.normal(0, 12, g.shape)
    return x.clip(0, 255).astype(np.uint8)

CONDITIONS = {"original": d_original, "low_contrast": d_low_contrast, "noise": d_noise,
              "blur": d_blur, "uneven_light": d_uneven, "combined": d_combined}
RANDOM_CONDS = {"noise", "combined"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gt", default="data/ground_truth.csv")
    ap.add_argument("--images", default="data/images")
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--no-degrade", action="store_true")
    ap.add_argument("--out", default="output")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    gt = list(csv.DictReader(open(a.gt, encoding="utf-8")))
    conds = {"original": d_original} if a.no_degrade else CONDITIONS
    methods = list(ENHANCERS)
    res = {m: {c: [] for c in conds} for m in methods}

    for row in gt:
        img = cv2.imread(os.path.join(a.images, row["filename"]))
        ref = row["nomor_ijazah"].replace(" ", "")
        roi, _ = crop_ratio(to_gray(img), C.ROI_NOMOR)
        for cname, fn in conds.items():
            reps = a.seeds if cname in RANDOM_CONDS else 1
            for s in range(reps):
                deg = fn(roi, np.random.default_rng(s))
                for m in methods:
                    hyp = read_number_raw(deg, m).replace(" ", "")
                    res[m][cname].append(cer(ref, hyp))

    # ---- tabel ----
    cnames = list(conds)
    mean = {m: {c: float(np.mean(res[m][c])) for c in cnames} for m in methods}
    overall = {m: float(np.mean([mean[m][c] for c in cnames])) for m in methods}
    ranking = sorted(methods, key=lambda m: overall[m])

    with open(f"{a.out}/cer_results.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["method"] + cnames + ["rata_rata"])
        for m in ranking:
            w.writerow([m] + [f"{mean[m][c]:.4f}" for c in cnames] + [f"{overall[m]:.4f}"])

    lines = ["| Peringkat | Metode | " + " | ".join(cnames) + " | **Rata-rata CER** |",
             "|---|---|" + "---|" * (len(cnames) + 1)]
    for i, m in enumerate(ranking, 1):
        lines.append(f"| {i} | `{m}` | " + " | ".join(f"{mean[m][c]:.3f}" for c in cnames)
                     + f" | **{overall[m]:.3f}** |")
    md = "\n".join(lines)
    open(f"{a.out}/cer_table.md", "w", encoding="utf-8").write(md + "\n")
    print(md)
    print(f"\nTerbaik: {ranking[0]} (CER rata-rata {overall[ranking[0]]:.3f})")

    # ---- grafik ----
    try:
        import matplotlib; matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(9, 4.5))
        ax.barh(ranking[::-1], [overall[m] for m in ranking[::-1]], color="#2b6cb0")
        ax.set_xlabel("Rata-rata CER (lebih kecil lebih baik)")
        ax.set_title("Perbandingan metode enhancement berdasarkan CER")
        plt.tight_layout(); plt.savefig(f"{a.out}/cer_chart.png", dpi=150)
    except ImportError:
        pass


if __name__ == "__main__":
    main()
