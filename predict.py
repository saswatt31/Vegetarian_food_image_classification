"""
Predict the class of a single food image.

Usage:
    python predict.py path/to/image.jpg
    python predict.py data/test/samosa/samosa_001.png
"""
import argparse

import torch
from PIL import Image
from torchvision import transforms

from train import DEVICE, IMAGENET_MEAN, IMAGENET_STD

TF = transforms.Compose([
    transforms.Resize(256), transforms.CenterCrop(224), transforms.ToTensor(),
    transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--model", default="outputs/best_model.pth")
    args = ap.parse_args()

    ckpt = torch.load(args.model, map_location=DEVICE, weights_only=False)
    classes = ckpt["classes"]

    import torch.nn as nn
    from torchvision import models
    model = models.resnet18(weights=None)
    model.fc = nn.Linear(model.fc.in_features, len(classes))
    model.load_state_dict(ckpt["model_state"])
    model.to(DEVICE).eval()

    img = Image.open(args.image).convert("RGB")
    x = TF(img).unsqueeze(0).to(DEVICE)
    with torch.no_grad():
        probs = torch.softmax(model(x)[0], dim=0)

    top = probs.topk(3)
    print(f"prediction for {args.image}:")
    for p, i in zip(top.values.tolist(), top.indices.tolist()):
        print(f"  {classes[i]:<15} {p:.3f}")


if __name__ == "__main__":
    main()
