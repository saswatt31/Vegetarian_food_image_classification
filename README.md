# Vegetarian Food Image Classification Using Transfer Learning
*(real photographs — Indian Food Images dataset)*

Classifies **8 Indian vegetarian dishes** from **real food photographs** using a
two-stage fine-tuned **ResNet-18** (PyTorch + torchvision, ImageNet weights).
**No synthetic or generated images are used anywhere in this pipeline.**

## Results (real, from this machine's runs)

| Metric | Value |
|---|---|
| Corpus (downloaded, validated) | **6,269** real photos, 20 classes, 0 corrupted |
| Vegetarian subset | **2,000** photos — 8 classes × 250 |
| Split | 1,400 / 296 / 304 (70/15/15, stratified, deduped) |
| Stage 1 (frozen backbone) val acc | 0.8277 |
| Stage 2 (fine-tuned layer3+4) val acc | **0.9122** (best checkpoint) |
| **Test accuracy** (unseen 304 photos) | **0.8849** |
| Macro precision / recall / F1 | 0.8924 / 0.8849 / **0.8860** |
| Meal categories | Breakfast 0.886 · Snack 0.895 · Main Meal 0.877 |

Selected classes (all verified present in the corpus): `chapati, dhokla, idli,
kadai_paneer, masala_dosa, pakode, pav_bhaji, samosa`.
Vegetarian assumptions are documented in `src/build_subset.py` and the report
(all lacto-vegetarian; ambiguous `kaathi_rolls` deliberately excluded).

## Project structure
```
├── data/          train/ validation/ test/  (curated real-photo subset)
│   └── split_summary.json
├── raw/           parquet shards + extracted corpus + dataset_stats.json
├── src/           prepare_data.py  build_subset.py  dataset.py  model.py
│                  train.py  evaluate.py  predict.py
├── app/           index.html + server.py   (upload-a-photo demo)
├── models/        best_model.pth  class_names.json
├── results/       training_loss.png  accuracy_curve.png  confusion_matrix.png
│                  classification_report.txt  test_metrics.json
│                  test_predictions.json  sample_predictions.png
│                  dataset_samples_grid.png  training_history.json
├── report/        make_report.py  check_report_template.py
│                  make_slides.py  check_slides_layout.py  render_slides_preview.py
├── notebooks/     exploration notebook
├── legacy_synthetic/   (archived earlier synthetic-data prototype — not part
│                        of this pipeline, kept only for history)
├── requirements.txt
└── README.md
```

## How to run

```bash
pip install -r requirements.txt

# 1. extract + validate the real-photo corpus (needs raw/*.parquet, see below)
python src/prepare_data.py --extract
python src/prepare_data.py --validate

# 2. curate the vegetarian subset (dedupe + stratified 70/15/15)
python src/build_subset.py

# 3. two-stage training (frozen head -> layer3+4 fine-tune), CPU ~13 min
python src/train.py

# 4. evaluate on the unseen test split
python src/evaluate.py

# 5. single-image prediction
python src/predict.py path/to/photo.jpg

# 6. upload demo
python app/server.py            # open http://localhost:8000
```

### Dataset source
`raw/train.parquet` + `raw/test.parquet` are the **Indian Food Images** corpus
(4,000–6,269 real photographs depending on distribution; the HuggingFace mirror
`rajistics/indian_food_images` used here ships 6,269 images across 20 classes).
Download with:
```bash
curl -L -o raw/train.parquet "https://huggingface.co/datasets/rajistics/indian_food_images/resolve/main/data/train-00000-of-00001-dbae6752a5d31c49.parquet"
curl -L -o raw/test.parquet  "https://huggingface.co/datasets/rajistics/indian_food_images/resolve/main/data/test-00000-of-00001-899c7c7e401d279b.parquet"
```

## Deliverables
1. **Project report** — `Project_Report_Vegetarian_Food_Image_Classification.docx`
   (official template filled in place; compliance-checked: `python report/check_report_template.py` → PASS)
2. **Presentation** — `Presentation_Vegetarian_Food_Image_Classification.pptx`
   (10 slides, light theme; layout-audited: `python report/check_slides_layout.py` → PASS;
   PNG previews in `slides_preview/index.html`)
3. **Upload demo** — `python app/server.py` → http://localhost:8000
