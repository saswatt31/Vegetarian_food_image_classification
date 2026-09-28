"""
Layout audit for Presentation_Vegetarian_Food_Image_Classification.pptx.

Checks every slide for the defects that make a deck look broken:
  1. text overflow   — wrapped text taller than its box (real font metrics)
  2. narrow boxes    — wrapped text wider than its box
  3. off-slide paint — shapes/text bleeding off the canvas (decor excluded)
  4. text collisions — two painted texts overlapping

Font metrics come from the actual Windows fonts (Segoe UI, Georgia),
measured with PIL at 4x precision.

Run:    python check_slides_layout.py
Exit 0 = PASS, 1 = FAIL.
"""
import sys

from PIL import ImageFont
from pptx import Presentation
from pptx.util import Emu

PPTX = "Presentation_Vegetarian_Food_Image_Classification.pptx"
FONT_DIR = "C:\\Windows\\Fonts"
EMU_IN = 914400

_cache = {}

def _font(name, size_pt, bold):
    key = (name, size_pt, bold)
    if key in _cache:
        return _cache[key]
    size4 = int(size_pt * 4)
    files = []
    if "Georgia" in name:
        files = ["georgiab.ttf" if bold else "georgia.ttf"]
    else:
        files = (["segoeuib.ttf"] if bold else ["segoeui.ttf"]) + \
                ["segoeuii.ttf", "arialbd.ttf", "arial.ttf"]
    for fn in files:
        try:
            f = ImageFont.truetype(FONT_DIR + "\\" + fn, size4)
            _cache[key] = f
            return f
        except OSError:
            continue
    f = ImageFont.load_default()
    _cache[key] = f
    return f

def _measure(paragraphs, box_w_in, wrap=True):
    """Return (width_in, height_in) of wrapped text at 4x precision."""
    max_w = 0.0
    total_h = 0.0
    for para in paragraphs:
        runs = para.runs
        if not runs:
            total_h += 0.18
            continue
        size = max((r.font.size.pt if r.font.size else 14) for r in runs)
        bold = any(bool(r.font.bold) for r in runs)
        name = runs[0].font.name or "Segoe UI"
        f = _font(name, size, bold)
        txt = "".join(r.text for r in runs)
        px_w = f.getlength(txt) / 4.0  # back to points
        w_in = px_w / 72.0
        spacing = para.line_spacing if isinstance(para.line_spacing, float) else 1.0
        if wrap and w_in > box_w_in and box_w_in > 0:
            # greedy wrap estimate
            words = txt.split()
            lines, cur = 1, ""
            for word in words:
                trial = (cur + " " + word).strip()
                if f.getlength(trial) / 4.0 / 72.0 <= box_w_in or not cur:
                    cur = trial
                else:
                    lines += 1
                    cur = word
            n_lines = lines
            max_w = max(max_w, box_w_in)
        else:
            n_lines = 1
            max_w = max(max_w, w_in)
        line_h = size * 1.22 * spacing / 72.0
        total_h += n_lines * line_h
    return max_w, total_h

def _walk(shapes):
    for sh in shapes:
        yield sh
        if sh.shape_type == 6:  # group
            yield from _walk(sh.shapes)

def main():
    prs = Presentation(PPTX)
    sw_in = prs.slide_width / EMU_IN
    sh_in = prs.slide_height / EMU_IN
    issues, warnings = [], []

    print("=" * 74)
    print("SLIDE LAYOUT AUDIT")
    print("=" * 74)

    for idx, slide in enumerate(prs.slides, 1):
        boxes = []  # painted text boxes for collision check
        for sh in _walk(slide.shapes):
            if sh.left is None or sh.top is None:
                continue
            x, y = sh.left / EMU_IN, sh.top / EMU_IN
            w = (sh.width or 0) / EMU_IN
            h = (sh.height or 0) / EMU_IN
            label = (sh.name or "shape")[:22]
            is_textbox = sh.has_text_frame and sh.text_frame.text.strip()
            is_autoshape_text = sh.has_text_frame and sh.text_frame.text.strip() and sh.shape_type != 17

            # off-slide check (text and content shapes; decor washes excluded)
            decor = sh.name.lower().startswith(("oval", "rectangle")) and not is_textbox
            if not decor:
                if x < -0.05 or y < -0.05 or x + w > sw_in + 0.05 or y + h > sh_in + 0.05:
                    # pictures/cards/chips must stay on canvas
                    if is_textbox or "Rectangle" in label or "Rounded" in label or sh.shape_type == 13:
                        issues.append(f"slide {idx}: off-slide paint ({label}) at "
                                      f"({x:.2f},{y:.2f}) {w:.2f}x{h:.2f}")
                        continue
                if x + w > sw_in + 0.05 or y + h > sh_in + 0.05:
                    warnings.append(f"slide {idx}: shape bleeds off-slide (decor ok): {label}")

            if not is_textbox:
                continue
            tf = sh.text_frame
            txt = tf.text.strip()
            ml = (tf.margin_left or 0) / EMU_IN
            mr = (tf.margin_right or 0) / EMU_IN
            mt = (tf.margin_top or 0) / EMU_IN
            mb = (tf.margin_bottom or 0) / EMU_IN
            inner_w = w - ml - mr
            inner_h = h - mt - mb
            tw, th = _measure(tf.paragraphs, inner_w, wrap=tf.word_wrap is not False)

            if th > inner_h + 0.06:
                issues.append(
                    f"slide {idx}: text may overflow ({th:.2f}\" in {inner_h:.2f}\"): \"{txt[:48]}\"")
            if tf.word_wrap is False and tw > inner_w + 0.06:
                issues.append(
                    f"slide {idx}: narrow text box ({tw:.2f}\" in {inner_w:.2f}\"): \"{txt[:40]}\"")
            if not tf.word_wrap is False and tw > inner_w + 0.02:
                warnings.append(f"slide {idx}: text wider than box (wraps ok): \"{txt[:36]}\"")
            boxes.append((x + ml, y + mt, tw, th, txt[:26]))

        # painted-text collisions
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                ax, ay, aw, ah, at = boxes[i]
                bx, by, bw, bh, bt = boxes[j]
                ox = min(ax + aw, bx + bw) - max(ax, bx)
                oy = min(ay + ah, by + bh) - max(ay, by)
                if ox > 0.05 and oy > 0.05:
                    issues.append(
                        f"slide {idx}: text boxes overlap (\"{at}\" vs \"{bt}\") over "
                        f"{ox:.2f}x{oy:.2f}\"")

        n_sh = len(slide.shapes)
        print(f"  slide {idx:2d}: {n_sh} shapes")

    print("=" * 74)
    if issues:
        print(f"\nblocking issues: {len(issues)}")
        for it in issues:
            print("   !! " + it)
    if warnings:
        print(f"\nwarnings: {len(warnings)}")
        for wn in warnings:
            print("   -  " + wn)
    print("=" * 74)
    print("RESULT: " + ("PASS - no blocking layout issues" if not issues
                        else f"FAIL - {len(issues)} issue(s)"))
    return 0 if not issues else 1

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
