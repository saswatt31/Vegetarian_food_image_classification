"""
Two-stage transfer-learning training on the real-photo vegetarian subset.

Stage 1 — frozen backbone, train the new head (higher LR).
Stage 2 — unfreeze layer3 + layer4, fine-tune everything at a lower LR.

Per-epoch console output: train/val loss + train/val accuracy.
Best checkpoint (validation accuracy) -> models/best_model.pth
Class mapping                         -> models/class_names.json
Curves                                -> results/training_loss.png, accuracy_curve.png
History                              -> results/training_history.json
"""
import argparse
import json
import os
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import torch
import torch.nn as nn

from dataset import (DEVICE, MODELS, RESULTS, build_model, make_loaders,
                     save_class_names, unfreeze_late_layers)


def run_stage(model, loader_train, loader_val, epochs, lr, stage_name,
              criterion, optimizer, scheduler, history, best):
    for epoch in range(1, epochs + 1):
        t0 = time.time()
        # ---- train
        model.train()
        tr_loss = tr_correct = tr_n = 0
        for x, y in loader_train:
            x, y = x.to(DEVICE), y.to(DEVICE)
            optimizer.zero_grad()
            out = model(x)
            loss = criterion(out, y)
            loss.backward()
            optimizer.step()
            tr_loss += loss.item() * y.size(0)
            tr_correct += (out.argmax(1) == y).sum().item()
            tr_n += y.size(0)
        if scheduler:
            scheduler.step()

        # ---- validate
        model.eval()
        va_loss = va_correct = va_n = 0
        with torch.no_grad():
            for x, y in loader_val:
                x, y = x.to(DEVICE), y.to(DEVICE)
                out = model(x)
                loss = criterion(out, y)
                va_loss += loss.item() * y.size(0)
                va_correct += (out.argmax(1) == y).sum().item()
                va_n += y.size(0)

        tr_acc, va_acc = tr_correct / tr_n, va_correct / va_n
        history["train_loss"].append(tr_loss / tr_n)
        history["val_loss"].append(va_loss / va_n)
        history["train_acc"].append(tr_acc)
        history["val_acc"].append(va_acc)
        print(f"[{stage_name}] epoch {epoch:02d} | "
              f"train loss {tr_loss/tr_n:.4f} acc {tr_acc:.4f} | "
              f"val loss {va_loss/va_n:.4f} acc {va_acc:.4f} | "
              f"{time.time()-t0:.0f}s")

        if va_acc > best["val_acc"]:
            best.update({"val_acc": va_acc, "epoch": len(history["val_acc"]),
                         "stage": stage_name})
            torch.save({"model_state": model.state_dict(),
                        "classes": best["classes"],
                        "val_acc": va_acc},
                       os.path.join(MODELS, "best_model.pth"))
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--stage1-epochs", type=int, default=6)
    ap.add_argument("--stage2-epochs", type=int, default=6)
    ap.add_argument("--lr-head", type=float, default=1e-3)
    ap.add_argument("--lr-ft", type=float, default=1e-4)
    args = ap.parse_args()

    os.makedirs(MODELS, exist_ok=True)
    os.makedirs(RESULTS, exist_ok=True)

    train_dl, val_dl, _, classes = make_loaders(args.batch_size)
    save_class_names(classes)
    print(f"device: {DEVICE} | classes ({len(classes)}): {classes}")

    model = build_model(len(classes)).to(DEVICE)
    criterion = nn.CrossEntropyLoss()
    history = {"train_loss": [], "val_loss": [], "train_acc": [], "val_acc": []}
    best = {"val_acc": -1.0, "epoch": 0, "stage": "", "classes": classes}

    # ---------------- stage 1: frozen backbone, head only ----------------
    head_params = [p for p in model.parameters() if p.requires_grad]
    opt1 = torch.optim.Adam(head_params, lr=args.lr_head)
    sched1 = torch.optim.lr_scheduler.CosineAnnealingLR(opt1, T_max=args.stage1_epochs)
    best = run_stage(model, train_dl, val_dl, args.stage1_epochs, args.lr_head,
                     "stage1-frozen", criterion, opt1, sched1, history, best)

    # ---------------- stage 2: fine-tune layer3+layer4 -------------------
    unfreeze_late_layers(model)
    ft_params = [p for p in model.parameters() if p.requires_grad]
    opt2 = torch.optim.Adam(ft_params, lr=args.lr_ft)
    sched2 = torch.optim.lr_scheduler.CosineAnnealingLR(opt2, T_max=args.stage2_epochs)
    best = run_stage(model, train_dl, val_dl, args.stage2_epochs, args.lr_ft,
                     "stage2-finetune", criterion, opt2, sched2, history, best)

    print(f"\nbest: val acc {best['val_acc']:.4f} "
          f"({best['stage']}, epoch {best['epoch']}) -> models/best_model.pth")

    n1 = args.stage1_epochs
    with open(os.path.join(RESULTS, "training_history.json"), "w") as f:
        json.dump({**history, "stage1_epochs": n1, "best": 
                   {"val_acc": best["val_acc"], "epoch": best["epoch"],
                    "stage": best["stage"]}}, f, indent=1)

    # ---------------- curves ----------------
    eps = range(1, len(history["train_loss"]) + 1)
    fig, ax = plt.subplots(figsize=(8, 4.6))
    ax.plot(eps, history["train_loss"], "o-", label="train loss", color="#C25E1C")
    ax.plot(eps, history["val_loss"], "s-", label="val loss", color="#3E7C4F")
    ax.axvline(n1 + 0.5, ls="--", c="#999", lw=1)
    ax.text(n1 + 0.6, ax.get_ylim()[1] * 0.95, "fine-tune starts", fontsize=9, color="#666")
    ax.set_xlabel("epoch"); ax.set_ylabel("cross-entropy loss")
    ax.set_title("Training loss (real-photo subset, 8 classes)")
    ax.legend(); ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout(); fig.savefig(os.path.join(RESULTS, "training_loss.png"), dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4.6))
    ax.plot(eps, history["train_acc"], "o-", label="train acc", color="#C25E1C")
    ax.plot(eps, history["val_acc"], "s-", label="val acc", color="#3E7C4F")
    ax.axvline(n1 + 0.5, ls="--", c="#999", lw=1)
    ax.set_xlabel("epoch"); ax.set_ylabel("accuracy")
    ax.set_title("Accuracy curve (real-photo subset, 8 classes)")
    ax.legend(); ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout(); fig.savefig(os.path.join(RESULTS, "accuracy_curve.png"), dpi=150)
    plt.close(fig)
    print("wrote results/training_loss.png, accuracy_curve.png")


if __name__ == "__main__":
    main()
