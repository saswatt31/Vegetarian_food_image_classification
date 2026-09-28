"""
Compliance checker: verifies that the generated food-classification report
follows the official template (all placeholders resolved, correct headings,
tables filled with real values, figures + code snippets + references present).

Run:    python check_report_template.py
Exit 0 = PASS, 1 = FAIL.
"""
import re
import sys

from docx import Document

OUT = "Project_Report_Vegetarian_Food_Image_Classification.docx"

EXPECTED_H1 = [
    "1. INTRODUCTION",
    "2. LITERATURE REVIEW & EXISTING SYSTEM",
    "3. PROPOSED SYSTEM / METHODOLOGY",
    "4. SYSTEM DESIGN & IMPLEMENTATION",
    "5. EXPERIMENTAL SETUP & RESULTS",
    "6. RESULTS ANALYSIS & DISCUSSION",
    "7. CONCLUSION, FUTURE SCOPE & REFERENCES",
]
H2 = {1: 5, 2: 4, 3: 5, 4: 4, 5: 4, 6: 6, 7: 4}   # h2 count per h1 section

PLACEHOLDER_RE = re.compile(
    r"\[Stage \d|\[Layer type|\[Size\]|\[Value\]|\[Objective|\[Limitation|"
    r"\[Baseline model\]|\[Proposed model\]|\[Student Name|\[Roll No|"
    r"\[PROJECT TITLE|\[One-line subtitle|\[Guide|\[Department|\[Faculty|"
    r"\[Academic Year|\[Course Name|\[Paragraph \d|\[Describe|\[Explain|"
    r"\[State|\[Define|\[Summarize|\[Paste|\[Preprocessing step|\[Step \d|"
    r"\[Future direction|\[e\.g\.|\[Author|\[Title\]|\[Conference|"
    r"\[Localization/Output\]|\[Semester|\[Programme\]|\[X\]|\[20XX|"
    r"LOREM|TODO|XXX")


def paragraphs_with_tables(doc):
    items = []
    for p in doc.paragraphs:
        items.append(("p", p))
    return items


def main():
    doc = Document(OUT)
    errors, warnings, checks = [], [], 0

    def ok(cond, msg, warn=False):
        nonlocal checks
        checks += 1
        if not cond:
            (warnings if warn else errors).append(msg)

    # ---- 1. no unresolved placeholders in any paragraph or table cell ----
    def all_text():
        for p in doc.paragraphs:
            yield p.text
        for t in doc.tables:
            for row in t.rows:
                for c in row.cells:
                    yield c.text

    bad = [t[:70] for t in all_text() if t.strip() and PLACEHOLDER_RE.search(t)]
    ok(not bad, f"unresolved placeholders: {bad[:4]}", warn=False)

    # ---- 2. required H1 headings present, in order ----
    h1 = [p.text.strip() for p in doc.paragraphs
          if p.style is not None and p.style.name == "Heading 1"]
    ok(h1 == EXPECTED_H1, f"H1 mismatch: {h1}")

    # ---- 3. H2 counts per section ----
    h2_by_section, cur = {}, None
    for p in doc.paragraphs:
        sn = p.style.name if p.style else ""
        if sn == "Heading 1":
            cur = p.text.strip()
            h2_by_section[cur] = 0
        elif sn == "Heading 2" and cur:
            h2_by_section[cur] += 1
    for i, name in enumerate(EXPECTED_H1, start=1):
        ok(h2_by_section.get(name) == H2[i],
           f"{name}: {h2_by_section.get(name)} H2 (expect {H2[i]})", warn=False)

    # ---- 4. section 6.2 heading has no bracketed choice left ----
    ok(any("6.2 Predictions and" in p.text and "[" not in p.text
           for p in doc.paragraphs),
       "6.2 heading must resolve the [Localization/Output] choice")

    # ---- 5. tables: 5 tables, all cells non-empty & placeholder-free ----
    ok(len(doc.tables) == 5, f"expected 5 tables, found {len(doc.tables)}")
    tmap = {i: [[c.text.strip() for c in r.cells] for r in t.rows]
            for i, t in enumerate(doc.tables)}
    ok(tmap[0][0] == ["Name", "Roll No."], "team table header")
    ok(len(tmap[0]) == 5 and all(all(v and "[" not in v for v in row)
                                 for row in tmap[0][1:]),
       "team table rows filled")
    ok(tmap[1][0][0] == "Stage", "arch table header")
    ok(all(all(v for v in row) for row in tmap[1]), "arch table filled")
    ok(tmap[2][0] == ["Parameter", "Value"], "training-config header")
    ok(all(all(v for v in row) for row in tmap[2]), "training config filled")
    ok(tmap[3][0] == ["Model", "Accuracy", "Precision", "Recall", "F1-Score"],
       "results header")
    ok(any("0.9911" in c for row in tmap[3] for c in row),
       "results table carries the real accuracy")
    ok("ImageNet transfer (proposed)" in " ".join(tmap[3][2]),
       "proposed row present")
    ok("random init" in " ".join(tmap[3][1]), "baseline row present")

    # ---- 6. code snippets: >= 2 Consolas runs ----
    consolas = 0
    for p in doc.paragraphs:
        for r in p.runs:
            if r.font.name == "Consolas":
                consolas += 1
                break
    ok(consolas >= 2, f"expected >=2 Consolas code paragraphs, found {consolas}")

    # ---- 7. figures: >=3 inline images + captions ----
    images = doc.inline_shapes
    ok(len(images) >= 3, f"expected >=3 figures, found {len(images)}")
    caps = sum(1 for p in doc.paragraphs
               if p.text.strip().lower().startswith("figure "))
    ok(caps >= 3, f"expected >=3 'Figure N:' captions, found {caps}")

    # ---- 8. references ----
    refs = [p.text for p in doc.paragraphs
            if re.match(r"\[\d\]", p.text.strip())]
    ok(len(refs) >= 3, f"expected >=3 references, found {len(refs)}")

    # ---- 9. front matter filled ----
    P = doc.paragraphs
    ok("VEGETARIAN FOOD" in P[1].text, "title set")
    ok("Rahul Rawat" in P[8].text, "guide set")
    ok("2023 – 2027" in P[11].text, "academic year set")
    ok(all(n in P[1].text + " ".join(c.text for c in doc.tables[0].rows[1].cells)
           for n in ["Saswat"]), "student names in team table")

    # ---- 10. abstract length sanity ----
    abstract = P[31].text + P[32].text + P[33].text + P[34].text
    ok(len(abstract.split()) >= 200, f"abstract too short ({len(abstract.split())} words)")

    # ---- prose volume ----
    words = sum(len(p.text.split()) for p in doc.paragraphs)
    print(f"prose (approx): {words} words | figures: {len(images)} | "
          f"tables: {len(doc.tables)} | refs: {len(refs)}")

    print()
    if errors:
        print("FAIL —", len(errors), "error(s)")
        for e in errors:
            print("  ✗", e)
        for w in warnings:
            print("  ⚠", w)
        sys.exit(1)
    print(f"PASS — {checks} checks, 0 errors, {len(warnings)} warnings")


if __name__ == "__main__":
    main()
