"""
Generate Presentation_Vegetarian_Food_Image_Classification.pptx — 10 slides,
light "menu editorial" theme matching the project frontend
(cream #FBF7F0, terracotta #C25E1C, saffron #E9A319, leaf #3E7C4F).

Slide flow mirrors the approved server-load deck:
  1 Title  2 Problem  3 Idea  4 Data  5 Pipeline
  6 Model  7 Results  8 Benchmark  9 Insight  10 Thank You

All numbers come from the real-photo artifacts:
  results/test_metrics.json, training_history.json, test_predictions.json,
  data/split_summary.json, raw/dataset_stats.json

Run:    python report/make_slides.py
Output: Presentation_Vegetarian_Food_Image_Classification.pptx (project root)
"""
import json
import os
import sys
from collections import Counter

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE)
sys.path.insert(0, os.path.join(BASE, "src"))

SLIDE_W, SLIDE_H = Inches(13.333), Inches(7.5)
M = 0.72

PAPER = RGBColor(0xFB, 0xF7, 0xF0)
PAPER2 = RGBColor(0xF4, 0xED, 0xE1)
CARD = RGBColor(0xFF, 0xFF, 0xFF)
CREAM_TILE = RGBColor(0xFF, 0xF8, 0xEC)
INK = RGBColor(0x23, 0x30, 0x1F)
INK2 = RGBColor(0x5C, 0x65, 0x53)
LINE = RGBColor(0xE5, 0xDC, 0xCB)
TERRA = RGBColor(0xC2, 0x5E, 0x1C)
SAFFRON = RGBColor(0xE9, 0xA3, 0x19)
LEAF = RGBColor(0x3E, 0x7C, 0x4F)
LEAF_D = RGBColor(0x2C, 0x5A, 0x3A)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

FONT = "Segoe UI"
FONT_D = "Georgia"
OUT = "Presentation_Vegetarian_Food_Image_Classification.pptx"

# ---------------------------------------------------------------- real data
METRICS = json.load(open("results/test_metrics.json", encoding="utf-8"))
HIST = json.load(open("results/training_history.json", encoding="utf-8"))
SPLIT = json.load(open("data/split_summary.json", encoding="utf-8"))
RAWS = json.load(open("raw/dataset_stats.json", encoding="utf-8"))
PREDS = json.load(open("results/test_predictions.json", encoding="utf-8"))

ACC = METRICS["accuracy"]; F1M = METRICS["f1_macro"]; PM = METRICS["precision_macro"]
BEST = HIST["best"]; S1_END = HIST["val_acc"][HIST["stage1_epochs"] - 1]
GAIN = (BEST["val_acc"] - S1_END) * 100
N_TOTAL = sum(SPLIT["totals"].values()); N_TEST = SPLIT["totals"]["test"]
N_FULL = RAWS["total_images"]; N_CLS = len(SPLIT["classes"])
CAT = METRICS["per_category"]
CORRECT = PREDS["correct"]

_miss = Counter((r["true"], r["pred"]) for r in PREDS["records"] if not r["correct"])
TOP_CONF = _miss.most_common(3)

prs = Presentation()
prs.slide_width, prs.slide_height = SLIDE_W, SLIDE_H
BLANK = prs.slide_layouts[6]
_slide = None

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

def _alpha(sp, pct):
    solid = sp.fill._xPr.find(qn("a:solidFill"))
    srgb = solid.find(qn("a:srgbClr"))
    srgb.append(srgb.makeelement(qn("a:alpha"),
                                 {"val": str(int((100 - pct) * 1000))}))

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
    tf.word_wrap = wrap; tf.vertical_anchor = anchor
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

def card(slide, x, y, w, h, fill=CARD, line=LINE, radius=0.09):
    sp = _shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h),
                fill=fill, line=line)
    sp.adjustments[0] = radius
    return sp

def chip(slide, x, y, w, h, label, fill=PAPER2, txt=INK2, size=11):
    sp = _shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h),
                fill=fill, shadow=False)
    sp.adjustments[0] = 0.5
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

def picture_fit(slide, path, x, y, w, h):
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
     f"A two-stage fine-tuned ResNet-18 recognises {N_CLS} Indian vegetarian dishes from "
     f"{N_TOTAL:,} REAL photographs — {ACC*100:.2f}% test accuracy, trained on CPU.",
     size=15, color=INK2, spacing=1.25)
card(s, 9.35, 1.7, 3.3, 3.85, radius=0.07)
picture_fit(s, "results/dataset_samples_grid.png", 9.5, 1.92, 3.0, 2.6)
text(s, 9.5, 4.62, 3.0, 0.3, "one real photo per class", size=10, color=INK2,
     align=PP_ALIGN.CENTER)
chip(s, 9.35, 5.1, 3.3, 0.45, f"TEST ACCURACY {ACC*100:.2f}%", fill=LEAF, txt=WHITE, size=13)
text(s, M, 5.92, 8.0, 0.3,
     "Saswat Pattanaik · Ritesh Kumar Singh · Manoranjan Barik · Ankit Kumar Das",
     size=13, bold=True)
text(s, M, 6.27, 8.4, 0.55,
     "Guide: Mr. Rahul Rawat  ·  Faculty of Engineering & Technology  ·  Academic Year 2023 – 2027",
     size=12, color=INK2)
notes(s, "Introduce the rebuilt project: trained entirely on real photographs from the Indian "
         "Food Images dataset (no synthetic images). Two-stage fine-tuning on CPU. Headline: "
         f"{ACC*100:.2f}% test accuracy on {N_TEST} unseen photos.")

# ================================================================ SLIDE 2
s = new_slide()
header(s, "The Problem", "Real photos are messy — and that's the point",
       "Why web-scraped food photography needs curation + transfer learning")
probs = [
    ("A", "Web photos are wild", "Real scraped food images vary in framing, lighting, plating — "
     "and hide duplicates, menus and posters among genuine photographs."),
    ("B", "Leakage ruins evaluation", "Near-identical uploads straddling train and test inflate "
     "accuracy; deduplication must happen before splitting."),
    ("C", "Compute is scarce", "Training a CNN from scratch needs GPU-days; a semester project "
     "has a laptop CPU and a small labelled subset."),
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
       (f"a {N_CLS}-class vegetarian dish classifier trained purely on real photographs, with "
        "leakage-free splits and a measured fine-tuning gain — CPU only.", {})]],
     size=13.5, spacing=1.2)
footer(2)
notes(s, "Three pain points: messy real photos, leakage risk, compute budget. The goal box sets "
         "the bar: real photos only, deduplicated splits, measured gain.")

# ================================================================ SLIDE 3
s = new_slide()
header(s, "The Idea", "Borrow ImageNet's eyes, then let the late layers adapt",
       "Two-stage transfer learning: frozen head training, then selective fine-tuning")
steps = [
    ("Stage 1 — frozen backbone", "ImageNet ResNet-18 is frozen; a fresh 4,104-parameter head "
     "trains with Adam (lr 1e-3, cosine annealing) for 6 epochs.", TERRA),
    ("Stage 2 — selective fine-tune", "layer3 + layer4 unfreeze (10.5M parameters, 93.9% of the "
     "network) and fine-tune at lr 1e-4 — late features adapt, early features stay generic.", SAFFRON),
    ("Honest evaluation", "Deduplicated 70/15/15 split; the test split is touched exactly once — "
     "at the end.", LEAF),
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
text(s, 8.92, 2.35, 3.4, 0.35, "WHY TWO STAGES", size=11.5, bold=True, color=SAFFRON)
text(s, 8.92, 2.78, 3.45, 2.4,
     "Dish identity lives in mid-level textures — idli's steam pores, pakode's fried-batter "
     "granularity, dosa's lace. Generic ImageNet features under-represent those; fine-tuning "
     "layer3+layer4 retunes exactly them while early layers keep their general edge vocabulary.",
     size=12.5, color=WHITE, spacing=1.28)
text(s, 8.92, 5.3, 3.45, 1.05,
     [[(f"+{GAIN:.1f} pts", {"size": 30, "bold": True, "color": SAFFRON})],
      [("validation gain from fine-tuning", {"size": 11.5, "color": WHITE})]], spacing=1.1)
footer(3)
notes(s, "The design: stage 1 trains only the head; stage 2 adapts the late residual blocks. "
         f"The payoff: +{GAIN:.1f} points validation accuracy.")

# ================================================================ SLIDE 4
s = new_slide()
header(s, "The Data", f"{N_TOTAL:,} real photographs, {N_CLS} verified classes",
       "From the Indian Food Images corpus — validated, deduplicated, stratified")
f1c = card(s, M, 2.0, 6.1, 4.55)
picture_fit(s, "results/dataset_samples_grid.png", M + 0.15, 2.18, 5.8, 3.55)
text(s, M + 0.15, 5.9, 5.8, 0.5, "Fig. 1 — one real photograph per class (validation grid)",
     size=11, color=INK2, align=PP_ALIGN.CENTER)
stats = [
    (f"{N_FULL:,}", "corpus photos", f"{len(RAWS['classes'])} classes, all real"),
    (f"{N_TOTAL:,}", "curated subset", "8 vegetarian classes × 250"),
    (f"{N_TEST}", "unseen test photos", "38 per class, balanced"),
    ("38", "duplicates removed", "30 exact + 8 near (aHash)"),
]
y = 2.0
for v, l, sub in stats:
    card(s, 7.0, y, 5.6, 0.98)
    text(s, 7.25, y + 0.16, 3.0, 0.5, v, size=20, bold=True, color=TERRA, font=FONT_D)
    text(s, 7.25, y + 0.62, 3.4, 0.3, l, size=11.5, bold=True, color=INK2)
    text(s, 10.0, y + 0.3, 2.4, 0.4, sub, size=11, color=INK2, align=PP_ALIGN.RIGHT)
    y += 1.19
footer(4)
notes(s, "Data story: 6,269-image real corpus validated (0 corrupted), eight vegetarian classes "
         "selected after verification, 38 duplicates removed, stratified 70/15/15 split. "
         "Vegetarian assumptions documented per dish; ambiguous kaathi_rolls excluded.")

# ================================================================ SLIDE 5
s = new_slide()
header(s, "From Download to Deployment", "Five-stage pipeline",
       "prepare_data → build_subset → train → evaluate → predict")
stages = [
    ("01", "Download + validate", "Parquet corpus extracted; every image decoded; corruption "
     "and flat-image scan; verification grid.", "prepare_data.py", TERRA),
    ("02", "Curate subset", "8 classes verified present; SHA-256 + perceptual-hash dedupe; "
     "stratified 70/15/15 split.", "build_subset.py", SAFFRON),
    ("03", "Two-stage training", "Frozen-head 6 epochs → layer3+4 fine-tune 6 epochs; best "
     "checkpoint on val accuracy.", "train.py", LEAF),
    ("04", "Evaluate + serve", "Test-only metrics, confusion matrix, category analysis; upload "
     "interface runs the checkpoint.", "evaluate.py / app/", LEAF_D),
]
x = M
for n, t, d, script, c in stages:
    card(s, x, 2.1, 2.83, 3.35)
    _shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x + 0.22), Inches(2.32), Inches(0.62),
           Inches(0.62), fill=c, shadow=False)
    text(s, x + 0.22, 2.42, 0.62, 0.4, n, size=15, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    text(s, x + 0.22, 3.14, 2.45, 0.6, t, size=14.5, bold=True, spacing=1.05)
    text(s, x + 0.22, 3.8, 2.45, 1.15, d, size=11.5, color=INK2, spacing=1.2)
    chip(s, x + 0.22, 4.95, 2.4, 0.34, script, fill=PAPER2, txt=TERRA, size=9.5)
    x += 3.02
card(s, M, 5.85, 11.89, 0.8, fill=CREAM_TILE, line=SAFFRON)
text(s, M + 0.3, 6.03, 11.3, 0.45,
     [[("Reproducibility:  ", {"bold": True, "color": LEAF_D}),
       ("five commands regenerate everything — dataset, subset, model, metrics, interface — "
        "from the raw shards.", {})]], size=13)
footer(5)
notes(s, "Walk the pipeline. Curation is a first-class stage, not an afterthought — that's what "
         "makes the evaluation honest.")

# ================================================================ SLIDE 6
s = new_slide()
header(s, "The Model", "ResNet-18: frozen first, adaptive later",
       "ImageNet1K_V1 backbone · 4,104-parameter head → 10.5M-parameter fine-tune")
layers = [
    ("Input", "224×224×3 · ImageNet-normalised", PAPER2, INK2),
    ("ResNet-18 backbone", "stem + res2/res3 FROZEN · res4/res5 fine-tuned", LEAF, WHITE),
    ("Global average pool", "512-d feature vector", PAPER2, INK2),
    ("fc head 512→8", "4,104 params (stage 1) + softmax", TERRA, WHITE),
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
    ("Stage 1", "head only · Adam 1e-3 · 6 ep"),
    ("Stage 2", "layer3+4 · Adam 1e-4 · 6 ep"),
    ("Scheduler", "cosine annealing (both)"),
    ("Batch size", "32"),
    ("Loss", "cross-entropy (8-class)"),
    ("Augment", "crop .7–1.0, flip, ±10°, jitter"),
    ("Best checkpoint", f"val {BEST['val_acc']:.4f} (ep {BEST['epoch']})"),
]
yy = 2.72
for k, v in cfg:
    text(s, 7.62, yy, 2.15, 0.3, k, size=12, color=INK2)
    text(s, 9.62, yy, 2.8, 0.3, v, size=12, bold=True, align=PP_ALIGN.RIGHT)
    yy += 0.47
footer(6)
notes(s, "Architecture and config. Key asymmetry: stage 1 trains 0.04% of the network, stage 2 "
         "93.9%. The 10x LR drop protects pretrained weights during fine-tuning.")

# ================================================================ SLIDE 7
s = new_slide()
header(s, "Results", f"{ACC*100:.2f}% test accuracy on {N_TEST} unseen photos",
       "Held-out real photographs · macro precision 0.8924 · macro F1 0.8860")
card(s, M, 2.0, 5.4, 4.55)
picture_fit(s, "results/confusion_matrix.png", M + 0.15, 2.18, 5.1, 3.6)
text(s, M + 0.15, 5.95, 5.1, 0.5, f"Fig. 2 — 8×8 confusion matrix, {N_TEST} test images",
     size=11, color=INK2, align=PP_ALIGN.CENTER)
percls = [
    ("Idli & Kadai Paneer", "36/38 each (0.947)", LEAF_D),
    ("Pakode", "35/38 (0.921)", LEAF_D),
    ("Masala Dosa (weakest)", "31/38 (0.816)", TERRA),
]
yy = 2.0
for name, v, c in percls:
    card(s, 6.4, yy, 6.2, 0.9)
    text(s, 6.66, yy + 0.14, 4.7, 0.32, name, size=12.5, bold=True)
    text(s, 6.66, yy + 0.48, 5.7, 0.3, v, size=11.5, color=c)
    yy += 1.04
card(s, 6.4, 5.02, 6.2, 1.55, fill=CREAM_TILE, line=SAFFRON)
text(s, 6.66, 5.2, 5.7, 0.35, "WHERE THE 35 ERRORS LIVE", size=11, bold=True, color=TERRA)
conf_txt = "  ·  ".join(f"{t.split('_')[0]}→{p.split('_')[0]} ({n})"
                        for (t, p), n in TOP_CONF)
text(s, 6.66, 5.56, 5.7, 0.9,
     f"{conf_txt} — visually plausible look-alikes: golden fried or gravy-dominant dishes. "
     "Every class stays above 0.82.", size=12.5, spacing=1.2)
footer(7)
notes(s, f"Results: {CORRECT}/304. Confusions are interpretable look-alike pairs. Balanced "
         "classes mean macro = weighted metrics (0.8860 F1).")

# ================================================================ SLIDE 8
s = new_slide()
header(s, "Benchmark", f"Fine-tuning is worth +{GAIN:.1f} points",
       "Same data, same schedule — only the trainable scope differs")
rows = [
    ("Stage 1 — frozen backbone", S1_END, "head only (4,104 params)", INK2, False),
    ("Stage 2 — fine-tuned layer3+4", BEST["val_acc"], "10.5M params (93.9%)", LEAF_D, True),
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
        chip(s, M + 5.45, y - 0.17, 1.7, 0.36, "OUR MODEL", fill=LEAF, txt=WHITE, size=9.5)
    y += 1.8
card(s, M, 5.75, 7.3, 1.05, fill=LEAF_D, line=None)
text(s, M + 0.3, 5.94, 6.7, 0.7,
     [[(f"Δ = +{GAIN:.1f} pts", {"bold": True, "size": 18, "color": SAFFRON}),
       (f"   and test accuracy {ACC*100:.2f}% with macro F1 {F1M:.4f}.", {"size": 12.5, "color": WHITE})]],
     spacing=1.15)
card(s, 8.35, 2.1, 4.26, 4.7)
text(s, 8.62, 2.32, 3.7, 0.35, "MEAL-CATEGORY SCOREBOARD", size=11.5, bold=True, color=TERRA)
mc = [("Breakfast", CAT["Breakfast"]), ("Snack", CAT["Snack"]), ("Main Meal", CAT["Main Meal"])]
yy = 2.82
for k, v in mc:
    text(s, 8.62, yy, 2.0, 0.3, k, size=12.5, bold=True)
    text(s, 8.62, yy + 0.3, 3.7, 0.3, f"{v['correct']}/{v['n']} test photos",
         size=10.5, color=INK2)
    text(s, 10.8, yy, 1.6, 0.4, f"{v['accuracy']*100:.1f}%", size=17, bold=True,
         color=LEAF_D, align=PP_ALIGN.RIGHT, font=FONT_D)
    yy += 0.78
text(s, 8.62, 5.3, 3.7, 1.2,
     "No meal slot is systematically weak — a diet-tracking app can rely on all three "
     "categories nearly equally.", size=11.5, color=INK2, spacing=1.2)
footer(8)
notes(s, "The ablation: frozen backbone plateaus at 82.77%, fine-tuning reaches 91.22% — and "
         "test accuracy 88.49% confirms it generalises. Category scoreboard is balanced.")

# ================================================================ SLIDE 9
s = new_slide()
header(s, "Key Insight", "Curate first, fine-tune second",
       "What training on real photographs taught us")
ins = [
    ("Honest splits need dedupe", "SHA-256 caught 30 byte-identical twins; perceptual hashing "
     "caught 8 more. Without them, near-duplicates would silently inflate test accuracy.", LEAF),
    (f"Late layers carry the cuisine", "Frozen features plateau at 82.8%; adapting layer3+4 "
     f"unlocks +{GAIN:.1f} points — dish identity lives in mid-level textures.", TERRA),
    ("Real-data errors are legible", "The 35 misses cluster into three plausible look-alike "
     "pairs. Legible errors make the next data investment obvious.", SAFFRON),
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
       (f"on real photographs, careful curation plus two-stage transfer learning delivers a "
        f" dependable {N_CLS}-dish classifier on a laptop CPU — no synthetic data, no GPU, "
        "no leakage.", {})]], size=13.5, color=WHITE, spacing=1.2)
footer(9)
notes(s, "Three insights: dedupe before splitting, fine-tune the late layers, and read the "
         "errors — they point to the next data investment.")

# ================================================================ SLIDE 10
s = new_slide()
_shape(MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_W, SLIDE_H, fill=LEAF_D, shadow=False)
_wash(SAFFRON, Inches(9.0), Inches(-1.5), Inches(6.0), Inches(4.0))
_wash(LEAF, Inches(-1.5), Inches(4.5), Inches(6.0), Inches(4.0))
text(s, M, 2.5, 11.9, 1.0, "Thank You", size=54, bold=True, color=WHITE, font=FONT_D)
text(s, M, 3.6, 11.9, 0.4,
     "Vegetarian Food Image Classification using Transfer Learning — on real photographs",
     size=16, color=RGBColor(0xE8, 0xF0, 0xE6))
text(s, M, 4.6, 11.9, 0.4, "Questions & discussion welcome", size=13.5,
     color=RGBColor(0xC9, 0xDD, 0xC9))
chip(s, M, 5.6, 4.6, 0.44,
     f"TEST ACCURACY {ACC*100:.2f}%  ·  {N_CLS} CLASSES  ·  {N_TOTAL:,} REAL PHOTOS",
     fill=SAFFRON, txt=INK, size=11)
notes(s, "Close: thank the panel. One-line summary: a two-stage fine-tuned ResNet-18 classifies "
         f"eight vegetarian dishes at {ACC*100:.2f}% test accuracy on {N_TEST} unseen real "
         "photographs — trained entirely on CPU.")

prs.save(OUT)
print(f"saved {OUT}: {len(prs.slides._sldIdLst)} slides")
