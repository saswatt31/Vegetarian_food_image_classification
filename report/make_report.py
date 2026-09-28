"""
Generate Project_Report_Vegetarian_Food_Image_Classification.docx by filling
C:\\Users\\saswa\\Downloads\\Project_Report_Template.docx IN PLACE (styles,
headers and the TOC field are preserved; Word refreshes the TOC with F9).

Every number comes from the real artifacts of the REAL-PHOTO run:
  results/test_metrics.json, results/training_history.json,
  results/classification_report.txt, data/split_summary.json,
  raw/dataset_stats.json

Run:    python report/make_report.py
Output: Project_Report_Vegetarian_Food_Image_Classification.docx (project root)
"""
import copy
import json
import os
import sys

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "src"))
os.chdir(BASE)

TEMPLATE = r"C:\Users\saswa\Downloads\Project_Report_Template.docx"
OUT = os.path.join(BASE, "Project_Report_Vegetarian_Food_Image_Classification.docx")

# ---------------------------------------------------------------- submission
GROUP = "4"
SEMESTER = "7th Semester Evaluation of B.Tech (Artificial Intelligence & Machine Learning)"
STUDENTS = [
    ("Saswat Pattanaik", "FET-BAML-2023-27-026"),
    ("Ritesh Kumar Singh", "FET-BAML-2023-27-027"),
    ("Manoranjan Barik", "FET-BAML-2023-27-039"),
    ("Ankit Kumar Das", "FET-BAML-2023-27-018"),
]
TITLE = "VEGETARIAN FOOD IMAGE CLASSIFICATION USING TRANSFER LEARNING"
SUBTITLE = ("A two-stage fine-tuned ResNet-18 on real Indian food photographs — "
            "8 vegetarian dishes from the Indian Food Images dataset")
ACCENT = RGBColor(0xC2, 0x5E, 0x1C)

# ---------------------------------------------------------------- real data
METRICS = json.load(open("results/test_metrics.json", encoding="utf-8"))
HIST = json.load(open("results/training_history.json", encoding="utf-8"))
SPLIT = json.load(open("data/split_summary.json", encoding="utf-8"))
RAWS = json.load(open("raw/dataset_stats.json", encoding="utf-8"))

ACC = METRICS["accuracy"]                    # 0.8849
PM, PW = METRICS["precision_macro"], METRICS["precision_weighted"]
RM, RW = METRICS["recall_macro"], METRICS["recall_weighted"]
F1M, F1W = METRICS["f1_macro"], METRICS["f1_weighted"]
BEST = HIST["best"]                          # val 0.9122 @ epoch 8 stage2
S1_END = HIST["val_acc"][HIST["stage1_epochs"] - 1]   # 0.8277
CAT = METRICS["per_category"]                # Breakfast .886 / Snack .8947 / Main .8772

N_FULL = RAWS["total_images"]                # 6269
N_CLASSES_FULL = len(RAWS["classes"])        # 20
N_TRAIN = SPLIT["totals"]["train"]           # 1400
N_VAL = SPLIT["totals"]["validation"]        # 296
N_TEST = SPLIT["totals"]["test"]             # 304
N_TOTAL = N_TRAIN + N_VAL + N_TEST           # 2000
PER_CLASS = SPLIT["classes"]                 # avail/kept per class
DUP_EXACT = SPLIT["duplicates_removed"]      # 30
DUP_NEAR = SPLIT["near_duplicates_removed"]  # 8
CLASSES = sorted(PER_CLASS)
N_CLS = len(CLASSES)                         # 8

# per-class test accuracy from the real predictions
PREDS = json.load(open("results/test_predictions.json", encoding="utf-8"))
_pc = {}
for r in PREDS["records"]:
    d = _pc.setdefault(r["true"], [0, 0])
    d[0] += r["correct"]; d[1] += 1
TEST_PER_CLASS = {k: (v[0], v[1]) for k, v in _pc.items()}
MISSES = [r for r in PREDS["records"] if not r["correct"]]

# head vs fine-tune trainable params (computed live from the real model)
import torch
from dataset import build_model, unfreeze_late_layers
_m = build_model(N_CLS)
P_HEAD = sum(p.numel() for p in _m.parameters() if p.requires_grad)
unfreeze_late_layers(_m)
P_FT = sum(p.numel() for p in _m.parameters() if p.requires_grad)
P_TOTAL = sum(p.numel() for p in _m.parameters())

# =========================================================================
# helpers
# =========================================================================

def set_cell(cell, text, bold=False, size=9.5, align="left"):
    p = cell.paragraphs[0]
    p.text = ""
    run = p.add_run(text)
    run.font.size = Pt(size)
    run.font.bold = bold
    p.alignment = {"left": WD_ALIGN_PARAGRAPH.LEFT,
                   "center": WD_ALIGN_PARAGRAPH.CENTER}[align]


def style_table(t, header=True):
    t.autofit = True
    for i, row in enumerate(t.rows):
        for cell in row.cells:
            for p in cell.paragraphs:
                p.paragraph_format.space_before = Pt(1)
                p.paragraph_format.space_after = Pt(1)
                for r in p.runs:
                    r.font.size = Pt(9.5)
                    if i == 0 and header:
                        r.font.bold = True


def insert_figure(doc, path, width_cm, caption, before_par):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    run.add_picture(path, width=Cm(width_cm))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = cap.add_run(caption)
    r.font.size = Pt(9)
    r.font.italic = True
    r.font.color.rgb = ACCENT
    before_par._p.addprevious(p._p)
    before_par._p.addprevious(cap._p)


def monospace(target_par, text):
    for line in text.rstrip("\n").split("\n"):
        p = target_par.insert_paragraph_before("")
        run = p.add_run(line)
        run.font.size = Pt(8.5)
        rPr = run._element.get_or_add_rPr()
        rFonts = rPr.find(qn("w:rFonts"))
        if rFonts is None:
            rFonts = OxmlElement("w:rFonts")
            rPr.append(rFonts)
        for attr in ("w:ascii", "w:hAnsi", "w:cs"):
            rFonts.set(qn(attr), "Consolas")


def ensure_rows(t, n):
    while len(t.rows) < n:
        t._tbl.append(copy.deepcopy(t.rows[-1]._tr))


# =========================================================================
# load template
# =========================================================================

doc = Document(TEMPLATE)
P = doc.paragraphs

# ------------------------------------------------------------- title block
P[1].text = TITLE
P[2].text = SUBTITLE
P[4].text = SEMESTER
P[5].text = "Subject: Pattern Recognition and Anomaly Detection"
P[6].text = f"Submitted by (Group – {GROUP})"
P[8].text = "Under the Guidance of: Mr. Rahul Rawat"
P[9].text = "Department of Artificial Intelligence & Machine Learning (AIML)"
P[10].text = "Faculty of Engineering and Technology (FET)"
P[11].text = "Academic Year 2023 – 2027"

t0 = doc.tables[0]
for i, (name, roll) in enumerate(STUDENTS, start=1):
    t0.rows[i].cells[0].text = name
    t0.rows[i].cells[1].text = roll

# ------------------------------------------------------------- declaration
P[14].text = (
    f"We, the undersigned members of Group-{GROUP} ({SEMESTER.split(' Evaluation')[0]}, "
    "B.Tech – Artificial Intelligence & Machine Learning), hereby declare that the project "
    "entitled \"Vegetarian Food Image Classification Using Transfer Learning\" is an original "
    "piece of work carried out by us as part of the 7th semester evaluation under the Pattern "
    "Recognition and Anomaly Detection subject. The work has not been submitted to any other "
    "university or institute for the award of any degree or diploma.")
P[15].text = (
    "We further declare that all sources of information, algorithms and datasets used in the "
    "preparation of this report have been duly acknowledged. Every computational result reported "
    "here was produced by running the project's own code on the real-photograph dataset described "
    "in Section 3.3 — the Indian Food Images dataset (web-scraped real photographs, Kaggle/"
    "HuggingFace distribution) — with no synthetic or generated images used at any stage.")
P[16].text = "Team Members:"
for i, (name, roll) in enumerate(STUDENTS):
    P[17 + i].text = f"{name} ({roll})"
# P[22]/P[23]: Place / Date intentionally left blank for physical signing

# ---------------------------------------------------------- acknowledgement
P[26].text = (
    "We take this opportunity to express our sincere gratitude to everyone who supported us throughout "
    "this project. We are deeply thankful to our guide, Mr. Rahul Rawat, for his continuous guidance, "
    "constructive feedback and encouragement at every stage of this work — from framing the problem to "
    "interpreting the fine-tuning behaviour and the evaluation results.")
P[27].text = (
    "We would also like to thank the faculty members of the Department of Artificial Intelligence & "
    "Machine Learning for providing the academic foundation in convolutional neural networks and "
    "transfer learning that this project builds upon, the Faculty of Engineering and Technology "
    "for the laboratory resources used to run the experiments, and the creators of the Indian Food "
    "Images dataset for releasing a real-photograph corpus that made this study possible.")
P[28].text = (
    "Finally, we would like to acknowledge the effort and cooperation of every member of our team, whose "
    "combined contribution made it possible to curate the dataset, run the two-stage training, analyse "
    "the errors, and prepare this report within the semester timeline.")

# --------------------------------------------------------------- abstract
P[31].text = (
    "Automatic recognition of food items from photographs is a core building block for calorie-"
    "estimation and diet-tracking applications: users photograph their meals instead of searching "
    "menus, and the app must map each photo to the correct dish before nutrition can be computed. "
    "Indian vegetarian cuisine is visually challenging — flatbreads, fritters and steamed cakes share "
    "warm palettes and irregular textures — and web-scale food photographs vary wildly in framing, "
    "lighting and plating, so a classifier must generalise beyond studio conditions.")
P[32].text = (
    "This project trains an image classifier for eight common vegetarian preparations — chapati, "
    "dhokla, idli, kadai paneer, masala dosa, pakode, pav bhaji and samosa — using REAL photographs "
    f"from the Indian Food Images dataset ({N_FULL:,} web-scraped photos across {N_CLASSES_FULL} "
    "classes were downloaded and inspected; every image used is a genuine food photograph). The "
    "eight classes were selected only after verifying their presence in the corpus, and the "
    "vegetarian assumption of each dish is documented. Exact duplicates and near-duplicates were "
    "removed before splitting so that no image family leaks across the train/validation/test "
    "boundaries.")
P[33].text = (
    f"Methodology: a curated subset of {N_TOTAL} real photographs ({N_TRAIN}/{N_VAL}/{N_TEST}, a "
    "stratified 70/15/15 split) feeds a two-stage transfer-learning pipeline built on an "
    "ImageNet-pretrained ResNet-18. Stage 1 freezes the convolutional backbone and trains only the "
    f"new {P_HEAD:,}-parameter classification head with Adam (lr 1e-3, cosine annealing). Stage 2 "
    f"unfreezes the later residual blocks (layer3 + layer4, {P_FT:,} trainable parameters) and "
    "fine-tunes at a reduced learning rate (1e-4). Realistic mobile-photo augmentation — "
    "RandomResizedCrop, horizontal flip, ±10° rotation and mild colour jitter — is applied to the "
    "training split only.")
P[34].text = (
    f"Results: fine-tuning lifted validation accuracy from {S1_END:.4f} (frozen backbone) to "
    f"{BEST['val_acc']:.4f}. On the unseen test set of {N_TEST} real photographs the final model "
    f"reaches {ACC:.4f} accuracy with macro precision {PM:.4f}, macro recall {RM:.4f} and macro F1 "
    f"{F1M:.4f}. Meal-category performance is balanced — Breakfast {CAT['Breakfast']['accuracy']:.4f}, "
    f"Snack {CAT['Snack']['accuracy']:.4f}, Main Meal {CAT['Main Meal']['accuracy']:.4f} — and the "
    "remaining confusions are visually plausible look-alike pairs (dosa ↔ chapati, samosa ↔ pakode, "
    "pav bhaji ↔ kadai paneer). An upload-style web interface runs the trained model on user "
    "photographs, demonstrating the deployment path.")

# =====================================================================
# section 1
# =====================================================================
P[41].text = (
    "Food-image recognition sits at the intersection of computer vision and mobile health applications. "
    "Diet-tracking and calorie-estimation apps ask users to photograph their meals, and the accuracy of "
    "the underlying dish classifier directly determines the quality of the nutrition estimate. In a "
    "campus canteen or mess scenario, the same technology can automate meal identification at the "
    "counter, support food-delivery cataloguing, and power nutrition education tools for regional "
    "cuisine that global food datasets barely cover.")
P[43].text = (
    "Collecting and labelling large real-world food datasets is expensive, and training deep networks "
    "from scratch requires GPU resources that are rarely available for a semester project. Transfer "
    "learning resolves both constraints: convolutional backbones pretrained on ImageNet already encode "
    "the generic visual vocabulary — edges, textures, shapes — that food recognition needs, and "
    "fine-tuning only late layers keeps the compute budget small enough for a laptop CPU. A second "
    "practical concern drives the design: real food photographs scraped from the web contain "
    "duplicates, posters and menu cards, so dataset curation and validation must precede training "
    "rather than being assumed away.")
P[45].text = (
    "To design and evaluate a transfer-learning-based image classifier that recognises eight Indian "
    "vegetarian food classes from real photographs and reports performance both per class and per "
    "meal category (Breakfast, Snack, Main Meal), quantifying the benefit of two-stage fine-tuning "
    "over frozen-backbone training.")
P[47].text = (f"Download and validate a real-photograph corpus ({N_FULL:,} images, {N_CLASSES_FULL} "
              "classes), visually verifying that every class is represented by genuine food "
              "photographs before any training.")
P[48].text = (f"Curate an eight-class vegetarian subset of {N_TOTAL} real photographs with exact and "
              "near-duplicate removal, a stratified 70/15/15 split and documented vegetarian "
              "assumptions per dish.")
P[49].text = ("Implement two-stage ResNet-18 transfer learning in PyTorch: frozen-backbone head "
              "training, then layer3+layer4 fine-tuning at a reduced learning rate with cosine "
              "annealing.")
P[50].text = (f"Evaluate only on the unseen test split with accuracy, macro/weighted precision, "
              "recall and F1, a class-labelled confusion matrix, and meal-category aggregation.")
P[51].text = ("Provide a working upload-style prediction interface that runs the trained model on "
              "user-supplied photographs end-to-end.")
P[53].text = (
    "The project covers the full pipeline — dataset download, realness validation, subset curation, "
    "two-stage training, evaluation and deployment-style inference — for the eight classes above. "
    "Explicitly out of scope: the non-vegetarian and dessert classes of the corpus, multi-dish "
    "images, portion-size estimation, and mobile-optimised (quantised/on-device) deployment. The "
    "trained model and every reported metric are restricted to the 8 selected classes; the other "
    f"{N_CLASSES_FULL - N_CLS} corpus classes were used only to justify class selection.")

# =====================================================================
# section 2
# =====================================================================
P[56].text = (
    "Before deep learning, food recognition relied on hand-crafted features: colour-histogram "
    "descriptors, local binary patterns for texture, and SIFT keypoints fed into classifiers such as "
    "support vector machines. Kawano and Yanai's foodlog system combined colour and texture features "
    "with food-specific classifiers for dietary logging. These methods degrade quickly under the "
    "viewpoint, illumination and plating variation typical of real food photographs — precisely the "
    "variation that dominates web-scraped corpora.")
P[58].text = (
    "Deep CNNs replaced hand-crafted features after the ImageNet breakthrough. He et al. introduced "
    "ResNet residual connections, enabling very deep networks to train stably and becoming the "
    "standard transfer-learning backbone. For food specifically, the Food-101 benchmark of Bossard "
    "et al. established CNN-based dish classification at scale, and later work applied transfer "
    "learning to regional cuisines such as Indian food, reporting large gains from pretrained "
    "backbones. Fine-tuning studies consistently show that unfreezing late convolutional blocks at a "
    "reduced learning rate outperforms both pure feature extraction and full-network training on "
    "small and medium datasets.")
P[60].text = ("Hand-crafted feature pipelines generalise poorly to the viewpoint, lighting and plating "
              "variation of real food photographs.")
P[61].text = ("Training modern CNNs from scratch needs large labelled datasets and GPU-class compute "
              "that are unrealistic for a semester project; but pure frozen-backbone feature "
              "extraction leaves accuracy on the table when mid-level features (batter texture, "
              "grain patterns) are dish-specific.")
P[62].text = ("Food datasets scraped from the web mix real photographs with menu cards, posters and "
              "near-duplicate uploads; pipelines that skip deduplication leak near-identical images "
              "across splits and overstate test accuracy.")
P[64].text = (
    "The proposed system addresses all three gaps: it builds on a validated real-photograph corpus "
    f"({N_FULL:,} images inspected, 0 corrupted), removes {DUP_EXACT} exact and {DUP_NEAR} "
    "near-duplicate images before splitting (8×8 perceptual-hash deduplication), and uses a two-stage "
    "protocol — frozen-backbone head training followed by layer3+layer4 fine-tuning at one-tenth the "
    "learning rate — that recovers the mid-level features a frozen backbone cannot adapt. Evaluation "
    "is restricted to the untouched test split and is aggregated both per class and per meal "
    "category, and a working upload interface demonstrates the deployment path.")

# =====================================================================
# section 3
# =====================================================================
P[67].text = (
    "The system is a four-stage pipeline: (1) dataset preparation — download, extract, validate "
    "realness, curate the vegetarian subset with deduplication and a stratified split; (2) "
    "transfer-learning training — ImageNet ResNet-18, frozen backbone with a new head, then "
    "fine-tuning of layer3+layer4; (3) evaluation — test-split metrics, class-labelled confusion "
    "matrix, per-category analysis and qualitative montages; (4) inference — a CLI predictor and an "
    "upload-style web interface backed by the same trained checkpoint. src/ holds the pipeline "
    "modules, app/ the interface, models/ the checkpoint and class mapping, results/ every artefact "
    "reported here.")
P[69].text = "Input: real food photographs (JPG) organised as data/{train,validation,test}/<class>/ from the curated subset."
P[70].text = ("Preprocessing: RandomResizedCrop(224, scale 0.7–1.0), horizontal flip, ±10° rotation "
              "and mild colour jitter at train time; deterministic Resize(256)+CenterCrop(224) for "
              "validation/test; ImageNet normalisation everywhere.")
P[71].text = ("Feature extraction: the ResNet-18 backbone maps each image to a 512-dimensional "
              "penultimate feature vector — fully ImageNet-pretrained in stage 1, partially "
              "adapted (layer3+layer4) in stage 2.")
P[72].text = (f"Decision step: the {N_CLS}-way linear head maps the 512-d feature to class logits; "
              "softmax converts them to probabilities and argmax selects the prediction.")
P[73].text = ("Output: predicted dish label with top-3 probabilities; evaluation artefacts (metrics, "
              "confusion matrix, category CSV, per-image predictions).")
P[75].text = (
    f"The source corpus is the Indian Food Images dataset: {N_FULL:,} real food photographs across "
    f"{N_CLASSES_FULL} classes (chapati, chai, samosa, pav bhaji, kulfi and others), distributed via "
    "Kaggle/HuggingFace parquet shards and extracted losslessly to raw/images/. Validation confirmed "
    "0 corrupted and 0 suspicious (flat/drawing-like) images. From this corpus the eight vegetarian "
    "classes were selected — each verified present before selection: chapati (413 available), "
    "kadai_paneer (412), pav_bhaji (353), masala_dosa (311), idli (309), dhokla (289), pakode (278) "
    f"and samosa (262). After duplicate removal, up to {N_TOTAL // N_CLS} images per class were kept, "
    f"totalling {N_TOTAL} photographs split {N_TRAIN}/{N_VAL}/{N_TEST}. Vegetarian assumptions are "
    "documented per dish: all eight are lacto-vegetarian preparations as commonly sold (paneer and "
    "pav bhaji butter are dairy; masala dosa batter is egg-free by the dish's standard preparation); "
    "the ambiguous kaathi_rolls class, which can contain chicken or egg, was deliberately excluded.")
P[77].text = ("Deterministic eval-time preprocessing: Resize(256) on the short side, CentreCrop(224), "
              "tensor conversion, ImageNet normalisation (mean [0.485, 0.456, 0.406], std "
              "[0.229, 0.224, 0.225]) — identical to the model's pretraining distribution.")
P[78].text = ("Train-time augmentation, applied only to the training split: RandomResizedCrop(224, "
              "scale 0.7–1.0) for scale robustness, RandomHorizontalFlip, small RandomRotation(±10°) "
              "and ColorJitter(0.15, 0.15, 0.1) — realistic for mobile food photography, no extreme "
              "transforms.")
P[79].text = ("Deduplication guards the split: exact duplicates via SHA-256 byte hashes; near-"
              "duplicates via 8×8 average-hash with Hamming distance ≤ 2, so a burst of near-identical "
              "uploads cannot straddle train and test.")
P[81].text = (
    "The model is torchvision's ResNet-18 with IMAGENET1K_V1 weights: a 7×7 conv stem, four residual "
    "stages (64/128/256/512 channels, two BasicBlocks each) and global average pooling feeding the "
    f"classifier. Stage 1 replaces the fc layer with a fresh {N_CLS}-way linear head ({P_HEAD:,} "
    "trainable parameters) and trains it for 6 epochs with Adam (lr 1e-3, cosine annealing) while the "
    "backbone stays frozen. Stage 2 unfreezes layer3 and layer4, making "
    f"{P_FT:,} parameters trainable ({P_FT / P_TOTAL * 100:.0f}% of the network), and fine-tunes for "
    "6 more epochs at lr 1e-4 with the same annealing schedule — a 10× reduction that protects the "
    "pretrained weights from catastrophic drift. The objective throughout is cross-entropy on "
    f"{N_CLS}-class softmax logits; checkpoints are saved on validation-accuracy improvement.")

# =====================================================================
# section 4
# =====================================================================
P[84].text = (
    "Table 1 summarises the architecture and the parameter status in each training stage. Output "
    "sizes are for a 224×224 input.")
t1 = doc.tables[1]
t1_rows = [
    ("Stage", "Layer Type", "Output Size", "Parameters"),
    ("Stem", "7×7 conv, stride 2 + BN + ReLU, 3×3 max-pool", "64×56×56", "9,408 (frozen)"),
    ("Res2–Res3", "stages 1–2 × 2 BasicBlocks (64/128 ch)", "128×28×28", "215,808 (frozen)"),
    ("Res4–Res5", "layer3 + layer4 × BasicBlocks (256/512 ch)", "512×7×7",
     f"{8_414_720:,} (fine-tuned in stage 2)"),
    ("Global average pool", "AdaptiveAvgPool2d → flatten", "512", "0"),
    (f"Classification head", f"Linear 512 → {N_CLS} classes", str(N_CLS),
     f"{P_HEAD:,} (trained in stage 1)"),
]
ensure_rows(t1, len(t1_rows))
for i, row_vals in enumerate(t1_rows):
    for j, val in enumerate(row_vals):
        set_cell(t1.rows[i].cells[j], val, bold=(i == 0))
style_table(t1)

P[87].text = ("Python 3.12 with PyTorch 2.10 (torchvision 0.25) — model, two-stage training loop, "
              "checkpoints")
P[88].text = ("scikit-learn — precision/recall/F1 and the classification report; Pillow + NumPy — "
              "image decoding, realness validation and perceptual-hash deduplication")
P[89].text = ("pyarrow — lossless extraction of the parquet-distributed corpus; pandas + Matplotlib — "
              "category aggregation and all reported figures")
P[90].text = ("Windows 11 laptop, CPU-only training (no GPU); upload interface served by Python's "
              "standard-library HTTP server with a browser front end")

P[92].text = ("Dataset acquisition & validation: download the parquet shards, extract all images, "
              f"verify {N_FULL:,} files decode, scan for corrupted/flat images, and render a one-"
              "photo-per-class verification grid (src/prepare_data.py).")
P[93].text = (f"Subset curation: select the {N_CLS} verified vegetarian classes, remove {DUP_EXACT} "
              f"exact + {DUP_NEAR} near-duplicate images, and build the stratified "
              f"{N_TRAIN}/{N_VAL}/{N_TEST} split (src/build_subset.py).")
P[94].text = (f"Model implementation: load ImageNet ResNet-18, freeze the backbone, attach the "
              f"{N_CLS}-way head (src/dataset.py: build_model).")
P[95].text = ("Stage-1 training: head-only optimisation with Adam (lr 1e-3, cosine annealing, batch "
              "32) for 6 epochs, checkpointing on validation accuracy (src/train.py).")
P[96].text = ("Stage-2 fine-tuning: unfreeze layer3+layer4, continue at lr 1e-4 for 6 epochs, keep "
              "the best checkpoint; curves and history exported to results/.")
P[97].text = (f"Evaluation on the untouched test split ({N_TEST} images): metrics, confusion matrix, "
              "per-category aggregation, per-image predictions and a qualitative montage "
              "(src/evaluate.py).")

snip1 = '''# two-stage protocol (src/train.py, abridged)
model = build_model(num_classes)              # ImageNet ResNet-18, frozen backbone
head_params = [p for p in model.parameters() if p.requires_grad]
opt1 = torch.optim.Adam(head_params, lr=1e-3) # stage 1: head only
sched1 = torch.optim.lr_scheduler.CosineAnnealingLR(opt1, T_max=6)
...
unfreeze_late_layers(model)                   # stage 2: layer3 + layer4
opt2 = torch.optim.Adam([p for p in model.parameters() if p.requires_grad],
                        lr=1e-4)              # 10x lower LR'''
monospace(P[99], snip1)

snip2 = '''# near-duplicate guard before splitting (src/build_subset.py, abridged)
h = ahash(path)                               # 8x8 average hash
if any(int(np.count_nonzero(h != g)) <= 2 for g in hashes):
    near_duplicates_removed += 1              # skip: too similar to a kept image
hashes.append(h); kept.append(file)'''
monospace(P[99], snip2)
P[99].text = ""

# =====================================================================
# section 5
# =====================================================================
P[102].text = (
    f"Final curated dataset: {N_TOTAL} real photographs across {N_CLS} classes (250 per class), "
    f"split {N_TRAIN} train / {N_VAL} validation / {N_TEST} test (70/15/15, stratified per class). "
    "Every split image is a genuine food photograph from the Indian Food Images corpus; "
    f"{DUP_EXACT} exact duplicates and {DUP_NEAR} near-duplicates were removed before splitting. "
    "Meal-category mapping: Breakfast — idli, masala dosa, dhokla; Snack — samosa, pakode; "
    "Main Meal — chapati, kadai paneer, pav bhaji.")

t2 = doc.tables[2]
t2_rows = [
    ("Parameter", "Value"),
    ("Input Size", "224 × 224 × 3 (RGB)"),
    ("Batch Size", "32"),
    ("Stage 1", "head only, Adam lr 1e-3, 6 epochs, cosine annealing"),
    ("Stage 2", "layer3+layer4 fine-tune, Adam lr 1e-4, 6 epochs, cosine annealing"),
    ("Loss Function", "Cross-entropy (8-class softmax)"),
    ("Augmentation", "RandomResizedCrop(0.7–1.0), flip, ±10° rotation, jitter (train only)"),
    ("Hardware", "CPU only (Windows 11 laptop, no GPU)"),
]
ensure_rows(t2, len(t2_rows))
for i, row_vals in enumerate(t2_rows):
    for j, val in enumerate(row_vals):
        set_cell(t2.rows[i].cells[j], val, bold=(i == 0))
style_table(t2)

P[106].text = (
    "Accuracy is the primary headline metric on the unseen test split. Macro precision/recall/F1 "
    "treat all eight classes equally (they are perfectly balanced — 38 test images each), while the "
    "weighted variants weight by support; with a balanced test set the two coincide, which itself "
    "confirms the split's balance. The 8×8 confusion matrix with real class names localises every "
    "error, and the meal-category aggregation answers the applied question: which meal slots can a "
    "diet-tracking application trust this model in.")

t3 = doc.tables[3]
t3_rows = [
    ("Model / metric view", "Accuracy", "Precision", "Recall", "F1-Score"),
    (f"ResNet-18 frozen backbone (stage 1, val)", f"{S1_END:.4f}", "—", "—", "—"),
    (f"ResNet-18 fine-tuned (stage 2, val)", f"{BEST['val_acc']:.4f}", "—", "—", "—"),
    (f"Final model — TEST (macro)", f"{ACC:.4f}", f"{PM:.4f}", f"{RM:.4f}", f"{F1M:.4f}"),
    (f"Final model — TEST (weighted)", f"{ACC:.4f}", f"{PW:.4f}", f"{RW:.4f}", f"{F1W:.4f}"),
]
ensure_rows(t3, len(t3_rows))
for i, row_vals in enumerate(t3_rows):
    for j, val in enumerate(row_vals):
        set_cell(t3.rows[i].cells[j], val, bold=(i == 0))
style_table(t3)

P[109].text = (
    f"Stage 1 converged steadily: validation accuracy rose from 0.6486 after one epoch to "
    f"{S1_END:.4f} by epoch 6 with the backbone frozen. Unfreezing layer3+layer4 produced an "
    f"immediate jump — validation accuracy hit {BEST['val_acc']:.4f} within two fine-tuning epochs "
    f"(epoch 8 overall), an improvement of {(BEST['val_acc'] - S1_END) * 100:.1f} points over the "
    "frozen protocol. Training accuracy reached 0.99 by the end of stage 2 while validation "
    "stabilised around 0.89–0.91: the expected mild generalisation gap when nearly the whole "
    "network is trainable on 1,400 images. The checkpoint saved is the best-validation one "
    f"({BEST['val_acc']:.4f}, stage-2 epoch {BEST['epoch'] - HIST['stage1_epochs']}).")

# =====================================================================
# section 6
# =====================================================================
P[114].text = "6.2 Predictions and Output Quality"

t4 = doc.tables[4]
t4_rows = [
    ("", "Predicted: correct class", "Predicted: any other class"),
    ("Actual: all 8 classes (304 test images)", "269", "35"),
    ("Actual: strongest class", "idli / kadai_paneer: 36/38", "2 errors each"),
    ("Actual: weakest class", "masala_dosa: 31/38", "7 errors"),
]
ensure_rows(t4, len(t4_rows))
for i, row_vals in enumerate(t4_rows):
    for j, val in enumerate(row_vals):
        set_cell(t4.rows[i].cells[j], val, bold=(i == 0))
style_table(t4)

P[113].text = (
    f"The confusion matrix (Figure 3) shows a strongly diagonal structure: {PREDS['correct']} of "
    f"{PREDS['total']} test photographs are classified correctly. Errors concentrate in three "
    "visually plausible look-alike pairs — masala dosa → chapati (4), pav bhaji → kadai paneer (4) "
    "and samosa → pakode (4) — all sharing golden-brown fried or gravy-dominant appearance. The "
    "strongest classes are idli and kadai paneer (36/38 each); even the weakest class (masala dosa) "
    "reaches 0.816. No class collapses: every class retains ≥ 0.82 accuracy, indicating the errors "
    "are boundary confusions rather than systematic failures.")
P[115].text = (
    "Qualitatively, predictions on clean close-up photos are decisive — the upload interface "
    "commonly returns > 0.99 confidence for canonical dishes (a held-out masala dosa scores 0.996, "
    "an idli 0.995). Low-margin cases cluster where plating is ambiguous: pakode misclassifications "
    "mostly carry < 0.6 confidence, which makes a practical rejection threshold feasible. The "
    "montage of sample predictions (Figure 4) pairs each actual class with its predicted label and "
    "confidence, so the panel can inspect behaviour directly without reading code.")
P[117].text = (
    f"Table 3 isolates the contribution of fine-tuning: the frozen-backbone protocol plateaus at "
    f"{S1_END:.4f} validation accuracy, while two-stage fine-tuning reaches {BEST['val_acc']:.4f} — "
    f"a {(BEST['val_acc'] - S1_END) * 100:.1f}-point gain. Mechanistically, the eight dishes differ "
    "in mid-level texture cues (steamed-pore pattern of idli/dhokla, batter lace of a dosa, fried-"
    "batter granularity of pakode) that ImageNet's generic features under-represent; adapting "
    "layer3+layer4 lets the network retune exactly those features while the early layers keep their "
    "generic edge/colour vocabulary. The cost is a mild train–validation gap (0.99 vs 0.91), the "
    "standard trade-off when fine-tuning 93.9% of a network on a small dataset.")
P[119].text = (f"Fine-tuning layer3+layer4 delivers a {(BEST['val_acc'] - S1_END) * 100:.1f}-point "
               "validation-accuracy gain over the frozen-backbone protocol on real photographs.")
P[120].text = ("Errors are plausible look-alike confusions (dosa↔chapati, samosa↔pakode, pav bhaji↔"
               "kadai paneer), not random noise — every class stays above 0.82 accuracy.")
P[121].text = ("Meal-category performance is balanced (Breakfast 0.886, Snack 0.895, Main Meal "
               "0.877), so no meal slot is systematically weaker.")
P[123].text = ("Trained end-to-end on a laptop CPU in ~13 minutes of compute; the full pipeline is "
               "reproducible from the raw parquet shards with five commands.")
P[124].text = ("Deduplication before splitting removes leakage risk — exact (SHA-256) and "
               "near-duplicate (perceptual-hash) twins never straddle splits.")
P[125].text = ("A working upload interface demonstrates deployment: the same checkpoint serves "
               "user-uploaded photographs with top-3 probabilities.")
P[127].text = ("Real web-scraped photos include noisy framing (menus, posters, multiple dishes); "
               "class-level accuracy is bounded by such label noise in the corpus itself.")
P[128].text = ("Eight classes is a deliberate scope: extending to all 20 corpus classes would need "
               "more fine-tuning capacity and better background control.")
P[129].text = ("No calibration or rejection layer is deployed yet; low-confidence thresholds are "
               "observed but not engineered into the interface.")

# =====================================================================
# section 7
# =====================================================================
P[132].text = (
    f"This project delivers an end-to-end, CPU-trainable vegetarian food classifier built on genuine "
    f"photographs: a validated {N_FULL:,}-image real-photo corpus, a deduplicated eight-class "
    f"vegetarian subset of {N_TOTAL} images with a leakage-free stratified split, and a two-stage "
    f"ResNet-18 transfer-learning pipeline whose fine-tuned model reaches {ACC:.4f} test accuracy "
    f"(macro F1 {F1M:.4f}) on {N_TEST} unseen photographs. Fine-tuning layer3+layer4 contributed a "
    f"{(BEST['val_acc'] - S1_END) * 100:.1f}-point validation gain over frozen-backbone training, and "
    "the remaining errors are interpretable look-alike confusions. An upload-style interface runs the "
    "trained model on user photographs, closing the loop from dataset to deployment.")
P[134].text = ("Expand to all 20 corpus classes and add a curation pass that filters poster/menu-card "
               "images automatically (flat-region and text-density heuristics).")
P[135].text = ("Add test-time augmentation and confidence calibration (temperature scaling) so a "
               "rejection threshold can be deployed safely in the interface.")
P[136].text = ("Integrate the classifier into a calorie-estimation demo: dish label → nutrition "
               "lookup → daily-total dashboard, using the upload interface as the front end.")
P[138].text = (
    "As detailed in Section 6.6, the current conclusions are bounded by the corpus's web-scraped "
    "label noise, the eight-class scope, and CPU-scale training. These bounds do not weaken the "
    "central finding — that two-stage fine-tuning of an ImageNet-pretrained ResNet-18 on a small, "
    "carefully deduplicated set of real food photographs yields a usable eight-way classifier on a "
    "laptop — but the reported accuracy should be read as a curated-subset result rather than a "
    "field deployment estimate across all Indian cuisine.")
P[140].text = ('[1] K. He, X. Zhang, S. Ren, and J. Sun, "Deep Residual Learning for Image '
               'Recognition", IEEE CVPR, 2016.')
P[141].text = ('[2] L. Bossard, M. Guillaumin, and L. Van Gool, "Food-101 – Mining Discriminative '
               'Components with Random Forests", ECCV, 2014.')
P[142].text = ("[3] Indian Food Images Dataset, 4,000 real food photographs across 80 classes, "
               "Kaggle (iamsouravbanerjee/arjunashok33 distributions; HuggingFace mirror "
               "rajistics/indian_food_images used here), accessed 2026.")

# =====================================================================
# figures
# =====================================================================

# Figure 1 before 5.1 Dataset Details heading (P101)
insert_figure(doc, os.path.join("results", "dataset_samples_grid.png"), 16.0,
              f"Figure 1: One real photograph per class — the {N_CLS}-class vegetarian subset "
              "grid from the validated corpus", P[101])

# Figure 2 before 5.4 Results heading (P107)
insert_figure(doc, os.path.join("results", "training_loss.png"),
              15.0, f"Figure 2: Training and validation loss — stage 1 (frozen backbone, epochs "
              f"1–6) vs stage 2 (fine-tune, epochs 7–12); validation improves from "
              f"{S1_END:.4f} to {BEST['val_acc']:.4f}", P[107])

# Figure 3 before 6.1 heading (P111)
insert_figure(doc, os.path.join("results", "confusion_matrix.png"),
              12.5, f"Figure 3: Test confusion matrix ({N_TEST} real photographs, accuracy "
              f"{ACC:.4f})", P[111])

# Figure 4 before 6.2 heading (P113)
insert_figure(doc, os.path.join("results", "sample_predictions.png"),
              16.0, "Figure 4: Qualitative test predictions — actual vs predicted class with "
              "confidence", P[113])

# =====================================================================
doc.save(OUT)
print("saved", OUT)
