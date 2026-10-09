"""CLI: python main.py ijazah_001.jpg [--debug]"""
import argparse
import glob
import json
import os
import sys
from src.pipeline import verify


def main():
    ap = argparse.ArgumentParser(description="Verifikasi ijazah: OCR nomor + deteksi tanda tangan")
    ap.add_argument("input", help="file citra atau folder berisi citra")
    ap.add_argument("--debug", action="store_true", help="simpan citra tahap antara ke output/debug")
    ap.add_argument("--json", action="store_true", help="keluaran JSON")
    a = ap.parse_args()

    if os.path.isdir(a.input):
        files = sorted(sum((glob.glob(os.path.join(a.input, e))
                            for e in ("*.jpg", "*.jpeg", "*.png")), []))
    else:
        files = [a.input]
    if not files:
        sys.exit("Tidak ada citra ditemukan.")

    for f in files:
        r = verify(f, debug_dir="output/debug" if a.debug else None)
        if a.json:
            print(json.dumps(r, ensure_ascii=False))
        else:
            print(f"Input: {r['file']}")
            print(f"Nomor Ijazah : {r['nomor_ijazah']}")
            print(f"Tanda Tangan : {r['tanda_tangan']}")
            print()


if __name__ == "__main__":
    main()
