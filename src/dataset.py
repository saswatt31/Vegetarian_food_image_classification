"""Shared dataset + model definitions for the vegetarian food classifier."""
import json
import os

import torch
import torch.nn as nn
from torchvision import datasets, models, transforms

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
MODELS = os.path.join(BASE, "models")
RESULTS = os.path.join(BASE, "results")

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]
INPUT_SIZE = 224

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# class -> meal category (only categories that make sense for these dishes)
CATEGORY_OF = {
    "idli": "Breakfast",
    "masala_dosa": "Breakfast",
    "dhokla": "Breakfast",          # steamed gram-flour cakes, eaten at breakfast/tea
    "pakode": "Snack",
    "samosa": "Snack",
    "pav_bhaji": "Main Meal",
    "kadai_paneer": "Main Meal",
    "chapati": "Main Meal",
}

# realistic mobile-photo augmentation (train) / deterministic (eval)
train_transform = transforms.Compose([
    transforms.RandomResizedCrop(INPUT_SIZE, scale=(0.7, 1.0)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(10),
    transforms.ColorJitter(0.15, 0.15, 0.1),
    transforms.ToTensor(),
    transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
])

eval_transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(INPUT_SIZE),
    transforms.ToTensor(),
    transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
])


def build_model(num_classes: int) -> nn.Module:
    """ImageNet-pretrained ResNet-18 with a fresh head; backbone frozen here."""
    model = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
    for p in model.parameters():
        p.requires_grad = False
    model.fc = nn.Linear(model.fc.in_features, num_classes)
    return model


def unfreeze_late_layers(model: nn.Module) -> None:
    """Stage-2 fine-tuning: unfreeze layer3 + layer4 (plus head)."""
    for name in ("layer3", "layer4"):
        for p in getattr(model, name).parameters():
            p.requires_grad = True


def make_loaders(batch_size: int = 32, num_workers: int = 2):
    train_ds = datasets.ImageFolder(os.path.join(DATA, "train"), train_transform)
    val_ds = datasets.ImageFolder(os.path.join(DATA, "validation"), eval_transform)
    test_ds = datasets.ImageFolder(os.path.join(DATA, "test"), eval_transform)

    train_dl = torch.utils.data.DataLoader(train_ds, batch_size=batch_size,
                                           shuffle=True, num_workers=num_workers)
    val_dl = torch.utils.data.DataLoader(val_ds, batch_size=batch_size,
                                         shuffle=False, num_workers=num_workers)
    test_dl = torch.utils.data.DataLoader(test_ds, batch_size=batch_size,
                                          shuffle=False, num_workers=num_workers)
    return train_dl, val_dl, test_dl, train_ds.classes


def save_class_names(classes):
    os.makedirs(MODELS, exist_ok=True)
    with open(os.path.join(MODELS, "class_names.json"), "w", encoding="utf-8") as f:
        json.dump({"classes": classes,
                   "category_of": CATEGORY_OF}, f, indent=1)
