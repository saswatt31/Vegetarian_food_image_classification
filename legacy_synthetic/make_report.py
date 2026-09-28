"""
Generate Project_Report_Vegetarian_Food_Image_Classification.docx by filling
C:\\Users\\saswa\\Downloads\\Project_Report_Template.docx IN PLACE (styles,
headers and the TOC field are preserved; Word refreshes the TOC with F9).

Run:    python make_report.py
Output: Project_Report_Vegetarian_Food_Image_Classification.docx (project root)
"""
import copy
import glob
import os

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

TEMPLATE = r"C:\Users\saswa\Downloads\Project_Report_Template.docx"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "Project_Report_Vegetarian_Food_Image_Classification.docx")

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
SUBTITLE = ("A ResNet-18 transfer-learning classifier for seven Indian vegetarian dishes "
            "with meal-category-wise evaluation")
ACCENT = RGBColor(0xC2, 0x5E, 0x1C)   # terracotta accent for figure captions

FIG_BASE = os.path.dirname(os.path.abspath(__file__))

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
    """Insert a centered picture + caption immediately before `before_par`."""
    p = doc.add_paragraph()          # appended at end of body
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
    """Insert Consolas lines BEFORE target_par (template keeps the anchor)."""
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
    "We further declare that all sources of information, ideas, algorithms, and datasets used in the "
    "preparation of this report have been duly acknowledged, and that the computational results "
    "reported here were produced by running the project's own code on the dataset described in "
    "Section 3.3.")
P[16].text = "Team Members:"
for i, (name, roll) in enumerate(STUDENTS):
    P[17 + i].text = f"{name} ({roll})"
# P[22]/P[23]: Place / Date intentionally left blank for physical signing

# ---------------------------------------------------------- acknowledgement
P[26].text = (
    "We take this opportunity to express our sincere gratitude to everyone who supported us throughout "
    "this project. We are deeply thankful to our guide, Mr. Rahul Rawat, for his continuous guidance, "
    "constructive feedback and encouragement at every stage of this work — from framing the problem to "
    "interpreting the evaluation results.")
P[27].text = (
    "We would also like to thank the faculty members of the Department of Artificial Intelligence & "
    "Machine Learning for providing the academic foundation in convolutional neural networks and "
    "transfer learning that this project builds upon, and the Faculty of Engineering and Technology "
    "for the laboratory resources used to run the experiments.")
P[28].text = (
    "Finally, we would like to acknowledge the effort and cooperation of every member of our team, whose "
    "combined contribution made it possible to design the dataset pipeline, train and evaluate the "
    "model, and prepare this report within the semester timeline.")

# --------------------------------------------------------------- abstract
P[31].text = (
    "Automatic recognition of food items from photographs has become a key building block for "
    "calorie-estimation and diet-tracking applications: users increasingly photograph their meals instead "
    "of searching menus, and a mobile app must map each photo to the correct dish before nutrition can be "
    "computed. Indian vegetarian cuisine poses a particular challenge because many dishes share "
    "similar colours and textures — a dosa and a vegetable thali can look alike at a glance — while small "
    "data regimes make training a large network from scratch impractical on student hardware.")
P[32].text = (
    "This project builds an image classifier for seven common vegetarian preparations — veg thali, "
    "paneer curry, dosa, idli, samosa, vegetable biryani and lassi — organised into four meal categories "
    "(Main Course, Breakfast, Snack, Beverage). It applies transfer learning: a ResNet-18 backbone "
    "pretrained on ImageNet supplies reusable visual features, and a newly initialised linear head is "
    "trained on top. The backbone is frozen, so only 3,591 parameters are updated, which allows training "
    "on a CPU in minutes and avoids overfitting on a small dataset.")
P[33].text = (
    "Methodology: a 1,120-image dataset (160 images per class) of synthetic-but-realistic mobile-style "
    "food photos is generated offline with dish-specific signatures (plate shape, colour palette, texture) "
    "and mobile-camera augmentation (rotation, brightness jitter, blur). Images are resized to 224×224 and "
    "normalised with ImageNet statistics; the head is trained for 6 epochs with Adam (lr = 1e-3) and "
    "cross-entropy loss, monitoring validation accuracy for checkpoint selection. Evaluation reports "
    "overall accuracy, per-class precision/recall/F1, a confusion matrix, and accuracy aggregated across "
    "meal categories.")
P[34].text = (
    "The transfer-learned model reaches 0.9911 test accuracy (111/112 images), macro precision 0.9916, "
    "macro recall 0.9911 and macro F1 0.9911, with 1.0 accuracy for the Beverage, Breakfast and Snack "
    "categories and 0.979 for Main Course. Compared with an identically trained random-initialisation "
    "ResNet-18 baseline, ImageNet transfer learning contributes a double-digit improvement, confirming "
    "that frozen pretrained features are the decisive ingredient for accurate food recognition under a "
    "small-data, CPU-only constraint.")

# =====================================================================
# section 1
# =====================================================================
P[41].text = (
    "Food-image recognition sits at the intersection of computer vision and mobile health applications. "
    "Diet-tracking and calorie-estimation apps ask users to photograph their meals, and the accuracy of "
    "the underlying dish classifier directly determines the quality of the nutrition estimate. In a "
    "campus canteen or mess scenario, the same technology can automate meal identification at the "
    "counter, support food-delivery cataloguing, and power nutrition education tools.")
P[43].text = (
    "Collecting and labelling large real-world food datasets is expensive, and training deep networks "
    "from scratch requires GPU resources that are rarely available for a semester project. At the same "
    "time, convolutional backbones pretrained on ImageNet already encode the generic visual vocabulary — "
    "edges, textures, shapes — that food recognition needs. This project is motivated by the question of "
    "how far a frozen, CPU-trainable transfer-learning pipeline can go on a compact, reproducible "
    "vegetarian-food dataset, while also answering a practical question that matters for deployment: "
    "which meal categories does the model master, and where do confusions remain?")
P[45].text = (
    "To design and evaluate a transfer-learning-based image classifier that recognises seven vegetarian "
    "food classes (veg thali, paneer curry, dosa, idli, samosa, vegetable biryani and lassi) from 224×224 "
    "images and reports performance both per class and per meal category (Breakfast, Main Course, Snack, "
    "Beverage).")
P[47].text = ("Build a labelled vegetarian-food image dataset with a deterministic 80/10/10 "
              "train/validation/test split and a class-to-meal-category mapping.")
P[48].text = ("Implement ResNet-18 transfer learning with a frozen ImageNet backbone and a trained "
              "linear classification head in PyTorch.")
P[49].text = ("Provide an optional fine-tuning mode (--finetune) that unfreezes layer3/layer4 at a "
              "reduced learning rate for real-photo datasets.")
P[50].text = ("Evaluate with accuracy, per-class precision/recall/F1, a confusion matrix, and "
              "accuracy aggregated across the four meal categories.")
P[51].text = ("Quantify the contribution of ImageNet pretraining by comparing against an identically "
              "trained random-initialisation baseline.")
P[53].text = (
    "The project covers the full pipeline — dataset construction, training, evaluation and single-image "
    "prediction — for the seven classes above, using a synthetic-but-realistic image generator so that "
    "every experiment is exactly reproducible offline. Single-image inference is provided as a "
    "command-line tool and as an interactive browser demo. Explicitly out of scope: real-photograph "
    "datasets at scale (the code accepts them via --real-dir but they are not evaluated here), object "
    "detection or portion-size estimation, multi-dish images, and deployment on embedded or mobile "
    "hardware.")

# =====================================================================
# section 2
# =====================================================================
P[56].text = (
    "Before deep learning, food recognition relied on hand-crafted features: colour-histogram "
    "descriptors, local binary patterns for texture, and scale-invariant feature transform (SIFT) "
    "keypoints fed into classifiers such as support vector machines. Kawano and Yanai's foodlog system "
    "combined colour and texture features with food-specific classifiers for dietary logging, while "
    "earlier bag-of-features pipelines treated dishes as texture collages. These methods degrade quickly "
    "under the viewpoint, illumination and plating variation typical of smartphone photos.")
P[58].text = (
    "Deep CNNs replaced hand-crafted features after the ImageNet breakthrough. He et al. introduced "
    "ResNet residual connections, enabling very deep networks to train stably and becoming the standard "
    "transfer-learning backbone. For food specifically, the Food-101 benchmark of Bossard et al. "
    "established CNN-based dish classification at scale, and later work applied transfer learning to "
    "regional cuisines such as Indian and Singaporean food, reporting large gains from pretrained "
    "backbones. Subsequent studies consistently show pretrained-backbone + linear-head pipelines "
    "reaching high accuracy with a few thousand images.")
P[60].text = ("Hand-crafted feature pipelines generalise poorly to the viewpoint, lighting and plating "
              "variation of smartphone food photos.")
P[61].text = ("Training modern CNNs from scratch needs large labelled datasets and GPU-class compute "
              "that are unrealistic for small, reproducible student projects.")
P[62].text = ("Generic CNN evaluations rarely report where a food model fails — per-class and "
              "per-meal-category behaviour is usually collapsed into a single accuracy number, hiding "
              "the confusions that matter for a diet-tracking product.")
P[64].text = (
    "The proposed system addresses all three gaps: it uses a frozen ImageNet-pretrained ResNet-18 so "
    "that only 3,591 head parameters are trained (removing the GPU/compute barrier), it pairs a compact "
    "reproducible dataset generator with realistic camera augmentation so the whole pipeline runs "
    "offline on a laptop, and it evaluates not only per class but also aggregated across the four meal "
    "categories, exposing exactly where the classifier is dependable. A random-init ablation isolates "
    "the contribution of transfer learning itself, and a single-image prediction tool plus a browser "
    "demo make the behaviour inspectable.")

# =====================================================================
# section 3
# =====================================================================
P[67].text = (
    "The system is a four-stage pipeline: (1) a dataset builder that renders 160 synthetic-but-realistic "
    "mobile-style photos per class and splits them 80/10/10; (2) a transfer-learning trainer that loads "
    "an ImageNet-pretrained ResNet-18, freezes the convolutional backbone, and trains a new linear head; "
    "(3) an evaluator that produces test accuracy, the per-class report, a confusion-matrix figure and "
    "meal-category aggregation; and (4) inference interfaces — a CLI single-image predictor and a "
    "browser demo that replays exported top-3 softmax predictions. Everything is orchestrated by "
    "run_all.py and leaves reproducible artefacts in outputs/ and results/.")
P[69].text = "Input: raw 224×224 RGB food images from data/{train,val,test}/<class>/ plus the class-to-category map."
P[70].text = ("Preprocessing: resize to 256 and centre-crop to 224 (RandomResizedCrop 224, scale "
              "0.7–1.0 at train time), convert to tensor, normalise with ImageNet mean/std.")
P[71].text = ("Feature Extraction: the frozen ResNet-18 backbone maps each image to its 512-dimensional "
              "penultimate feature vector, reusing ImageNet-learned visual representations.")
P[72].text = ("Model / Decision Step: the trained linear head maps the 512-d feature to 7 class logits; "
              "softmax converts them to class probabilities and argmax selects the prediction.")
P[73].text = ("Output: predicted dish label with top-3 softmax probabilities; aggregate evaluation "
              "artefacts (accuracy, per-class report, confusion matrix, category-wise accuracy CSVs).")
P[75].text = (
    "The dataset contains 1,120 RGB images at 224×224 resolution — 160 per class for seven vegetarian "
    "classes — generated deterministically by prepare_dataset.py (seeded per class) so every run is "
    "reproducible. Each class has a distinct visual signature: veg thali a large decorated plate with "
    "katori spots, paneer curry a grey bowl with rich orange-red gravy, dosa a golden-brown oval, idli "
    "pale-white paired circles, samosa a brown triangle with darkened edges, biryani a bowl of "
    "rice-like grains, and lassi a tall glass with a frothy top. Mobile-camera realism is simulated by "
    "rotation (±25°), brightness jitter (±22 levels), random Gaussian blur (35% of images) and textured "
    "wooden-table backgrounds. Labels are exact by construction; the class → meal-category mapping is: "
    "dosa, idli → Breakfast; veg thali, paneer curry, veg biryani → Main Course; samosa → Snack; "
    "lassi → Beverage. The split is 896 train / 112 val / 112 test images.")
P[77].text = ("Resize to 256 px on the short side and centre-crop to 224×224 at evaluation time; "
              "RandomResizedCrop(224, scale 0.7–1.0) during training for scale robustness.")
P[78].text = ("Convert to tensor and normalise with ImageNet channel statistics "
              "(mean [0.485, 0.456, 0.406], std [0.229, 0.224, 0.225]) to match the backbone's "
              "pretraining distribution.")
P[79].text = ("Data augmentation on the training split only: random horizontal flip and colour jitter "
              "(brightness/contrast/saturation ±0.15); the generator itself already applies rotation, "
              "brightness and Gaussian blur as camera-variation augmentation.")
P[81].text = (
    "The model is torchvision's ResNet-18 with IMAGENET1K_V1 weights. ResNet-18 comprises a 7×7 "
    "convolutional stem (stride 2), max-pooling, four residual stages (64, 128, 256, 512 channels; each "
    "stage two BasicBlocks with identity skip connections), and global average pooling feeding a fully "
    "connected layer. For transfer learning, all backbone parameters are frozen (requires_grad = False) "
    "and the 512→7 linear head is replaced and trained; this leaves exactly 3,591 trainable parameters "
    "(512 × 7 weights + 7 biases), which is why the pipeline trains on a CPU in minutes. An optional "
    "fine-tuning mode unfreezes layer3 and layer4 and trains them at one-tenth the learning rate. The "
    "training objective is cross-entropy loss on 7-class softmax logits, optimised with Adam.")

# =====================================================================
# section 4
# =====================================================================
P[84].text = (
    "Table 1 summarises the frozen ResNet-18 backbone and the trained head. Only the final linear stage "
    "receives gradient updates; every earlier stage merely forwards activations. Output sizes are for a "
    "224×224 input.")
t1 = doc.tables[1]
t1_rows = [
    ("Stage", "Layer Type", "Output Size", "Parameters"),
    ("Stem", "7×7 conv, stride 2 + BN + ReLU, 3×3 max-pool", "64×56×56", "9,408 (frozen)"),
    ("Res2–Res5", "4 stages × 2 BasicBlocks (64/128/256/512 ch)", "512×7×7",
     "11,176,512 (frozen)"),
    ("Global average pool", "AdaptiveAvgPool2d → flatten", "512", "0"),
    ("Classification head", "Linear 512 → 7 classes", "7", "3,591 (trained)"),
]
while len(t1.rows) < len(t1_rows):
    t1._tbl.append(copy.deepcopy(t1.rows[-1]._tr))
for i, row_vals in enumerate(t1_rows):
    for j, val in enumerate(row_vals):
        set_cell(t1.rows[i].cells[j], val, bold=(i == 0))
style_table(t1)

P[87].text = "Python 3.12 with PyTorch 2.10 (torchvision 0.25) — model, training loop, checkpoints"
P[88].text = ("Pillow + NumPy — synthetic dataset rendering and camera-noise augmentation; "
              "scikit-learn — classification report and confusion-matrix computation")
P[89].text = ("Matplotlib — training curves and the confusion-matrix figure; pandas — "
              "category-accuracy aggregation")
P[90].text = ("Windows 11 laptop, CPU-only training (no GPU required); browser demo in HTML/"
              "JavaScript with no additional dependencies")
P[92].text = ("Data collection & organisation: generate the 1,120-image synthetic dataset and the "
              "labels.csv index (prepare_dataset.py).")
P[93].text = ("Preprocessing pipeline: build the train/eval transform chains (resize, crop, tensor, "
              "ImageNet normalisation).")
P[94].text = ("Model implementation: load ImageNet ResNet-18, freeze all backbone parameters, replace "
              "the fc head with a 512→7 linear layer (train.py: build_model).")
P[95].text = ("Training configuration: cross-entropy loss, Adam optimizer (lr 1e-3, batch size 32), "
              "6 epochs, checkpoint on best val accuracy (train.py).")
P[96].text = ("Training with monitoring: per-epoch train/val loss and accuracy logging; best checkpoint "
              "saved to outputs/best_model.pth; curves saved to outputs/training_curves.png.")
P[97].text = ("Evaluation on held-out test set: overall accuracy, per-class report, confusion-matrix "
              "figure, and meal-category aggregation (evaluate.py).")

snip1 = '''# build_model: ImageNet backbone frozen, new head trained (train.py)
model = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
for p in model.parameters():
    p.requires_grad = False          # freeze the entire backbone
model.fc = nn.Linear(model.fc.in_features, num_classes)  # 512 -> 7 head
# -> only 3,591 trainable parameters, CPU-trainable in minutes'''
monospace(P[99], snip1)

snip2 = '''# per-epoch checkpoint selection (train.py, abridged)
if va_acc > best_acc:
    best_acc = va_acc
    torch.save({"model_state": model.state_dict(), "classes": classes},
               os.path.join(args.out, "best_model.pth"))'''
monospace(P[99], snip2)
P[99].text = ""

# =====================================================================
# section 5
# =====================================================================
P[102].text = (
    "Final dataset: 1,120 images across 7 classes (160 per class) at 224×224 resolution, split "
    "896 / 112 / 112 for train / validation / test (80/10/10). The class-to-meal-category mapping "
    "groups the seven dishes into Breakfast (dosa, idli), Main Course (veg thali, paneer curry, veg "
    "biryani), Snack (samosa) and Beverage (lassi).")

t2 = doc.tables[2]
t2_rows = [
    ("Parameter", "Value"),
    ("Input Size", "224 × 224 × 3 (RGB)"),
    ("Batch Size", "32"),
    ("Optimizer", "Adam, lr = 1e-3 (head parameters only)"),
    ("Loss Function", "Cross-entropy (7-class softmax)"),
    ("Epochs", "6 (best checkpoint on validation accuracy)"),
    ("Hardware", "CPU only (Windows 11 laptop, no GPU)"),
]
for i, row_vals in enumerate(t2_rows):
    for j, val in enumerate(row_vals):
        set_cell(t2.rows[i].cells[j], val, bold=(i == 0))
style_table(t2)

P[106].text = (
    "Accuracy is the primary headline metric (111/112 test images correct). Per-class precision, recall "
    "and F1 (scikit-learn classification_report) quantify per-dish reliability and reveal the single "
    "confusion. Macro averaging treats all seven classes equally despite their identical support. The "
    "7×7 confusion matrix localises every error, and the category-level summary — a sample-weighted "
    "average of per-class accuracy grouped by meal category — answers the project's applied question: "
    "which meal slots can a diet-tracking app trust this model in.")

t3 = doc.tables[3]
# baseline numbers come from the actually-executed ablation (baseline_experiment.py)
import json
with open(os.path.join(FIG_BASE, "results", "baseline_scratch.json"),
          encoding="utf-8") as f:
    base = json.load(f)
base_gap = round((0.9911 - base["test_accuracy"]) * 100, 1)
t3_rows = [
    ("Model", "Accuracy", "Precision", "Recall", "F1-Score"),
    ("ResNet-18 random init (frozen, head-only)",
     f"{base['test_accuracy']:.4f}", f"{base['macro_precision']:.4f}",
     f"{base['macro_recall']:.4f}", f"{base['macro_f1']:.4f}"),
    ("ResNet-18 ImageNet transfer (proposed)",
     "0.9911", "0.9916", "0.9911", "0.9911"),
]
for i, row_vals in enumerate(t3_rows):
    for j, val in enumerate(row_vals):
        set_cell(t3.rows[i].cells[j], val, bold=(i == 0))
style_table(t3)
BASE_ACC = f"{base['test_accuracy']:.4f}"
GAP = f"+{base_gap:.1f}"

P[109].text = (
    "Training converged within two epochs — validation accuracy reached 1.0000 by epoch 2 and stayed "
    "there, while training accuracy climbed from 0.84 to 1.00 over the six epochs, showing that the "
    "frozen ImageNet features already separated the seven dishes almost perfectly and the head only had "
    "to learn a simple linear read-out. No overfitting gap appeared (train and validation losses moved "
    "together), which is the expected behaviour when only 3,591 parameters are trained on 896 images.")

# =====================================================================
# section 6
# =====================================================================
P[114].text = "6.2 Predictions and Output Quality"

t4 = doc.tables[4]
# Collapse the template's two-class grid into the aggregate correct/incorrect
# view supported by the actual 7×7 confusion matrix (Figure 2).
t4_rows = [
    ("", "Predicted: correct class", "Predicted: any other class"),
    ("Actual: all 7 classes (112 test images)", "111", "1"),
    ("Actual: per-class detail (Figure 2)", "6 classes: 16/16 each", "biryani: 15/16"),
]
for i, row_vals in enumerate(t4_rows):
    for j, val in enumerate(row_vals):
        set_cell(t4.rows[i].cells[j], val, bold=(i == 0))
style_table(t4)

P[113].text = (
    "The full 7×7 confusion matrix (Figure 2) is essentially diagonal: 111 of 112 test images are "
    "classified correctly. The single error is one veg biryani image misclassified as paneer curry — "
    "both are Main-Course bowl dishes with warm brown/orange palettes, so the confusion is visually "
    "plausible. Every other class, including the near-identical Breakfast pair dosa/idli, is perfectly "
    "separated. There is no class-level bias: each class contributes exactly 16 test images, and six of "
    "seven classes score a perfect 16/16.")
P[115].text = (
    "The browser demo (frontend/) replays the exported top-3 softmax probabilities of every test image, "
    "so qualitative behaviour can be inspected without re-running the model. Correct predictions are "
    "decisive — dosa images are predicted dosa with >0.99 confidence and lassi with ≈1.00. The lone "
    "biryani→paneer_curry error is a low-margin case, illustrating the practical failure mode of bowl "
    "dishes with similar warm palettes. The model excels on shape-coded dishes (oval dosa, triangular "
    "samosa, glass lassi) and is marginally weaker on texture-coded bowls, where grain pattern is the "
    "only discriminator.")
P[117].text = (
    "Table 3 isolates the effect of ImageNet pretraining: an identically trained random-initialisation "
    "ResNet-18 (same frozen-backbone, head-only protocol, same 6 epochs and optimizer) reaches only "
    f"{BASE_ACC} test accuracy, while the ImageNet-transfer model reaches 0.9911 — a {GAP} percentage-point "
    "gap. Mechanistically, the frozen pretrained backbone supplies texture, colour and shape features "
    "that already distinguish the dishes; the head only learns a linear read-out. With random "
    "initialisation those mid-level visual features do not exist yet after 6 head-only epochs, so the "
    "head fits class-correlated colour shortcuts and confuses visually similar dishes.")
P[119].text = ("Validation accuracy saturates at 1.0000 from epoch 2 — the linear head converges almost "
               "immediately on frozen ImageNet features.")
P[120].text = ("All errors concentrate in the Main-Course bowl group (biryani ↔ paneer curry); "
               "shape-distinct classes reach 1.0 accuracy.")
P[121].text = ("Training completes on CPU in about 2–3 minutes for the full 6 epochs, confirming the "
               "practicality of frozen-backbone transfer learning.")
P[123].text = ("Only 3,591 trainable parameters — no GPU, no overfitting risk, and a 2–3 minute CPU "
               "training budget.")
P[124].text = ("Fully reproducible: the dataset generator is seeded, so every split, training run and "
               "reported number can be regenerated exactly.")
P[125].text = ("Category-level evaluation is built in, directly answering which meal slots a "
               "diet-tracking app can trust.")
P[127].text = ("Evaluation uses a synthetic-but-realistic dataset; absolute numbers will be lower on "
               "real photography despite the --real-dir ingestion path.")
P[128].text = "Single-dish images only: multi-dish plates and portion-size estimation are out of scope."
P[129].text = ("The head-only protocol caps what can be achieved on harder real-world variation (an "
               "optional --finetune mode exists but was not needed here).")

# =====================================================================
# section 7
# =====================================================================
P[132].text = (
    "This project delivers an end-to-end, CPU-trainable vegetarian food image classifier: a seeded "
    "1,120-image dataset across seven dishes and four meal categories, a frozen ResNet-18 + linear-head "
    "transfer-learning pipeline (3,591 trainable parameters), and an evaluation suite reporting 0.9911 "
    "test accuracy with macro F1 0.9911. The random-init ablation shows that ImageNet transfer learning "
    f"contributes a {GAP}-point improvement and is the decisive ingredient under the small-data "
    "CPU-only constraint, while the category-level analysis locates the single remaining confusion in "
    "the Main-Course bowl group.")
P[134].text = ("Regenerate the dataset from real photography (e.g. an Indian subset of Food-101) and "
               "fine-tune layer3/layer4 with the existing --finetune mode.")
P[135].text = ("Replace the linear head with a small multi-layer head or add test-time augmentation to "
               "close the residual bowl-dish confusion.")
P[136].text = ("Integrate the classifier into a calorie-estimation demo: dish label → nutrition lookup "
               "→ daily-total dashboard, using the browser demo as the front end.")
P[138].text = (
    "As detailed in Section 6.6, the current conclusions are bounded by the synthetic dataset (absolute "
    "accuracy will differ on real photos), single-dish framing (no multi-dish plates or portion "
    "estimation), and the head-only training protocol. These bounds do not weaken the central finding — "
    "that frozen ImageNet features make dish recognition tractable at extreme parameter and compute "
    "budgets — but they do mean the reported 0.9911 accuracy should be read as an upper-bound "
    "characterisation of the pipeline rather than a field deployment estimate.")
P[140].text = ('[1] K. He, X. Zhang, S. Ren, and J. Sun, "Deep Residual Learning for Image '
               'Recognition", IEEE CVPR, 2016.')
P[141].text = ('[2] L. Bossard, M. Guillaumin, and L. Van Gool, "Food-101 – Mining Discriminative '
               'Components with Random Forests", ECCV, 2014.')
P[142].text = ("[3] PyTorch Documentation — torchvision.models (ResNet-18, ImageNet1K_V1 weights), "
               "PyTorch Foundation, https://pytorch.org/vision/stable/models.html (accessed 2026).")

# =====================================================================
# figures
# =====================================================================

# dataset sample collage (one image per class)
collage = os.path.join(FIG_BASE, "results", "dataset_samples.png")
if not os.path.exists(collage):
    from PIL import Image, ImageDraw
    picks = []
    for cls in ["dosa", "idli", "lassi", "paneer_curry", "samosa",
                "veg_biryani", "veg_thali"]:
        picks.append(sorted(glob.glob(
            os.path.join(FIG_BASE, "data", "train", cls, "*.png")))[0])
    picks.append(sorted(glob.glob(
        os.path.join(FIG_BASE, "data", "train", "dosa", "*.png")))[8])
    tiles = [Image.open(x).resize((224, 224)) for x in picks]
    canvas = Image.new("RGB", (224 * 4, 224 * 2), (250, 250, 248))
    d = ImageDraw.Draw(canvas)
    for i, (img, path) in enumerate(zip(tiles, picks)):
        x, y = (i % 4) * 224, (i // 4) * 224
        canvas.paste(img, (x, y))
        d.rectangle([x, y, x + 223, y + 223], outline=(205, 200, 190))
        d.text((x + 8, y + 6), os.path.basename(os.path.dirname(path)),
               fill=(255, 255, 255))
    canvas.save(collage)
    print("built", collage)

# Figure 1: dataset samples before 5.1 Dataset Details heading (P101)
insert_figure(doc, collage, 16.0,
              "Figure 1: One sample per class from the generated dataset "
              "(mobile-augmented, 224×224)", P[101])

# Figure 2: training curves before 5.4 Results heading (P107)
insert_figure(doc, os.path.join(FIG_BASE, "outputs", "training_curves.png"),
              15.5, "Figure 2: Training and validation loss / accuracy over 6 epochs "
                    "(val accuracy saturates at 1.0 by epoch 2)", P[107])

# Figure 3: confusion matrix before 6.1 heading (P111)
insert_figure(doc, os.path.join(FIG_BASE, "results", "confusion_matrix.png"),
              12.5, "Figure 3: Test confusion matrix (7×7, test accuracy 0.991)", P[111])

# =====================================================================
doc.save(OUT)
print("saved", OUT)
