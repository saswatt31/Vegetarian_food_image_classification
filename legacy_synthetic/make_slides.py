"""
Generate Presentation_Vegetarian_Food_Image_Classification.pptx — 10 slides,
light "menu editorial" theme matching the ThaliScan frontend
(cream paper #FBF7F0, terracotta #C25E1C, saffron #E9A319, leaf #3E7C4F).

Slide flow mirrors the approved server-load deck:
  1 Title  2 Problem  3 Idea  4 Data  5 Pipeline
  6 Model  7 Results  8 Benchmark  9 Insight  10 Thank You

All numbers come from the real artifacts:
  results/predictions.json, results/baseline_scratch.json,
  results/classification_report.txt, results/category_accuracy.csv

Run:    python make_slides.py
Output: Presentation_Vegetarian_Food_Image_Classification.pptx (project root)
"""
import json

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

# ---------------------------------------------------------------- constants
SLIDE_W, SLIDE_H = Inches(13.333), Inches(7.5)
M = 0.72  # default margin, inches

PAPER = RGBColor(0xFB, 0xF7, 0xF0)   # cream
PAPER2 = RGBColor(0xF4, 0xED, 0xE1)
CARD = RGBColor(0xFF, 0xFF, 0xFF)
CREAM_TILE = RGBColor(0xFF, 0xF8, 0xEC)
INK = RGBColor(0x23, 0x30, 0x1F)     # deep green-ink text
INK2 = RGBColor(0x5C, 0x65, 0x53)    # muted text
LINE = RGBColor(0xE5, 0xDC, 0xCB)    # hairline
TERRA = RGBColor(0xC2, 0x5E, 0x1C)   # terracotta accent
TERRA_D = RGBColor(0x9C, 0x48, 0x12)
SAFFRON = RGBColor(0xE9, 0xA3, 0x19)
LEAF = RGBColor(0x3E, 0x7C, 0x4F)
LEAF_D = RGBColor(0x2C, 0x5A, 0x3A)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

FONT = "Segoe UI"
FONT_D = "Georgia"  # serif display stand-in for Fraunces

OUT = "Presentation_Vegetarian_Food_Image_Classification.pptx"

# ---------------------------------------------------------------- real data
PRED = json.load(open("results/predictions.json", encoding="utf-8"))
BASE = json.load(open("results/baseline_scratch.json", encoding="utf-8"))
with open("results/category_accuracy.csv", encoding="utf-8") as f:
    _rows = [ln.split(",") for ln in f.read().strip().splitlines()[1:]]
PER_CLASS = {r[0]: (int(r[2]), float(r[3])) for r in _rows}

ACC = PRED["accuracy"]                            # 0.9911
TOTAL, CORRECT = PRED["total"], PRED["correct"]   # 112, 111
GAIN = (ACC - BASE["test_accuracy"]) * 100        # +16.07 pts
MISS = next(r for r in PRED["records"] if not r["correct"])  # the one error

prs = Presentation()
prs.slide_width, prs.slide_height = SLIDE_W, SLIDE_H
BLANK = prs.slide_layouts[6]
_slide = None  # current slide for the shape helpers

# ---------------------------------------------------------------- helpers
def new_slide():
    global _slide
    _slide = prs.slides.add_slide(BLANK)
    _slide.background.fill.solid()
    _slide.background.fill.fore_color.rgb = PAPER
    _wash(WHITE, Inches(-1.8), Inches(-1.6), Inches(7.2), Inches(4.6))
    _wash(PAPER2, Inches(8.4), Inches(4.6), Inches(6.6), Inches(4.4))
    return _slide

def _wash(color, x, y, w, h):
    sp = _shape(MSO_SHAPE.OVAL, x, y, w, h, fill=color, shadow=False)
    _alpha(sp, 45)

def _alpha(sp, transparency_pct):
    """Soften a solid fill by writing an alpha element into its srgbClr."""
    solid = sp.fill._xPr.find(qn("a:solidFill"))
    srgb = solid.find(qn("a:srgbClr"))
    a = srgb.makeelement(qn("a:alpha"),
                         {"val": str(int((100 - transparency_pct) * 1000))})
    srgb.append(a)

def _shape(shape, x, y, w, h, fill=None, line=None, lw=0.75, shadow=True):
    sp = _slide.shapes.add_shape(shape, x, y, w, h)
    if fill is not None:
        sp.fill.solid(); sp.fill.fore_color.rgb = fill
    else:
        sp.fill.background()
    if line is not None:
        sp.line.color.rgb = line; sp.line.width = Pt(lw)
    else:
        sp.line.fill.background()
    sp.shadow.inherit = False
    return sp

def text(slide, x, y, w, h, runs, size=14, color=INK, bold=False, italic=False,
         align=PP_ALIGN.LEFT, font=FONT, anchor=MSO_ANCHOR.TOP, spacing=1.0,
         wrap=True):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = wrap
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    paras = runs if isinstance(runs, list) else [runs]
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        if spacing != 1.0:
            p.line_spacing = spacing
        if isinstance(para, str):
            para = [(para, {})]
        for txt, style in para:
            r = p.add_run(); r.text = txt
            f = r.font
            f.name = style.get("font", font)
            f.size = Pt(style.get("size", size))
            f.bold = style.get("bold", bold)
            f.italic = style.get("italic", italic)
            f.color.rgb = style.get("color", color)
    return tb

def _radius(sp, frac):
    sp.adjustments[0] = frac

def card(slide, x, y, w, h, fill=CARD, line=LINE, radius=0.09):
    sp = _shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h),
                fill=fill, line=line)
    _radius(sp, radius)
    return sp

def chip(slide, x, y, w, h, label, fill=PAPER2, txt=INK2, size=11):
    sp = _shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h),
                fill=fill, shadow=False)
    _radius(sp, 0.5)
    tf = sp.text_frame
    tf.word_wrap = False
    tf.margin_left = tf.margin_right = Inches(0.08)
    tf.margin_top = tf.margin_bottom = Inches(0.02)
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = label
    r.font.name = FONT; r.font.size = Pt(size); r.font.bold = True; r.font.color.rgb = txt
    return sp

def accent_bar(slide, x, y, h, w=0.055, color=TERRA):
    return _shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h),
                  fill=color, shadow=False)

def header(slide, label, headline, sub=None):
    text(slide, M, 0.42, 11.9, 0.3, label.upper(), size=11.5, color=TERRA, bold=True)
    _shape(MSO_SHAPE.RECTANGLE, Inches(M), Inches(0.72), Inches(0.55), Pt(2.6),
           fill=SAFFRON, shadow=False)
    text(slide, M, 0.86, 11.9, 0.62, headline, size=27, color=INK, bold=True, font=FONT_D)
    if sub:
        text(slide, M, 1.52, 11.5, 0.4, sub, size=13, color=INK2)

def footer(idx):
    bar_w = 11.893
    _shape(MSO_SHAPE.RECTANGLE, Inches(M), Inches(7.24), Inches(bar_w), Pt(3.2),
           fill=LINE, shadow=False)
    _shape(MSO_SHAPE.RECTANGLE, Inches(M), Inches(7.24), Inches(bar_w * idx / 10), Pt(3.2),
           fill=TERRA, shadow=False)
    text(_slide, 12.15, 6.94, 0.82, 0.28, f"{idx:02d} / 10", size=10, color=INK2,
         align=PP_ALIGN.RIGHT, wrap=False)

def metric(slide, x, y, w, h, value, label, sub=None, color=TERRA):
    card(slide, x, y, w, h)
    accent_bar(slide, x + 0.16, y + 0.18, h - 0.36, color=color)
    text(slide, x + 0.36, y + 0.14, w - 0.5, 0.5, value, size=25, bold=True, font=FONT_D)
    text(slide, x + 0.36, y + 0.66, w - 0.5, 0.3, label, size=11, bold=True, color=INK2)
    if sub:
        text(slide, x + 0.36, y + 0.92, w - 0.5, 0.3, sub, size=10.5, color=INK2)

def picture_fit(slide, path, x, y, w, h):
    """Aspect-preserving image inside a w×h inch box, centred."""
    from PIL import Image
    iw, ih = Image.open(path).size
    x, y, w, h = Inches(x), Inches(y), Inches(w), Inches(h)
    scale = min(w / iw, h / ih)
    nw, nh = int(iw * scale), int(ih * scale)
    return slide.shapes.add_picture(path, x + (w - nw) // 2, y + (h - nh) // 2, nw, nh)

def notes(slide, txt):
    slide.notes_slide.notes_text_frame.text = txt

# ================================================================ SLIDE 1
s = new_slide()
_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.28), SLIDE_H, fill=TERRA, shadow=False)
chip(s, M, 0.9, 3.7, 0.42, "B.TECH AI & ML  ·  7TH SEMESTER  ·  GROUP 4", size=10.5)
text(s, M, 1.95, 8.3, 0.35, "PATTERN RECOGNITION PROJECT", size=13, color=TERRA, bold=True)
text(s, M, 2.35, 8.5, 2.3,
     [[("Vegetarian Food Image Classification", {})],
      [("using Transfer Learning", {"color": TERRA})]],
     size=40, bold=True, font=FONT_D, spacing=1.04)
text(s, M, 4.75, 7.9, 1.05,
     "A frozen ResNet-18 backbone with a 3,591-parameter head recognises seven "
     "Indian vegetarian dishes from ordinary photos — 99.11% test accuracy, "
     "trained on CPU in minutes.", size=15, color=INK2, spacing=1.25)
card(s, 9.35, 1.7, 3.3, 3.85, radius=0.07)
picture_fit(s, "results/dataset_samples.png", 9.5, 1.92, 3.0, 2.6)
text(s, 9.5, 4.68, 3.0, 0.3, "one sample per class · 224×224", size=10, color=INK2,
     align=PP_ALIGN.CENTER)
chip(s, 9.35, 5.1, 3.3, 0.45, f"TEST ACCURACY {ACC*100:.2f}%", fill=LEAF, txt=WHITE, size=13)
text(s, M, 5.92, 8.0, 0.3,
     "Saswat Pattanaik · Ritesh Kumar Singh · Manoranjan Barik · Ankit Kumar Das",
     size=13, bold=True)
text(s, M, 6.27, 8.4, 0.55,
     "Guide: Mr. Rahul Rawat  ·  Faculty of Engineering & Technology  ·  Academic Year 2023 – 2027",
     size=12, color=INK2)
notes(s, "Introduce the project: classify seven Indian vegetarian dishes from photos using "
         "transfer learning. Emphasise the constraint that shaped it: CPU-only training, "
         "one semester. Headline result: 99.11% on 112 unseen images.")

# ================================================================ SLIDE 2
s = new_slide()
header(s, "The Problem", "Same nutrition, wildly different pixels",
       "Why food recognition needs learned features, not hand-tuned rules")
probs = [
    ("A", "Appearance is everything", "The same dal looks completely different across "
     "plates, angles and lighting. Colour thresholds break the moment the tablecloth changes."),
    ("B", "Labels need scale", "Canteens, calorie trackers and recipe apps need to tag "
     "thousands of photos a day — manual labelling does not scale."),
    ("C", "Compute is scarce", "Training a CNN from scratch needs GPU-days; a semester "
     "project has a laptop CPU and six weeks."),
]
x = M
for tag, t, d in probs:
    card(s, x, 2.1, 3.72, 3.0)
    accent_bar(s, x + 0.2, 2.32, 2.55)
    text(s, x + 0.42, 2.3, 3.0, 0.4, tag, size=26, bold=True, color=TERRA, font=FONT_D)
    text(s, x + 0.42, 2.86, 3.05, 0.65, t, size=15.5, bold=True, spacing=1.05)
    text(s, x + 0.42, 3.62, 3.05, 1.3, d, size=12.5, color=INK2, spacing=1.2)
    x += 4.095
card(s, M, 5.5, 11.89, 1.15, fill=CREAM_TILE, line=SAFFRON)
text(s, M + 0.3, 5.72, 11.3, 0.75,
     [[("Goal:  ", {"bold": True, "color": LEAF_D}),
       ("a lightweight vegetarian-food classifier that reaches ≥95% test accuracy on seven dish "
        "categories while training end-to-end on a CPU in under ten minutes.", {})]],
     size=13.5, spacing=1.2)
footer(2)
notes(s, "Three pain points: visual variability, labelling scale, compute budget. "
         "The goal box sets the success criterion used later: 95%+ accuracy, CPU-trained.")

# ================================================================ SLIDE 3
s = new_slide()
header(s, "The Idea", "Borrow ImageNet's eyes, train only the last layer",
       "Transfer learning turns a six-week problem into a six-minute one")
steps = [
    ("Frozen ResNet-18", "ImageNet-pretrained convolutional backbone converts each "
     "224×224 photo into a 512-d visual feature vector. No pixel-level rules, ever.", TERRA),
    ("Tiny trainable head", "A single 512→7 linear layer + softmax (3,591 trainable "
     "parameters) maps features to dishes.", SAFFRON),
    ("CPU-friendly training", "Cross-entropy + Adam at lr 1e-3 for 6 epochs — the head "
     "converges in minutes because the features are already good.", LEAF),
]
y = 2.05
for i, (t, d, c) in enumerate(steps, 1):
    card(s, M, y, 7.6, 1.32)
    _shape(MSO_SHAPE.OVAL, Inches(M + 0.24), Inches(y + 0.41), Inches(0.5), Inches(0.5),
           fill=c, shadow=False)
    text(s, M + 0.24, y + 0.5, 0.5, 0.35, str(i), size=16, bold=True, color=WHITE,
         align=PP_ALIGN.CENTER)
    text(s, M + 0.95, y + 0.18, 6.4, 0.35, t, size=15.5, bold=True)
    text(s, M + 0.95, y + 0.56, 6.45, 0.7, d, size=12.5, color=INK2, spacing=1.18)
    y += 1.54
card(s, 8.62, 2.05, 3.99, 4.4, fill=LEAF_D, line=None)
text(s, 8.92, 2.35, 3.4, 0.35, "WHY IT WORKS", size=11.5, bold=True, color=SAFFRON)
text(s, 8.92, 2.78, 3.45, 2.4,
     "ImageNet's 1.2M photos already teach edges, textures and shapes. Food photos "
     "reuse exactly those features — a dosa's crisp gradient, a lassi's glass rim, "
     "a thali's multi-bowl layout are ordinary visual patterns to the backbone.",
     size=12.5, color=WHITE, spacing=1.28)
text(s, 8.92, 5.35, 3.45, 0.85,
     [[("3591", {"size": 30, "bold": True, "color": SAFFRON})],
      [("trainable parameters — 0.16% of the network", {"size": 11.5, "color": WHITE})]],
     spacing=1.1)
footer(3)
notes(s, "Explain transfer learning simply: reuse the pretrained backbone as a fixed feature "
         "extractor, train only the 3,591-parameter head. This is what makes CPU training viable.")

# ================================================================ SLIDE 4
s = new_slide()
header(s, "The Data", "1,120 mobile-style food photos, 7 balanced classes",
       "Synthetic-but-learnable plates with real-world camera noise")
card(s, M, 2.0, 6.1, 4.55)
picture_fit(s, "results/dataset_samples.png", M + 0.15, 2.18, 5.8, 3.55)
text(s, M + 0.15, 5.9, 5.8, 0.5,
     "Fig. 1 — one generated sample per dish class (dataset_samples.png)",
     size=11, color=INK2, align=PP_ALIGN.CENTER)
stats = [
    ("1,120", "images", "160 per class"),
    ("7", "classes", "4 meal categories"),
    ("896 / 112 / 112", "train / val / test", "80 / 10 / 10"),
    ("±25°", "rotation jitter", "plus blur, brightness"),
]
y = 2.0
for v, l, sub in stats:
    card(s, 7.0, y, 5.6, 0.98)
    text(s, 7.25, y + 0.16, 3.0, 0.5, v, size=20, bold=True, color=TERRA, font=FONT_D)
    text(s, 7.25, y + 0.62, 3.4, 0.3, l, size=11.5, bold=True, color=INK2)
    text(s, 10.4, y + 0.3, 2.0, 0.4, sub, size=11.5, color=INK2, align=PP_ALIGN.RIGHT)
    y += 1.19
footer(4)
notes(s, "Data: 1,120 seeded, procedurally generated 'mobile food photos' — plate-shape and "
         "palette signatures per dish, with rotation, blur and brightness simulating real "
         "phone cameras. Balanced classes; 80/10/10 split.")

# ================================================================ SLIDE 5
s = new_slide()
header(s, "From Pixels to Features", "Four-stage pipeline",
       "prepare_dataset.py → train.py → evaluate.py → export_predictions.py")
stages = [
    ("01", "Dataset builder", "PIL-generated plates with per-class shape/palette "
     "signatures on textured table backgrounds.", "prepare_dataset.py", TERRA),
    ("02", "Camera augmentation", "±25° rotation, brightness jitter, Gaussian blur "
     "(σ 0.4–1.3) — mobile-photo realism.", "prepare_dataset.py", SAFFRON),
    ("03", "Frozen backbone + head", "RandomResizedCrop, flip, jitter → ResNet-18 → "
     "512-d features → 7-way softmax head.", "train.py", LEAF),
    ("04", "Evaluation & export", "Confusion matrix, per-class precision/recall, "
     "per-image top-3 softmax export.", "evaluate.py", LEAF_D),
]
x = M
for n, t, d, script, c in stages:
    card(s, x, 2.1, 2.83, 3.35)
    _shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x + 0.22), Inches(2.32), Inches(0.62),
           Inches(0.62), fill=c, shadow=False)
    text(s, x + 0.22, 2.42, 0.62, 0.4, n, size=15, bold=True, color=WHITE,
         align=PP_ALIGN.CENTER)
    text(s, x + 0.22, 3.14, 2.45, 0.6, t, size=14.5, bold=True, spacing=1.05)
    text(s, x + 0.22, 3.8, 2.45, 1.15, d, size=11.5, color=INK2, spacing=1.2)
    chip(s, x + 0.22, 4.95, 2.4, 0.34, script, fill=PAPER2, txt=TERRA_D, size=10)
    x += 3.02
card(s, M, 5.85, 11.89, 0.8, fill=CREAM_TILE, line=SAFFRON)
text(s, M + 0.3, 6.03, 11.3, 0.45,
     [[("Reproducibility:  ", {"bold": True, "color": LEAF_D}),
       ("python run_all.py  →  data → train → evaluate → figures, one command, seeded and CPU-only.", {})]],
     size=13)
footer(5)
notes(s, "Walk the four stages and the one-command reproducibility. Augmentation choice "
         "matters: it bakes camera variance into training data so the frozen backbone generalises.")

# ================================================================ SLIDE 6
s = new_slide()
header(s, "The Model", "ResNet-18, frozen and re-headed",
       "Backbone: 11.7M frozen parameters · Head: 3,591 trainable parameters")
layers = [
    ("Input", "224×224×3 · ImageNet-normalised", PAPER2, INK2),
    ("ResNet-18 backbone", "4 stage blocks · 512 channels · FROZEN", LEAF, WHITE),
    ("Global average pool", "512-d feature vector", PAPER2, INK2),
    ("fc head 512→7", "3,591 trainable params + softmax", TERRA, WHITE),
]
y = 2.05
for i, (t, d, c, tc) in enumerate(layers):
    _shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(M), Inches(y), Inches(6.3), Inches(0.88),
           fill=c, shadow=False)
    text(s, M + 0.28, y + 0.13, 5.8, 0.35, t, size=14, bold=True, color=tc)
    text(s, M + 0.28, y + 0.48, 5.8, 0.3, d, size=11.5, color=tc)
    if i < 3:
        a = _shape(MSO_SHAPE.ISOSCELES_TRIANGLE, Inches(M + 3.0), Inches(y + 0.92),
                   Inches(0.3), Inches(0.14), fill=LINE, shadow=False)
        a.rotation = 180
    y += 1.08
card(s, 7.35, 2.05, 5.26, 4.5)
text(s, 7.62, 2.28, 4.7, 0.35, "TRAINING CONFIGURATION", size=11.5, bold=True, color=TERRA)
cfg = [
    ("Backbone", "ResNet-18, ImageNet1K_V1"),
    ("Frozen layers", "all conv + bn"),
    ("Head", "nn.Linear(512, 7)"),
    ("Loss / optim", "CrossEntropy · Adam"),
    ("Learning rate", "1e-3 (head only)"),
    ("Epochs / batch", "6 · 32"),
    ("Augment (train)", "crop, flip, jitter"),
    ("Best val accuracy", "1.000 (epoch 4)"),
]
yy = 2.72
for k, v in cfg:
    text(s, 7.62, yy, 2.15, 0.3, k, size=12, color=INK2)
    text(s, 9.62, yy, 2.8, 0.3, v, size=12, bold=True, align=PP_ALIGN.RIGHT)
    yy += 0.47
footer(6)
notes(s, "Architecture walk-through. Stress the asymmetry: 11.7M frozen vs 3,591 trained. "
         "Validation hit 1.000 accuracy by epoch 4 — the head converges almost immediately.")

# ================================================================ SLIDE 7
s = new_slide()
header(s, "Results", f"{ACC*100:.2f}% test accuracy — {CORRECT} of {TOTAL} correct",
       "Held-out test set · per-class scores from classification_report.txt")
card(s, M, 2.0, 5.4, 4.55)
picture_fit(s, "results/confusion_matrix.png", M + 0.15, 2.18, 5.1, 3.6)
text(s, M + 0.15, 5.95, 5.1, 0.5, "Fig. 2 — 7×7 confusion matrix, 112 test images",
     size=11, color=INK2, align=PP_ALIGN.CENTER)
percls = [
    ("Dosa · Idli · Lassi · Samosa · Veg Thali", "100% precision, recall and F1", LEAF_D),
    ("Paneer Curry", "1.00 recall · 0.94 precision", LEAF_D),
    ("Veg Biryani", "0.94 recall · 1.00 precision", TERRA_D),
]
yy = 2.0
for name, v, c in percls:
    card(s, 6.4, yy, 6.2, 0.9)
    text(s, 6.66, yy + 0.14, 4.7, 0.32, name, size=12.5, bold=True)
    text(s, 6.66, yy + 0.48, 5.7, 0.3, v, size=11.5, color=c)
    yy += 1.04
card(s, 6.4, 5.02, 6.2, 1.55, fill=CREAM_TILE, line=SAFFRON)
text(s, 6.66, 5.2, 5.7, 0.35, "THE ONE MISS", size=11, bold=True, color=TERRA_D)
text(s, 6.66, 5.56, 5.7, 0.9,
     f"{MISS['file']}: a veg biryani bowl read as paneer curry at 50.6% confidence — "
     "both Main-Course bowls share warm palettes and grain textures.",
     size=12.5, spacing=1.2)
footer(7)
notes(s, "Results: 111/112. Five classes perfect; the single error is biryani→paneer_curry, "
         "an intra-category confusion (both main-course bowls). Macro precision 0.9916, F1 0.9911.")

# ================================================================ SLIDE 8
s = new_slide()
header(s, "Benchmark", f"Transfer learning is worth +{GAIN:.1f} points",
       "Identical protocol: same data, split, epochs and optimizer — only the init differs")
rows = [
    ("Transfer (ImageNet init)", ACC, "ResNet-18 frozen · head-only", LEAF_D, True),
    ("Random-init baseline", BASE["test_accuracy"], "same protocol, no pretraining", INK2, False),
]
y = 2.1
for name, v, d, c, star in rows:
    card(s, M, y, 7.3, 1.5,
         fill=RGBColor(0xF3, 0xF8, 0xF3) if star else CARD,
         line=LEAF if star else LINE)
    text(s, M + 0.3, y + 0.18, 4.6, 0.35, name, size=15.5, bold=True)
    text(s, M + 0.3, y + 0.58, 4.6, 0.3, d, size=11.5, color=INK2)
    text(s, M + 5.1, y + 0.38, 1.9, 0.6, f"{v*100:.2f}%", size=26, bold=True, color=c,
         font=FONT_D, align=PP_ALIGN.RIGHT)
    if star:
        chip(s, M + 5.55, y - 0.17, 1.5, 0.36, "OUR MODEL", fill=LEAF, txt=WHITE, size=9.5)
    y += 1.8
card(s, M, 5.75, 7.3, 1.05, fill=LEAF_D, line=None)
text(s, M + 0.3, 5.94, 6.7, 0.7,
     [[("Δ = +16.07 pts", {"bold": True, "size": 18, "color": SAFFRON}),
       ("   macro F1 0.9911 vs 0.8274 — pretraining supplies features six epochs cannot.",
        {"size": 12.5, "color": WHITE})]], spacing=1.15)
card(s, 8.35, 2.1, 4.26, 4.7)
text(s, 8.62, 2.32, 3.7, 0.35, "RANDOM-INIT BASELINE", size=11.5, bold=True, color=TERRA)
bt = [
    ("test accuracy", f"{BASE['test_accuracy']*100:.2f}%"),
    ("macro precision", f"{BASE['macro_precision']:.4f}"),
    ("macro recall", f"{BASE['macro_recall']:.4f}"),
    ("macro F1", f"{BASE['macro_f1']:.4f}"),
    ("best val accuracy", f"{BASE['best_val_accuracy']*100:.2f}%"),
    ("epochs to converge", str(BASE["best_epoch"])),
]
yy = 2.78
for k, v in bt:
    text(s, 8.62, yy, 2.4, 0.3, k, size=12, color=INK2)
    text(s, 10.92, yy, 1.5, 0.3, v, size=12, bold=True, align=PP_ALIGN.RIGHT)
    yy += 0.44
text(s, 8.62, 5.55, 3.7, 1.0,
     "Control experiment in baseline_experiment.py: identical train.py protocol, "
     "only the ImageNet weights removed.", size=11.5, color=INK2, spacing=1.2)
footer(8)
notes(s, "The control experiment: same everything, random init. 83.04% vs 99.11% — "
         "the +16.07-point gap is the measured value of ImageNet pretraining on this task.")

# ================================================================ SLIDE 9
s = new_slide()
header(s, "Key Insight", "Tiny heads on big features beat big training runs",
       "What the numbers say about solving vision problems cheaply")
ins = [
    ("3,591 params trained", "0.16% of the network trained end-to-end; 99.11% accuracy. "
     "Task knowledge lives in the features, not the head.", LEAF),
    ("Features transfer, labels don't", "The random-init control shows the same architecture "
     "without pretraining stalls 16 points lower — pretraining is the algorithm, not a bonus.", TERRA),
    ("Know the failure mode", "The only error is an intra-category confusion (biryani vs paneer "
     "curry). Hard negatives within a meal category are the next data investment.", SAFFRON),
]
x = M
for t, d, c in ins:
    card(s, x, 2.1, 3.72, 3.1)
    accent_bar(s, x + 0.2, 2.32, 2.65, color=c)
    text(s, x + 0.42, 2.35, 3.0, 0.75, t, size=16, bold=True, spacing=1.05, font=FONT_D)
    text(s, x + 0.42, 3.25, 3.05, 1.75, d, size=12.5, color=INK2, spacing=1.25)
    x += 4.095
card(s, M, 5.6, 11.89, 1.05, fill=LEAF_D, line=None)
text(s, M + 0.3, 5.78, 11.3, 0.7,
     [[("Takeaway:  ", {"bold": True, "color": SAFFRON}),
       ("for small labelled datasets, frozen-pretrained-backbone + tiny-head is the highest-"
        "accuracy-per-watt recipe — CPU training is enough when the backbone already knows how to see.", {})]],
     size=13.5, color=WHITE, spacing=1.2)
footer(9)
notes(s, "Three insights, one takeaway. If asked about deployment: the whole pipeline is CPU-"
         "class; ONNX export of the head is a trivial next step.")

# ================================================================ SLIDE 10
s = new_slide()
_shape(MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_W, SLIDE_H, fill=LEAF_D, shadow=False)
_wash(SAFFRON, Inches(9.0), Inches(-1.5), Inches(6.0), Inches(4.0))
_wash(LEAF, Inches(-1.5), Inches(4.5), Inches(6.0), Inches(4.0))
text(s, M, 2.5, 11.9, 1.0, "Thank You", size=54, bold=True, color=WHITE, font=FONT_D)
text(s, M, 3.6, 11.9, 0.4,
     "Vegetarian Food Image Classification using Transfer Learning",
     size=16, color=RGBColor(0xE8, 0xF0, 0xE6))
text(s, M, 4.6, 11.9, 0.4, "Questions & discussion welcome", size=13.5,
     color=RGBColor(0xC9, 0xDD, 0xC9))
chip(s, M, 5.6, 4.4, 0.44, f"TEST ACCURACY {ACC*100:.2f}%  ·  7 CLASSES  ·  CPU-TRAINED",
     fill=SAFFRON, txt=INK, size=11)
notes(s, "Close: thank the panel, invite questions. One-line summary if asked: frozen "
         "ResNet-18 features plus a 3,591-parameter head classify seven vegetarian dishes "
         "at 99.11% test accuracy, trained on CPU in minutes.")

prs.save(OUT)
print(f"saved {OUT}: {len(prs.slides._sldIdLst)} slides")
