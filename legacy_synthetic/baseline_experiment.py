"""
Baseline experiment for the comparison table in the report:
ResNet-18 with RANDOM-INIT weights (no ImageNet pretraining), frozen backbone,
head-only training -- the identical protocol to train.py.

This quantifies exactly how much ImageNet transfer learning contributes on
the vegetarian-food dataset (same data, same split, same epochs, same optimizer).

Run:    python baseline_experiment.py
Output: results/baseline_scratch.json
"""
import json
import os

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms

from train import (DEVICE, IMAGENET_MEAN, IMAGENET_STD, build_model,
                   run_one_epoch)

BASE = os.path.dirname(os.path.abspath(__file__))


def eval_test(model):
    from sklearn.metrics import classification_report
    tf = transforms.Compose([
        transforms.Resize(256), transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])
    test = datasets.ImageFolder(os.path.join(BASE, "data", "test"), tf)
    dl = DataLoader(test, batch_size=32, shuffle=False, num_workers=0)
    model.eval()
    y_true, y_pred = [], []
    with torch.no_grad():
        for x, y in dl:
            pred = model(x.to(DEVICE)).argmax(1).cpu()
            y_pred.extend(pred.tolist())
            y_true.extend(y.tolist())
    rep = classification_report(y_true, y_pred, output_dict=True,
                                zero_division=0)
    macro = rep["macro avg"]
    return rep["accuracy"], macro["precision"], macro["recall"], macro["f1-score"]


def main():
    data_dir = os.path.join(BASE, "data")
    train_tf = transforms.Compose([
        transforms.RandomResizedCrop(224, scale=(0.7, 1.0)),
        transforms.RandomHorizontalFlip(),
        transforms.ColorJitter(0.15, 0.15, 0.15),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])
    eval_tf = transforms.Compose([
        transforms.Resize(256), transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])
    train = datasets.ImageFolder(os.path.join(data_dir, "train"), train_tf)
    val = datasets.ImageFolder(os.path.join(data_dir, "val"), eval_tf)
    train_dl = DataLoader(train, batch_size=32, shuffle=True, num_workers=0)
    val_dl = DataLoader(val, batch_size=32, shuffle=False, num_workers=0)
    classes = train.classes

    # ---- random-init ResNet-18, frozen backbone, trained head (same as train.py)
    torch.manual_seed(0)
    model = models.resnet18(weights=None)
    for p in model.parameters():
        p.requires_grad = False
    model.fc = nn.Linear(model.fc.in_features, len(classes))
    model = model.to(DEVICE)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(
        [p for p in model.parameters() if p.requires_grad], lr=1e-3)

    best_val, best_epoch = 0.0, 0
    for epoch in range(1, 7):  # same 6 epochs as train.py default
        tr_loss, tr_acc = run_one_epoch(model, train_dl, criterion, optimizer)
        va_loss, va_acc = run_one_epoch(model, val_dl, criterion)
        if va_acc > best_val:
            best_val, best_epoch = va_acc, epoch
        print(f"[scratch] epoch {epoch:02d} | train acc {tr_acc:.4f} | "
              f"val acc {va_acc:.4f}")

    test_acc, mp, mr, mf1 = eval_test(model)
    out = {
        "model": "ResNet-18 (random init, frozen backbone, head-only)",
        "epochs": 6, "best_val_accuracy": round(best_val, 4),
        "best_epoch": best_epoch, "test_accuracy": round(test_acc, 4),
        "macro_precision": round(mp, 4), "macro_recall": round(mr, 4),
        "macro_f1": round(mf1, 4),
        "test_samples": 112,
    }
    os.makedirs(os.path.join(BASE, "results"), exist_ok=True)
    out_path = os.path.join(BASE, "results", "baseline_scratch.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(json.dumps(out, indent=2))
    print(f"saved {out_path}")


if __name__ == "__main__":
    main()
