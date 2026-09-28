"""
Build the vegetarian food image dataset.

Default mode: generate a synthetic-but-learnable dataset of "mobile food
photos" so the whole project runs offline on a laptop. Each class has a
distinct visual signature (colors, plate shape, texture pattern), simulating
real dish appearance variation via hue/lightness jitter, rotation and crops.

Real-data mode: --real-dir <folder-of-class-subfolders> splits your own
photos into train/val/test instead (80/10/10).

Output layout:
  data/train/<class>/xxx.png ... data/val/... data/test/...
  data/labels.csv   (filepath, class, meal_category, split)
"""
import argparse
import csv
import os
import shutil

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

CLASSES = {
    "veg_thali":     {"category": "Main Course", "base": (215, 170, 90),  "shape": "circle",  "spots": 26},
    "paneer_curry":  {"category": "Main Course", "base": (205, 120, 60),  "shape": "bowl",    "spots": 18},
    "dosa":          {"category": "Breakfast",   "base": (222, 178, 105), "shape": "oval",    "spots": 4},
    "idli":          {"category": "Breakfast",   "base": (235, 235, 228), "shape": "circle",  "spots": 6},
    "samosa":        {"category": "Snack",       "base": (196, 140, 70),  "shape": "triangle","spots": 5},
    "veg_biryani":   {"category": "Main Course", "base": (222, 190, 120), "shape": "bowl",    "spots": 40},
    "lassi":         {"category": "Beverage",    "base": (240, 236, 220), "shape": "glass",   "spots": 2},
}

IMG_SIZE = 224
SPLIT = {"train": 0.8, "val": 0.1, "test": 0.1}


# --------------------------------------------------------------------------
# synthetic image generation
# --------------------------------------------------------------------------
def _draw_background(rng: np.random.Generator) -> Image.Image:
    """Tablecloth / wooden table background with slight noise."""
    hue = int(rng.integers(0, 40))
    bg = Image.new("RGB", (IMG_SIZE, IMG_SIZE),
                   (60 + hue, 45 + hue // 2, 35 + hue // 3))
    d = ImageDraw.Draw(bg)
    for _ in range(120):  # subtle texture
        x, y = rng.integers(0, IMG_SIZE, 2)
        x2, y2 = x + rng.integers(-8, 8), y + rng.integers(-8, 8)
        c = int(rng.integers(45, 95))
        d.line((x, y, x2, y2), fill=(c, c - 10, c - 20), width=1)
    return bg


def _draw_dish(rng: np.random.Generator, cls: str, spec: dict) -> Image.Image:
    """The food item itself, centered, class-specific shape/colors."""
    img = _draw_background(rng)
    d = ImageDraw.Draw(img)
    cx, cy = IMG_SIZE // 2, IMG_SIZE // 2

    jitter = lambda base, amt=18: tuple(
        int(np.clip(c + rng.integers(-amt, amt + 1), 0, 255)) for c in base)

    if spec["shape"] == "circle":       # thali plate / idli
        r = rng.integers(70, 88)
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=jitter((240, 240, 235)))
        for _ in range(spec["spots"]):
            ang = rng.uniform(0, 2 * np.pi)
            rr = rng.uniform(0, r * 0.75)
            k = rng.integers(7, 15)
            d.ellipse((cx + rr * np.cos(ang) - k, cy + rr * np.sin(ang) - k,
                       cx + rr * np.cos(ang) + k, cy + rr * np.sin(ang) + k),
                      fill=jitter(spec["base"]))
    elif spec["shape"] == "bowl":       # curry / biryani
        r = rng.integers(74, 92)
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=jitter((150, 150, 155)))
        r2 = int(r * 0.82)
        d.ellipse((cx - r2, cy - r2, cx + r2, cy + r2), fill=jitter(spec["base"]))
        for _ in range(spec["spots"]):  # chunks / grains
            ang = rng.uniform(0, 2 * np.pi)
            rr = rng.uniform(0, r2 * 0.7)
            k = rng.integers(4, 10)
            color = jitter((255, 255, 255)) if cls == "veg_biryani" else jitter((250, 245, 235))
            d.ellipse((cx + rr * np.cos(ang) - k, cy + rr * np.sin(ang) - k,
                       cx + rr * np.cos(ang) + k, cy + rr * np.sin(ang) + k), fill=color)
    elif spec["shape"] == "oval":       # dosa
        w, h = rng.integers(85, 100), rng.integers(40, 52)
        d.ellipse((cx - w, cy - h, cx + w, cy + h), fill=jitter(spec["base"]))
        d.ellipse((cx - w + 12, cy - h + 8, cx + w - 12, cy + h - 8),
                  fill=jitter((205, 155, 85)))
    elif spec["shape"] == "triangle":   # samosa
        s = rng.integers(55, 70)
        pts = [(cx, cy - s), (cx - s, cy + s * 0.7), (cx + s, cy + s * 0.7)]
        d.polygon(pts, fill=jitter(spec["base"]))
        d.line((pts[0], pts[1]), fill=jitter((150, 100, 50)), width=4)
        d.line((pts[0], pts[2]), fill=jitter((150, 100, 50)), width=4)
    elif spec["shape"] == "glass":      # lassi
        w, h = rng.integers(38, 46), rng.integers(80, 95)
        d.rectangle((cx - w, cy - h, cx + w, cy + h), fill=jitter(spec["base"]))
        d.rectangle((cx - w, cy - h, cx - w + 8, cy + h), fill=jitter((210, 205, 195)))
        d.ellipse((cx - w, cy - h - 6, cx + w, cy - h + 10), fill=jitter((250, 250, 245)))
    return img


def _mobile_augment(rng: np.random.Generator, img: Image.Image) -> Image.Image:
    """Simulate mobile-photo variation: rotation, brightness, blur, noise."""
    img = img.rotate(rng.uniform(-25, 25), resample=Image.BILINEAR,
                     fillcolor=(70, 55, 40))
    img = np.asarray(img).astype(np.int16)
    img = np.clip(img + rng.integers(-22, 23), 0, 255).astype(np.uint8)
    out = Image.fromarray(img)
    if rng.random() < 0.35:
        out = out.filter(ImageFilter.GaussianBlur(rng.uniform(0.4, 1.3)))
    return out.resize((IMG_SIZE, IMG_SIZE))


def generate_synthetic(out_root: str, per_class: int) -> list[tuple]:
    rows, idx = [], 0
    for cls, spec in CLASSES.items():
        rng = np.random.default_rng(1000 + hash(cls) % 1000)
        for i in range(per_class):
            split = ("train" if i < per_class * SPLIT["train"] else
                     "val" if i < per_class * (SPLIT["train"] + SPLIT["val"])
                     else "test")
            img = _draw_dish(rng, cls, spec)
            img = _mobile_augment(rng, img)
            rel = os.path.join(split, cls, f"{cls}_{i:03d}.png")
            path = os.path.join(out_root, rel)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            img.save(path)
            rows.append((rel, cls, spec["category"], split))
            idx += 1
        print(f"  {cls}: {per_class} images ({spec['category']})")
    return rows


def split_real(src_root: str, out_root: str) -> list[tuple]:
    rows = []
    cls_dirs = [d for d in sorted(os.listdir(src_root))
                if os.path.isdir(os.path.join(src_root, d))]
    rng = np.random.default_rng(7)
    for cls in cls_dirs:
        category = "Uncategorized"
        files = [f for f in os.listdir(os.path.join(src_root, cls))
                 if f.lower().endswith((".jpg", ".jpeg", ".png"))]
        rng.shuffle(files)
        n = len(files)
        cuts = (int(n * SPLIT["train"]), int(n * (SPLIT["train"] + SPLIT["val"])))
        for split, group in zip(("train", "val", "test"),
                                (files[:cuts[0]], files[cuts[0]:cuts[1]],
                                 files[cuts[1]:])):
            for f in group:
                rel = os.path.join(split, cls, f)
                dst = os.path.join(out_root, rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(os.path.join(src_root, cls, f), dst)
                rows.append((rel, cls, category, split))
        print(f"  {cls}: {n} images")
    return rows


def main():
    ap = argparse.ArgumentParser(description="Prepare vegetarian food dataset")
    ap.add_argument("--real-dir", default=None,
                    help="folder with one sub-folder per class (real photos)")
    ap.add_argument("--out", default="data")
    ap.add_argument("--per-class", type=int, default=160)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    if args.real_dir:
        rows = split_real(args.real_dir, args.out)
    else:
        rows = generate_synthetic(args.out, args.per_class)

    with open(os.path.join(args.out, "labels.csv"), "w", newline="",
              encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["filepath", "class", "meal_category", "split"])
        w.writerows(rows)
    n = len(rows)
    print(f"\nwrote {args.out}: {n} images "
          f"({sum(1 for r in rows if r[3] == 'train')} train / "
          f"{sum(1 for r in rows if r[3] == 'val')} val / "
          f"{sum(1 for r in rows if r[3] == 'test')} test)")


if __name__ == "__main__":
    main()
