"""
Transfer learning: ResNet-18 (ImageNet weights) -> vegetarian food classes.

Default: freeze the convolutional backbone, train a new classification head.
Pass --finetune to unfreeze layer3+layer4 with a lower learning rate.
"""
import argparse
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


def loaders(data_dir: str, batch_size: int):
    train_tf = transforms.Compose([
        transforms.RandomResizedCrop(224, scale=(0.7, 1.0)),
        transforms.RandomHorizontalFlip(),
        transforms.ColorJitter(0.15, 0.15, 0.15),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])
    eval_tf = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])
    train = datasets.ImageFolder(os.path.join(data_dir, "train"), train_tf)
    val = datasets.ImageFolder(os.path.join(data_dir, "val"), eval_tf)
    train_dl = DataLoader(train, batch_size=batch_size, shuffle=True,
                          num_workers=0)
    val_dl = DataLoader(val, batch_size=batch_size, shuffle=False,
                        num_workers=0)
    return train_dl, val_dl, train.classes


def build_model(num_classes: int, finetune: bool) -> nn.Module:
    model = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
    for p in model.parameters():
        p.requires_grad = False
    if finetune:  # unfreeze the deeper blocks with the head
        for p in model.layer3.parameters():
            p.requires_grad = True
        for p in model.layer4.parameters():
            p.requires_grad = True
    model.fc = nn.Linear(model.fc.in_features, num_classes)
    return model.to(DEVICE)


def run_one_epoch(model, dl, criterion, optimizer=None):
    training = optimizer is not None
    model.train() if training else model.eval()
    total, correct, loss_sum = 0, 0, 0.0
    with torch.set_grad_enabled(training):
        for x, y in dl:
            x, y = x.to(DEVICE), y.to(DEVICE)
            logits = model(x)
            loss = criterion(logits, y)
            if training:
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
            loss_sum += loss.item() * y.size(0)
            total += y.size(0)
            correct += (logits.argmax(1) == y).sum().item()
    return loss_sum / total, correct / total


def main():
    ap = argparse.ArgumentParser(description="Train ResNet-18 food classifier")
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--epochs", type=int, default=6)
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--finetune", action="store_true",
                    help="unfreeze layer3/layer4 with lr/10")
    ap.add_argument("--out", default="outputs")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    train_dl, val_dl, classes = loaders(args.data_dir, args.batch_size)
    print(f"classes ({len(classes)}): {classes}")
    print(f"train={len(train_dl.dataset)}  val={len(val_dl.dataset)}  "
          f"device={DEVICE}")

    model = build_model(len(classes), args.finetune)
    head_params = [p for p in model.parameters() if p.requires_grad]
    print(f"trainable parameters: {sum(p.numel() for p in head_params):,}")

    criterion = nn.CrossEntropyLoss()
    lr = args.lr / 10 if args.finetune else args.lr
    optimizer = torch.optim.Adam(head_params, lr=lr)

    history = {"train_loss": [], "val_loss": [], "train_acc": [], "val_acc": []}
    best_acc = 0.0
    for epoch in range(1, args.epochs + 1):
        tr_loss, tr_acc = run_one_epoch(model, train_dl, criterion, optimizer)
        va_loss, va_acc = run_one_epoch(model, val_dl, criterion)
        history["train_loss"].append(tr_loss)
        history["val_loss"].append(va_loss)
        history["train_acc"].append(tr_acc)
        history["val_acc"].append(va_acc)
        marker = ""
        if va_acc > best_acc:
            best_acc = va_acc
            torch.save({"model_state": model.state_dict(), "classes": classes},
                       os.path.join(args.out, "best_model.pth"))
            marker = "  <- saved"
        print(f"epoch {epoch:02d} | train loss {tr_loss:.4f} acc {tr_acc:.4f} | "
              f"val loss {va_loss:.4f} acc {va_acc:.4f}{marker}")

    print(f"\nbest val accuracy: {best_acc:.4f}")

    # training curves
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    ax[0].plot(history["train_loss"], label="train")
    ax[0].plot(history["val_loss"], label="val")
    ax[0].set_title("Loss"); ax[0].set_xlabel("epoch"); ax[0].legend()
    ax[1].plot(history["train_acc"], label="train")
    ax[1].plot(history["val_acc"], label="val")
    ax[1].set_title("Accuracy"); ax[1].set_xlabel("epoch"); ax[1].legend()
    fig.tight_layout()
    fig.savefig(os.path.join(args.out, "training_curves.png"), dpi=140)
    print(f"saved {args.out}/training_curves.png and best_model.pth")


if __name__ == "__main__":
    main()
