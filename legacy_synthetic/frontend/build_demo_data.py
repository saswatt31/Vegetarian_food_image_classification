"""
Assemble the frontend data bundle from real project artifacts:
  * results/predictions.json  -> frontend/data/predictions.json (verbatim)
  * per-class / category CSVs -> frontend/data/metrics.json
  * data/test/<class>/*.png   -> frontend/assets/img/<class>/<file> (thumbnails)

Run:    python frontend/build_demo_data.py
"""
import csv
import json
import os
import shutil

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONT = os.path.join(BASE, "frontend")
DATA = os.path.join(FRONT, "data")
IMG = os.path.join(FRONT, "assets", "img")

CLASS_META = {
    "veg_thali":    {"label": "Veg Thali",      "category": "Main Course", "blurb": "Full plated meal with katori sides"},
    "paneer_curry": {"label": "Paneer Curry",   "category": "Main Course", "blurb": "Cottage cheese in rich gravy, bowl-served"},
    "veg_biryani":  {"label": "Veg Biryani",    "category": "Main Course", "blurb": "Layered rice bowl, grain texture"},
    "dosa":         {"label": "Dosa",           "category": "Breakfast",   "blurb": "Golden crisp crepe, oval silhouette"},
    "idli":         {"label": "Idli",           "category": "Breakfast",   "blurb": "Steamed white cakes, paired circles"},
    "samosa":       {"label": "Samosa",         "category": "Snack",       "blurb": "Fried pastry triangles, crisp edges"},
    "lassi":        {"label": "Lassi",          "category": "Beverage",    "blurb": "Tall frothy yogurt drink"},
}


def main():
    os.makedirs(DATA, exist_ok=True)

    # 1. predictions verbatim
    shutil.copy(os.path.join(BASE, "results", "predictions.json"),
                os.path.join(DATA, "predictions.json"))

    # 2. metrics.json
    per_class, cat = {}, {}
    with open(os.path.join(BASE, "results", "category_accuracy.csv"),
              encoding="utf-8") as f:
        for r in csv.DictReader(f):
            per_class[r["class"]] = {"category": r["meal_category"],
                                     "samples": int(r["samples"]),
                                     "accuracy": float(r["accuracy"])}
    with open(os.path.join(BASE, "results", "category_accuracy_summary.csv"),
              encoding="utf-8") as f:
        for r in csv.DictReader(f):
            cat[r["meal_category"]] = float(r["category_accuracy"])

    pred = json.load(open(os.path.join(BASE, "results", "predictions.json"),
                          encoding="utf-8"))
    metrics = {
        "test_accuracy": pred["accuracy"],
        "total": pred["total"], "correct": pred["correct"],
        "classes": pred["classes"],
        "trainable_params": 3591,
        "epochs": 6, "batch_size": 32, "lr": "1e-3", "optimizer": "Adam",
        "backbone": "ResNet-18 (ImageNet1K_V1, frozen)",
        "per_class": per_class, "categories": cat,
        "class_meta": CLASS_META,
    }
    with open(os.path.join(DATA, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=1)

    # 3. thumbnails (max 3 per class keeps the bundle light; the demo
    #    actually uses one hero + up to 12 gallery items)
    n_copied = 0
    for cls in CLASS_META:
        src_dir = os.path.join(BASE, "data", "test", cls)
        dst_dir = os.path.join(IMG, cls)
        os.makedirs(dst_dir, exist_ok=True)
        files = sorted(os.listdir(src_dir))[:3]
        for fn in files:
            shutil.copy(os.path.join(src_dir, fn), os.path.join(dst_dir, fn))
            n_copied += 1

    print(f"frontend data ready: metrics.json, predictions.json "
          f"({pred['total']} records), {n_copied} thumbnails")


if __name__ == "__main__":
    main()
