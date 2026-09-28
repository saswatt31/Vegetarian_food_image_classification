"""
Extract the Indian Food Images dataset from the downloaded HuggingFace
parquet shards into per-class folders, and run the mandatory realness
validation BEFORE any training:

  * decode every image, verify it opens with PIL
  * flag corrupted files (unreadable) and suspicious flat images
    (very low pixel variance => drawing/icon/placeholder territory)
  * print dataset statistics: totals, classes, per-class counts, sizes
  * build a labeled sample grid for visual verification (results/dataset_samples_grid.png)

Usage:
    python src/prepare_data.py --extract   # parquet -> raw/images/<class>/*.jpg
    python src/prepare_data.py --validate  # stats + grid + corruption scan
"""
import argparse
import io
import json
import os
import sys
from collections import Counter

import numpy as np
from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "raw")
IMG_DIR = os.path.join(RAW, "images")
RESULTS = os.path.join(BASE, "results")

CLASS_NAMES = [
    "burger", "butter_naan", "chai", "chapati", "chole_bhature",
    "dal_makhani", "dhokla", "fried_rice", "idli", "jalebi",
    "kaathi_rolls", "kadai_paneer", "kulfi", "masala_dosa", "momos",
    "paani_puri", "pakode", "pav_bhaji", "pizza", "samosa",
]

SHARDS = {
    "train": os.path.join(RAW, "train.parquet"),
    "test": os.path.join(RAW, "test.parquet"),
}


def extract():
    import pyarrow.parquet as pq
    os.makedirs(IMG_DIR, exist_ok=True)
    total = 0
    for split, path in SHARDS.items():
        pf = pq.ParquetFile(path)
        n = 0
        for batch in pf.iter_batches(batch_size=64, columns=["image", "label"]):
            imgs = batch.column("image").to_pylist()
            labels = batch.column("label").to_pylist()
            for rec, lab in zip(imgs, labels):
                cls = CLASS_NAMES[lab]
                d = os.path.join(IMG_DIR, cls)
                os.makedirs(d, exist_ok=True)
                raw_bytes = rec["bytes"] if isinstance(rec, dict) else rec
                fname = f"{split}_{n:05d}.jpg"
                with open(os.path.join(d, fname), "wb") as f:
                    f.write(raw_bytes)
                n += 1
                total += 1
        print(f"{split}: extracted {n} images")
    print(f"TOTAL extracted: {total} images across {len(set(os.listdir(IMG_DIR)))} classes")


def image_files():
    for cls in sorted(os.listdir(IMG_DIR)):
        d = os.path.join(IMG_DIR, cls)
        if os.path.isdir(d):
            for fn in sorted(os.listdir(d)):
                yield cls, os.path.join(d, fn)


def validate(make_grid=True):
    os.makedirs(RESULTS, exist_ok=True)
    per_class = Counter()
    corrupted, flat = [], []
    sizes = []
    total_bytes = 0
    samples = {}

    for cls, path in image_files():
        per_class[cls] += 1
        total_bytes += os.path.getsize(path)
        try:
            with Image.open(path) as im:
                im.load()
                sizes.append(im.size)
                arr = np.asarray(im.convert("L"), dtype=np.float32)
                if arr.std() < 6.0:  # near-uniform => drawing/placeholder
                    flat.append(path)
                if cls not in samples and im.size[0] >= 200:
                    samples[cls] = path
        except Exception as e:
            corrupted.append((path, str(e)[:60]))

    n_img = sum(per_class.values())
    print("=" * 70)
    print("DATASET VALIDATION — Indian Food Images (real photographs)")
    print("=" * 70)
    print(f"total images        : {n_img}")
    print(f"total classes       : {len(per_class)}")
    print(f"dataset size        : {total_bytes / 1e6:.1f} MB")
    if sizes:
        ws = [w for w, h in sizes]
        hs = [h for w, h in sizes]
        print(f"image dims (min/med/max): {min(ws)}/{int(np.median(ws))}/{max(ws)} px wide")
    print(f"corrupted images    : {len(corrupted)}")
    print(f"suspicious flat imgs: {len(flat)}")
    print()
    print("images per class:")
    for cls in sorted(per_class):
        print(f"  {cls:18s} {per_class[cls]:4d}")
    assert set(per_class) == set(CLASS_NAMES), "unexpected class set!"

    if make_grid:
        # 4 x 5 grid, one real photo per class
        from PIL import ImageDraw, ImageFont
        tile = 260
        grid = Image.new("RGB", (tile * 5, tile * 4 + 40 * 4), (250, 250, 247))
        d = ImageDraw.Draw(grid)
        try:
            font = ImageFont.truetype("C:\\Windows\\Fonts\\segoeuib.ttf", 20)
        except OSError:
            font = ImageFont.load_default()
        for i, cls in enumerate(CLASS_NAMES):
            p = samples.get(cls)
            x, y = (i % 5) * tile, (i // 5) * (tile + 40)
            if p:
                with Image.open(p) as im:
                    im = im.convert("RGB")
                    # center-crop to square tile
                    w, h = im.size
                    s = min(w, h)
                    im = im.crop(((w - s) // 2, (h - s) // 2,
                                  (w + s) // 2, (h + s) // 2)).resize((tile, tile))
                grid.paste(im, (x, y))
            d.rectangle([x, y + tile, x + tile, y + tile + 40], fill=(30, 42, 68))
            d.text((x + 10, y + tile + 8), cls, fill=(255, 255, 255), font=font)
        out = os.path.join(RESULTS, "dataset_samples_grid.png")
        grid.save(out)
        print(f"\nsample grid saved -> {out}")
        print(">>> VISUALLY VERIFY: every tile must be a real food photograph.")

    # persist the scan results for the report
    stats = {
        "total_images": n_img,
        "classes": sorted(per_class),
        "per_class": {c: per_class[c] for c in sorted(per_class)},
        "total_mb": round(total_bytes / 1e6, 1),
        "corrupted": corrupted,
        "suspicious_flat": flat,
    }
    with open(os.path.join(RAW, "dataset_stats.json"), "w") as f:
        json.dump(stats, f, indent=1)
    print(f"stats saved -> raw/dataset_stats.json")

    if corrupted or flat:
        print("\nACTION NEEDED: remove flagged files and re-run before training.")
        for p, why in corrupted[:10]:
            print("  corrupt:", p, why)
        for p in flat[:10]:
            print("  flat   :", p)
    else:
        print("\nOK: no corrupted or suspicious images found.")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--extract", action="store_true")
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--no-grid", action="store_true")
    args = ap.parse_args()
    if args.extract:
        extract()
    if args.validate or not args.extract:
        validate(make_grid=not args.no_grid)
