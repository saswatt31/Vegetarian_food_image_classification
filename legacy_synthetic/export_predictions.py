"""
Export per-test-image predictions to JSON for the web demo frontend.

Replays the exact evaluation pass of evaluate.py (same transforms, same
checkpoint) but records each image's predicted class and top-3 softmax
probabilities instead of only aggregate metrics.

Run:    python export_predictions.py
Output: results/predictions.json  (list of per-image records)
"""
import json
import os

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms

from train import DEVICE, IMAGENET_MEAN, IMAGENET_STD

BASE = os.path.dirname(os.path.abspath(__file__))


def main():
    ckpt = torch.load(os.path.join(BASE, "outputs", "best_model.pth"),
                      map_location=DEVICE, weights_only=False)
    classes = ckpt["classes"]

    tf = transforms.Compose([
        transforms.Resize(256), transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])
    test = datasets.ImageFolder(os.path.join(BASE, "data", "test"), tf)
    dl = DataLoader(test, batch_size=32, shuffle=False, num_workers=0)

    model = models.resnet18(weights=None)
    model.fc = nn.Linear(model.fc.in_features, len(classes))
    model.load_state_dict(ckpt["model_state"])
    model.to(DEVICE).eval()

    records = []
    all_paths = [s[0] for s in test.samples]  # same order as dl (shuffle=False)
    cursor = 0
    with torch.no_grad():
        for x, y in dl:
            probs = torch.softmax(model(x.to(DEVICE)), dim=1).cpu()
            for i in range(x.size(0)):
                path = all_paths[cursor]
                cursor += 1
                top = probs[i].topk(3)
                rec = {
                    "file": os.path.basename(path),
                    "relpath": f"test/{test.classes[y[i]]}/{os.path.basename(path)}",
                    "true": test.classes[y[i]],
                    "pred": classes[top.indices[0].item()],
                    "confidence": round(top.values[0].item(), 4),
                    "top3": [
                        {"class": classes[top.indices[k].item()],
                         "prob": round(top.values[k].item(), 4)}
                        for k in range(3)
                    ],
                    "correct": classes[top.indices[0].item()] == test.classes[y[i]],
                }
                records.append(rec)

    n = len(records)
    n_ok = sum(1 for r in records if r["correct"])
    out_path = os.path.join(BASE, "results", "predictions.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"classes": classes, "total": n, "correct": n_ok,
                   "accuracy": round(n_ok / n, 4), "records": records},
                  f, indent=1)
    print(f"exported {n} predictions ({n_ok} correct, acc {n_ok/n:.4f})")
    print(f"saved {out_path}")


if __name__ == "__main__":
    main()
