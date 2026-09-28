"""
Build the small vegetarian subset from the extracted real-photo corpus.

Selected classes (all verified present in the Indian Food Images dataset):

  dhokla       289 imgs   — steamed gram-flour cakes (veg)
  idli         309 imgs   — steamed rice cakes (veg)
  masala_dosa  311 imgs   — fermented rice crepe, potato filling (veg)
  pakode       278 imgs   — vegetable fritters (veg)
  pav_bhaji    353 imgs   — mashed vegetable curry + bread roll (veg)
  kadai_paneer 412 imgs   — paneer (Indian cottage cheese) in gravy (veg)
  samosa       262 imgs   — spiced potato pastry (veg)
  chapati      413 imgs   — whole-wheat flatbread (veg; vegan)

Vegetarian assumptions (documented per instructions):
  * All eight classes are lacto-vegetarian preparations as commonly sold.
  * kadai_paneer: paneer is dairy; commercial gravies are tomato-onion based.
    We assume the dataset images contain paneer dishes without meat.
  * pav_bhaji: bhaji is a vegetable mash; butter (dairy) is standard.
  * masala_dosa: potato-onion filling; no egg in the batter as per the
    dish's standard preparation.
  * No class among the 20 contains meat by definition; we additionally
    avoided ambiguous classes (kaathi_rolls can contain chicken/egg).

Deduplication:
  * exact duplicates via SHA-256 of file bytes
  * near-duplicates across different images via 8x8 aHash with
    Hamming distance <= 2 (kept first, later twins dropped)

Split: stratified 70 / 15 / 15 per class (seeded shuffle).
Output: data/train|validation|test/<class>/*.jpg + data/split_summary.json
"""
import argparse
import hashlib
import json
import os
import random
import shutil
from collections import Counter

import numpy as np
from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(BASE, "raw", "images")
OUT = os.path.join(BASE, "data")

SELECTED = {
    "dhokla": "Breakfast/Snack",
    "idli": "Breakfast",
    "masala_dosa": "Breakfast",
    "pakode": "Snack",
    "pav_bhaji": "Main Meal",
    "kadai_paneer": "Main Meal",
    "samosa": "Snack",
    "chapati": "Main Meal",
}
SPLIT = (0.70, 0.15, 0.15)
SEED = 42


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def ahash(path, size=8):
    with Image.open(path) as im:
        im = im.convert("L").resize((size, size))
        a = np.asarray(im, dtype=np.float32)
    return a > a.mean()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cap", type=int, default=250, help="max images per class")
    args = ap.parse_args()
    rng = random.Random(SEED)

    report = {"classes": {}, "duplicates_removed": 0, "near_duplicates_removed": 0}
    grand = Counter()

    for cls in SELECTED:
        src = os.path.join(IMG_DIR, cls)
        files = sorted(os.listdir(src))
        files = [f for f in files if f.lower().endswith((".jpg", ".jpeg", ".png"))]

        # ---- exact dedupe (byte hash)
        seen, uniq = set(), []
        for f in files:
            h = sha256(os.path.join(src, f))
            if h in seen:
                report["duplicates_removed"] += 1
                continue
            seen.add(h)
            uniq.append(f)

        # ---- near-dedupe (aHash, Hamming <= 2)
        kept = []
        hashes = []
        for f in uniq:
            p = os.path.join(src, f)
            try:
                h = ahash(p)
            except Exception:
                continue  # unreadable => drop
            if any(int(np.count_nonzero(h != g)) <= 2 for g in hashes):
                report["near_duplicates_removed"] += 1
                continue
            hashes.append(h)
            kept.append(f)

        rng.shuffle(kept)
        kept = kept[: args.cap]

        # ---- stratified split
        n = len(kept)
        n_tr = int(n * SPLIT[0])
        n_va = int(n * SPLIT[1])
        splits = {
            "train": kept[:n_tr],
            "validation": kept[n_tr:n_tr + n_va],
            "test": kept[n_tr + n_va:],
        }
        counts = {}
        for split, fl in splits.items():
            d = os.path.join(OUT, split, cls)
            os.makedirs(d, exist_ok=True)
            for f in fl:
                shutil.copy(os.path.join(src, f), os.path.join(d, f))
            counts[split] = len(fl)
            grand[split] += len(fl)
        report["classes"][cls] = {
            "available": len(files), "after_dedupe": len(uniq),
            "kept": n, "category": SELECTED[cls], **counts,
        }
        print(f"{cls:13s} avail={len(files):3d} uniq={len(uniq):3d} kept={n:3d} "
              f"-> train {counts['train']} val {counts['validation']} test {counts['test']}")

    report["totals"] = dict(grand)
    report["selected"] = SELECTED
    with open(os.path.join(OUT, "split_summary.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1)
    print(f"\nTOTALS: {dict(grand)}  (grand total {sum(grand.values())} real photographs)")
    print(f"duplicates removed: {report['duplicates_removed']}, "
          f"near-duplicates removed: {report['near_duplicates_removed']}")
    print("wrote data/split_summary.json")


if __name__ == "__main__":
    main()
