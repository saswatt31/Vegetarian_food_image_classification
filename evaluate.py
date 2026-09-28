"""
Evaluate the trained food classifier on the test split:
  * overall + per-class accuracy
  * confusion matrix -> results/confusion_matrix.png
  * performance ACROSS MEAL CATEGORIES -> results/category_accuracy.csv
"""
import argparse
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms

from train import DEVICE, IMAGENET_MEAN, IMAGENET_STD, build_model

# class -> meal category (kept in sync with prepare_dataset.CLASSES)
CATEGORY_OF = {
    "veg_thali": "Main Course", "paneer_curry": "Main Course",
    "veg_biryani": "Main Course", "dosa": "Breakfast", "idli": "Breakfast",
    "samosa": "Snack", "lassi": "Beverage",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--model", default="outputs/best_model.pth")
    ap.add_argument("--out", default="results")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    ckpt = torch.load(args.model, map_location=DEVICE, weights_only=False)
    classes = ckpt["classes"]

    tf = transforms.Compose([
        transforms.Resize(256), transforms.CenterCrop(224),
        transforms.ToTensor(), transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])
    test = datasets.ImageFolder(os.path.join(args.data_dir, "test"), tf)
    dl = DataLoader(test, batch_size=32, shuffle=False, num_workers=0)

    model = build_model(len(classes), finetune=False)
    model.load_state_dict(ckpt["model_state"])
    model.eval()

    y_true, y_pred = [], []
    with torch.no_grad():
        for x, y in dl:
            logits = model(x.to(DEVICE))
            y_pred.extend(logits.argmax(1).cpu().tolist())
            y_true.extend(y.tolist())

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    acc = (y_true == y_pred).mean()

    lines = [f"Test samples : {len(y_true)}",
             f"Test accuracy: {acc:.4f}", "",
             "Per-class report:", ""]
    from sklearn.metrics import classification_report, confusion_matrix
    report = classification_report(y_true, y_pred, target_names=classes,
                                   zero_division=0)
    lines += [report]
    print("\n".join(lines))

    with open(os.path.join(args.out, "classification_report.txt"), "w",
              encoding="utf-8") as f:
        f.write("\n".join(lines))

    # ---- confusion matrix -------------------------------------------------
    cm = confusion_matrix(y_true, y_pred)
    fig, ax = plt.subplots(figsize=(7.5, 6.5))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(len(classes)), classes, rotation=45, ha="right")
    ax.set_yticks(range(len(classes)), classes)
    for i in range(len(classes)):
        for j in range(len(classes)):
            ax.text(j, i, cm[i, j], ha="center", va="center",
                    color="white" if cm[i, j] > cm.max() / 2 else "black",
                    fontsize=9)
    ax.set_xlabel("predicted"); ax.set_ylabel("true")
    ax.set_title(f"Confusion matrix (test acc = {acc:.3f})")
    fig.colorbar(im, fraction=0.046)
    fig.tight_layout()
    fig.savefig(os.path.join(args.out, "confusion_matrix.png"), dpi=140)
    plt.close(fig)

    # ---- per-meal-category performance -------------------------------------
    rows = []
    for cls_idx, cls in enumerate(classes):
        m = y_true == cls_idx
        if m.sum() == 0:
            continue
        rows.append({
            "class": cls,
            "meal_category": CATEGORY_OF.get(cls, "Uncategorized"),
            "samples": int(m.sum()),
            "accuracy": float((y_pred[m] == cls_idx).mean()),
        })
    cat_df = pd.DataFrame(rows)
    cat_summary = (cat_df.groupby("meal_category")
                   .apply(lambda g: np.average(g["accuracy"], weights=g["samples"]),
                          include_groups=False)
                   .rename("category_accuracy").reset_index())
    cat_df.to_csv(os.path.join(args.out, "category_accuracy.csv"), index=False)
    cat_summary.to_csv(os.path.join(args.out, "category_accuracy_summary.csv"),
                       index=False)

    print("\nAccuracy across meal categories:")
    print(cat_summary.to_string(index=False))
    print(f"\nsaved {args.out}/classification_report.txt, "
          f"confusion_matrix.png, category_accuracy*.csv")


if __name__ == "__main__":
    main()
