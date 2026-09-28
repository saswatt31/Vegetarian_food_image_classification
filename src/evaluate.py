"""
Evaluate the trained model on the UNSEEN test split only.

Outputs (all from the actual trained model + real test images):
  results/classification_report.txt   accuracy, precision/recall/F1 (macro+weighted), per-class table
  results/confusion_matrix.png        8x8 matrix labelled with the real class names
  results/category_accuracy.csv       per-meal-category performance
  results/test_predictions.json       per-image predictions (for the demo/report)
  results/sample_predictions.png      montage: actual vs predicted + confidence
  results/test_metrics.json           headline metrics summary
"""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
from sklearn.metrics import (accuracy_score, classification_report,
                             confusion_matrix, f1_score, precision_score,
                             recall_score)

from dataset import (CATEGORY_OF, DEVICE, MODELS, RESULTS, eval_transform,
                     make_loaders)
from PIL import Image

def load_model():
    ckpt = torch.load(os.path.join(MODELS, "best_model.pth"),
                      map_location=DEVICE, weights_only=False)
    classes = ckpt["classes"]
    from dataset import build_model
    model = build_model(len(classes))
    model.load_state_dict(ckpt["model_state"])
    model.to(DEVICE).eval()
    return model, classes


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    _, _, test_dl, classes = make_loaders()
    model, ckpt_classes = load_model()
    assert ckpt_classes == classes, "checkpoint classes != test folder order"

    y_true, y_pred, confs, paths = [], [], [], []
    with torch.no_grad():
        for (x, y), pl in zip(test_dl, [b[0] for b in test_dl.dataset.samples]):
            pass  # placeholder to keep linters calm; real loop below

    # real loop (also records file paths + confidences)
    ds = test_dl.dataset
    dl = torch.utils.data.DataLoader(ds, batch_size=32, shuffle=False, num_workers=2)
    with torch.no_grad():
        for x, y in dl:
            out = model(x.to(DEVICE))
            prob = torch.softmax(out, dim=1)
            c, p = prob.max(1)
            y_true.extend(y.tolist())
            y_pred.extend(p.cpu().tolist())
            confs.extend(c.cpu().tolist())
    paths = [s[0] for s in ds.samples]

    acc = accuracy_score(y_true, y_pred)
    prec_m = precision_score(y_true, y_pred, average="macro", zero_division=0)
    rec_m = recall_score(y_true, y_pred, average="macro", zero_division=0)
    f1_macro = f1_score(y_true, y_pred, average="macro", zero_division=0)
    f1_weighted = f1_score(y_true, y_pred, average="weighted", zero_division=0)
    prec_w = precision_score(y_true, y_pred, average="weighted", zero_division=0)
    rec_w = recall_score(y_true, y_pred, average="weighted", zero_division=0)

    lines = []
    lines.append("TEST-SET EVALUATION (unseen real photographs)")
    lines.append("=" * 60)
    lines.append(f"test images : {len(y_true)}")
    lines.append(f"accuracy    : {acc:.4f}")
    lines.append(f"precision   : macro {prec_m:.4f} | weighted {prec_w:.4f}")
    lines.append(f"recall      : macro {rec_m:.4f} | weighted {rec_w:.4f}")
    lines.append(f"F1          : macro {f1_macro:.4f} | weighted {f1_weighted:.4f}")
    lines.append("")
    lines.append(classification_report(y_true, y_pred, target_names=classes,
                                       digits=4, zero_division=0))
    report_txt = "\n".join(lines)
    with open(os.path.join(RESULTS, "classification_report.txt"), "w",
              encoding="utf-8") as f:
        f.write(report_txt)
    print(report_txt)

    # ---- confusion matrix with real class names
    cm = confusion_matrix(y_true, y_pred)
    fig, ax = plt.subplots(figsize=(8.6, 7.2))
    im = ax.imshow(cm, cmap="Oranges")
    ax.set_xticks(range(len(classes)), classes, rotation=35, ha="right", fontsize=9)
    ax.set_yticks(range(len(classes)), classes, fontsize=9)
    thresh = cm.max() / 2
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center", fontsize=9,
                    color="white" if cm[i, j] > thresh else "#333")
    ax.set_xlabel("Predicted"); ax.set_ylabel("Actual")
    ax.set_title(f"Confusion matrix — test set (accuracy {acc:.4f})")
    fig.colorbar(im, shrink=0.8)
    fig.tight_layout()
    fig.savefig(os.path.join(RESULTS, "confusion_matrix.png"), dpi=150)
    plt.close(fig)

    # ---- meal-category analysis from ACTUAL test results
    cat_stats = {}
    for idx, cls in enumerate(classes):
        cat = CATEGORY_OF[cls]
        sel = [k for k, t in enumerate(y_true) if t == idx]
        correct = sum(1 for k in sel if y_pred[k] == idx)
        cat_stats.setdefault(cat, {"n": 0, "correct": 0})
        cat_stats[cat]["n"] += len(sel)
        cat_stats[cat]["correct"] += correct
    with open(os.path.join(RESULTS, "category_accuracy.csv"), "w",
              encoding="utf-8") as f:
        f.write("meal_category,classes,samples,correct,accuracy\n")
        for cat, s in sorted(cat_stats.items()):
            f.write(f"{cat},{s['n'] and ''}{s['correct']}/{s['n']},"
                    f"{s['n']},{s['correct']},{s['correct']/s['n']:.4f}\n")
    print("\nmeal-category performance (from actual test results):")
    for cat, s in sorted(cat_stats.items()):
        print(f"  {cat:10s} {s['correct']:3d}/{s['n']:3d} = {s['correct']/s['n']:.4f}")

    # ---- per-image predictions export (used by frontend + report)
    recs = []
    for p, t, pr, c in zip(paths, y_true, y_pred, confs):
        prob_top = []
        recs.append({"file": os.path.basename(p), "relpath": p, "true": classes[t],
                     "pred": classes[pr], "confidence": round(c, 4),
                     "correct": t == pr})
    with open(os.path.join(RESULTS, "test_predictions.json"), "w",
              encoding="utf-8") as f:
        json.dump({"classes": classes, "total": len(recs),
                   "correct": sum(r["correct"] for r in recs),
                   "accuracy": round(acc, 4), "records": recs}, f, indent=1)

    # ---- qualitative montage: 10 test images, actual vs predicted
    from PIL import ImageDraw, ImageFont
    try:
        font = ImageFont.truetype("C:\\Windows\\Fonts\\segoeui.ttf", 16)
        fontb = ImageFont.truetype("C:\\Windows\\Fonts\\segoeuib.ttf", 16)
    except OSError:
        font = fontb = ImageFont.load_default()
    idxs = list(range(0, len(recs), max(1, len(recs) // 10)))[:10]
    tile = 220
    grid = Image.new("RGB", (tile * 5, (tile + 46) * 2), (250, 250, 247))
    d = ImageDraw.Draw(grid)
    for k, i in enumerate(idxs):
        r = recs[i]
        with Image.open(r["relpath"]) as im:
            im = im.convert("RGB")
            w, h = im.size
            s = min(w, h)
            im = im.crop(((w - s) // 2, (h - s) // 2, (w + s) // 2, (h + s) // 2)
                         ).resize((tile, tile))
        gx, gy = (k % 5) * tile, (k // 5) * (tile + 46)
        grid.paste(im, (gx, gy))
        ok = r["correct"]
        d.rectangle([gx, gy + tile, gx + tile, gy + tile + 46],
                    fill=(46, 90, 58) if ok else (156, 72, 18))
        d.text((gx + 8, gy + tile + 4), f"true: {r['true']}", fill="white", font=fontb)
        d.text((gx + 8, gy + tile + 24),
               f"pred: {r['pred']} {r['confidence']*100:.1f}%",
               fill=(230, 240, 230) if ok else (255, 220, 190), font=font)
    grid.save(os.path.join(RESULTS, "sample_predictions.png"))
    print("wrote results/sample_predictions.png")

    metrics = {"accuracy": round(acc, 4), "precision_macro": round(prec_m, 4),
               "recall_macro": round(rec_m, 4), "f1_macro": round(f1_macro, 4),
               "f1_weighted": round(f1_weighted, 4),
               "precision_weighted": round(prec_w, 4),
               "recall_weighted": round(rec_w, 4),
               "test_images": len(y_true),
               "per_category": {k: {"correct": v["correct"], "n": v["n"],
                                    "accuracy": round(v["correct"] / v["n"], 4)}
                                for k, v in cat_stats.items()}}
    with open(os.path.join(RESULTS, "test_metrics.json"), "w") as f:
        json.dump(metrics, f, indent=1)
    print("wrote results/test_metrics.json")


if __name__ == "__main__":
    main()
