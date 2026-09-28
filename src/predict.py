"""
Predict the class of a single uploaded food photograph.

Usage:
    python src/predict.py path/to/photo.jpg
Output (JSON on stdout):
    {"prediction": "masala_dosa", "confidence": 0.874,
     "top3": [{"class": "...", "prob": 0.87}, ...]}
"""
import argparse
import json
import os
import sys

import torch
from PIL import Image

from dataset import DEVICE, MODELS, build_model, eval_transform


def load_model():
    ckpt = torch.load(os.path.join(MODELS, "best_model.pth"),
                      map_location=DEVICE, weights_only=False)
    classes = ckpt["classes"]
    model = build_model(len(classes))
    model.load_state_dict(ckpt["model_state"])
    model.to(DEVICE).eval()
    return model, classes


def predict_image(path):
    model, classes = load_model()
    with Image.open(path) as im:
        im = im.convert("RGB")
        x = eval_transform(im).unsqueeze(0).to(DEVICE)
    with torch.no_grad():
        prob = torch.softmax(model(x), dim=1)[0]
    top = prob.topk(3)
    top3 = [{"class": classes[i], "prob": round(float(v), 4)}
            for v, i in zip(top.values, top.indices)]
    return {"prediction": top3[0]["class"], "confidence": top3[0]["prob"],
            "top3": top3}


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    args = ap.parse_args()
    print(json.dumps(predict_image(args.image), indent=1))
