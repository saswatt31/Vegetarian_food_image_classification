"""
Minimal local server for the food-photo upload demo.

Serves app/index.html and exposes POST /predict:
  multipart form field "image" -> runs the trained ResNet on the upload,
  returns JSON {prediction, confidence, top3}.

Run:    python app/server.py            (default port 8000)
Then:   open http://localhost:8000 in a browser.
"""
import io
import json
import os
import re
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler

import torch
from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "src"))

from dataset import DEVICE, build_model, eval_transform  # noqa: E402

MODEL = None
CLASSES = None

def load_model():
    global MODEL, CLASSES
    ckpt = torch.load(os.path.join(BASE, "models", "best_model.pth"),
                      map_location=DEVICE, weights_only=False)
    CLASSES = ckpt["classes"]
    MODEL = build_model(len(CLASSES))
    MODEL.load_state_dict(ckpt["model_state"])
    MODEL.to(DEVICE).eval()

def predict_bytes(raw: bytes):
    im = Image.open(io.BytesIO(raw)).convert("RGB")
    x = eval_transform(im).unsqueeze(0).to(DEVICE)
    with torch.no_grad():
        prob = torch.softmax(MODEL(x), dim=1)[0]
    top = prob.topk(3)
    return {"prediction": CLASSES[int(top.indices[0])],
            "confidence": round(float(top.values[0]), 4),
            "top3": [{"class": CLASSES[int(i)], "prob": round(float(v), 4)}
                     for v, i in zip(top.values, top.indices)]}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=os.path.join(BASE, "app"), **kw)

    def do_POST(self):
        if self.path != "/predict":
            self.send_error(404)
            return
        ctype = self.headers.get("Content-Type", "")
        boundary = re.search(r"boundary=(.+)", ctype).group(1).encode()
        remain = int(self.headers["Content-Length"])
        body = self.rfile.read(remain)
        # extract the first file part's bytes
        parts = body.split(b"--" + boundary)
        img_bytes = None
        for part in parts:
            if b"filename=" in part:
                hdr_end = part.find(b"\r\n\r\n")
                img_bytes = part[hdr_end + 4:].rstrip(b"\r\n")
                break
        if not img_bytes:
            self._json(400, {"error": "no image field in form"})
            return
        try:
            result = predict_bytes(img_bytes)
            self._json(200, result)
        except Exception as e:  # noqa: BLE001
            self._json(500, {"error": str(e)[:200]})

    def _json(self, code, obj):
        payload = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *a):  # quieter
        pass


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print(f"loading model ...")
    load_model()
    print(f"serving on http://localhost:{port}  (Ctrl+C to stop)")
    HTTPServer(("127.0.0.1", port), Handler).serve_forever()
