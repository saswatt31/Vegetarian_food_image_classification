"""
Render the generated PPTX to PNG previews + a base64-embedded HTML gallery
(no PowerPoint/LibreOffice needed — shapes, text and images are drawn with PIL).

Run:    python render_slides_preview.py
Output: slides_preview/slide_XX.png + slides_preview/index.html
"""
import base64
import html
import os
import sys

from PIL import Image, ImageDraw, ImageFont
from pptx import Presentation
from pptx.util import Emu

PPTX = "Presentation_Vegetarian_Food_Image_Classification.pptx"
OUTDIR = "slides_preview"
SCALE = 110  # px per inch
FONT_DIR = "C:\\Windows\\Fonts"

_cache = {}

def _font(name, size_pt, bold):
    key = (name, int(size_pt * SCALE / 72), bold)
    if key in _cache:
        return _cache[key]
    px = max(8, int(size_pt * SCALE / 72))
    files = []
    if "Georgia" in name:
        files = ["georgiab.ttf" if bold else "georgia.ttf"]
    else:
        files = (["segoeuib.ttf"] if bold else ["segoeui.ttf"]) + \
                ["arialbd.ttf", "arial.ttf"]
    for fn in files:
        try:
            f = ImageFont.truetype(FONT_DIR + "\\" + fn, px)
            _cache[key] = f
            return f
        except OSError:
            continue
    f = ImageFont.load_default()
    _cache[key] = f
    return f

def _rgba(color, alpha=None):
    if color is None:
        return None
    r, g, b = color[0], color[1], color[2]
    if alpha is not None:
        return (r, g, b, alpha)
    return (r, g, b)

def _shape_fill_color(sh):
    try:
        if sh.fill.type is not None and str(sh.fill.type) != "MSO_FILL_TYPE.BACKGROUND":
            fc = sh.fill.fore_color
            if fc.type is not None and "RGB" in str(fc.type):
                return fc.rgb
    except (AttributeError, TypeError):
        pass
    return None

def _wrap_runs(draw, runs, max_px):
    """Wrap runs into lines of (text, font, color). Greedy by word."""
    lines, cur, cur_w = [], [], 0
    for txt, fnt, col in runs:
        for piece in txt.replace("\v", "\n").split("\n"):
            words = piece.split(" ")
            for wi, word in enumerate(words):
                token = word if wi == 0 else " " + word
                if token == "" or token == " ":
                    continue
                wpx = draw.textlength(token, font=fnt)
                if cur and cur_w + wpx > max_px and wrap_allowed(token):
                    lines.append((cur, cur_w))
                    cur, cur_w = [], 0
                    token = word  # no leading space on new line
                cur.append((token, fnt, col))
                cur_w += wpx
    if cur:
        lines.append((cur, cur_w))
    return lines

def wrap_allowed(tok):
    return True

def _draw_text_frame(draw, tf, x, y, w, h):
    ml = int((tf.margin_left or 0) / 914400 * SCALE)
    mr = int((tf.margin_right or 0) / 914400 * SCALE)
    mt = int((tf.margin_top or 0) / 914400 * SCALE)
    max_px = w - ml - mr
    yy = y + mt
    for para in tf.paragraphs:
        runs = []
        for r in para.runs:
            size = r.font.size.pt if r.font.size else 14
            bold = bool(r.font.bold)
            name = r.font.name or "Segoe UI"
            col = _rgba(r.font.color.rgb) if r.font.color and r.font.color.type is not None else (35, 30, 20)
            runs.append((r.text, _font(name, size, bold), col))
        if not runs:
            yy += int(0.5 * SCALE * 0.35)
            continue
        line_h = max(f.size for _, f, _ in runs) * 1.22
        spacing = para.line_spacing if isinstance(para.line_spacing, float) else 1.0
        line_h = int(line_h * spacing)
        # align
        wrapped = _wrap_runs(draw, runs, max_px)
        for line, _w in wrapped:
            lx = x + ml
            if para.alignment is not None and "CENTER" in str(para.alignment):
                lx = x + ml + (max_px - _w) // 2
            elif para.alignment is not None and "RIGHT" in str(para.alignment):
                lx = x + ml + max_px - _w
            for tok, fnt, col in line:
                draw.text((lx, yy), tok, font=fnt, fill=col)
                lx += draw.textlength(tok, font=fnt)
            yy += line_h
    return yy

def _walk(shapes):
    for sh in shapes:
        yield sh
        if sh.shape_type == 6:
            yield from _walk(sh.shapes)

def render(prs, path):
    sw = int(prs.slide_width / 914400 * SCALE)
    shh = int(prs.slide_height / 914400 * SCALE)
    img = Image.new("RGB", (sw, shh), (251, 247, 240))
    draw = ImageDraw.Draw(img, "RGBA")
    for sh in _walk(prs.slides[0].shapes):
        x = int(sh.left / 914400 * SCALE)
        y = int(sh.top / 914400 * SCALE)
        w = int((sh.width or 0) / 914400 * SCALE)
        h = int((sh.height or 0) / 914400 * SCALE)
        st = str(sh.shape_type)

        if sh.shape_type == 13:  # picture
            try:
                blob = sh.image.blob
                import io
                pic = Image.open(io.BytesIO(blob)).convert("RGB")
                pic = pic.resize((max(1, w), max(1, h)))
                img.paste(pic, (x, y))
            except Exception:
                draw.rectangle([x, y, x + w, y + h], outline=(180, 180, 180))
            continue

        if "OVAL" in st or sh.name == "Oval":
            col = _shape_fill_color(sh)
            # parse alpha if present
            alpha = _alpha_of(sh)
            if col:
                draw.ellipse([x, y, x + w, y + h], fill=_rgba(col, alpha), outline=None)
            continue

        if "ROUND" in st or "RECTANGLE" in st or "RECT" in st:
            col = _shape_fill_color(sh)
            alpha = _alpha_of(sh)
            line_col = None
            try:
                if sh.line.fill.type is not None and "BACKGROUND" not in str(sh.line.fill.type):
                    line_col = _rgba(sh.line.color.rgb)
            except Exception:
                line_col = None
            rad = int(min(w, h) * (sh.adjustments[0] if sh.adjustments and len(sh.adjustments) else 0.12))
            if "ROUND" in st:
                draw.rounded_rectangle([x, y, x + w, y + h], radius=rad,
                                       fill=_rgba(col, alpha) if col else None,
                                       outline=line_col, width=2)
            else:
                draw.rectangle([x, y, x + w, y + h], fill=_rgba(col, alpha) if col else None,
                               outline=line_col, width=2)
            if sh.has_text_frame and sh.text_frame.text.strip():
                _draw_text_frame(draw, sh.text_frame, x, y, w, h)
            continue

        # freeform / generic: text only
        if sh.has_text_frame and sh.text_frame.text.strip():
            _draw_text_frame(draw, sh.text_frame, x, y, w, h)

def _alpha_of(sh):
    try:
        solid = sh.fill._xPr.find(
            "{http://schemas.openxmlformats.org/drawingml/2006/main}solidFill")
        if solid is None:
            return None
        srgb = solid.find(
            "{http://schemas.openxmlformats.org/drawingml/2006/main}srgbClr")
        if srgb is None:
            return None
        a = srgb.find(
            "{http://schemas.openxmlformats.org/drawingml/2006/main}alpha")
        if a is None:
            return None
        return int(int(a.get("val")) / 1000 * 255 / 100)
    except Exception:
        return None

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    os.makedirs(OUTDIR, exist_ok=True)
    prs = Presentation(PPTX)
    pngs = []
    for idx, slide in enumerate(prs.slides, 1):
        sw = int(prs.slide_width / 914400 * SCALE)
        shh = int(prs.slide_height / 914400 * SCALE)
        img = Image.new("RGB", (sw, shh), (251, 247, 240))
        draw = ImageDraw.Draw(img, "RGBA")
        for sh in _walk(slide.shapes):
            render_one(img, draw, sh)
        p = os.path.join(OUTDIR, f"slide_{idx:02d}.png")
        img.save(p)
        pngs.append(p)
        print("rendered", p)

    # gallery
    cards = []
    for p in pngs:
        b64 = base64.b64encode(open(p, "rb").read()).decode()
        cards.append(f"""
        <figure><img src="data:image/png;base64,{b64}" alt="{p}">
        <figcaption>{os.path.basename(p)}</figcaption></figure>""")
    doc = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
    <title>Deck preview — {html.escape(PPTX)}</title>
    <style>
      body {{ background:#EDE9E0; font-family:Segoe UI, sans-serif; margin:24px; }}
      h1 {{ font-size:18px; color:#333; }}
      figure {{ margin:0 0 26px; }}
      img {{ width:100%; max-width:1280px; border-radius:10px;
             box-shadow:0 8px 30px rgba(0,0,0,.18); display:block; }}
      figcaption {{ font-size:12px; color:#666; padding:6px 2px; }}
    </style></head><body>
    <h1>{html.escape(PPTX)} — {len(pngs)} slides (PIL preview)</h1>
    {''.join(cards)}
    </body></html>"""
    with open(os.path.join(OUTDIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(doc)
    print("gallery:", os.path.join(OUTDIR, "index.html"))

def render_one(img, draw, sh):
    """Draw one top-level shape (recursing into groups) onto img."""
    if sh.shape_type == 6:
        for sub in sh.shapes:
            render_one(img, draw, sub)
        return
    x = int(sh.left / 914400 * SCALE)
    y = int(sh.top / 914400 * SCALE)
    w = int((sh.width or 0) / 914400 * SCALE)
    h = int((sh.height or 0) / 914400 * SCALE)

    if sh.shape_type == 13:  # picture
        try:
            import io
            pic = Image.open(io.BytesIO(sh.image.blob)).convert("RGB")
            pic = pic.resize((max(1, w), max(1, h)))
            img.paste(pic, (x, y))
        except Exception:
            draw.rectangle([x, y, x + w, y + h], outline=(180, 180, 180))
        return

    # autoshape geometry (OVAL / ROUNDED_RECTANGLE / RECTANGLE / TRIANGLE)
    geom = ""
    try:
        if sh.shape_type == 1:  # AUTO_SHAPE
            geom = str(sh.auto_shape_type).upper()
    except Exception:
        geom = ""
    if not geom:
        if sh.has_text_frame and sh.text_frame.text.strip():
            _draw_text_frame(draw, sh.text_frame, x, y, w, h)
        return

    col = _shape_fill_color(sh)
    alpha = _alpha_of(sh)
    line_col = None
    try:
        if sh.line.fill.type is not None and "BACKGROUND" not in str(sh.line.fill.type):
            line_col = _rgba(sh.line.color.rgb)
    except Exception:
        line_col = None

    if "OVAL" in geom:
        if col:
            draw.ellipse([x, y, x + w, y + h], fill=_rgba(col, alpha))
        return
    if "TRIANGLE" in geom:
        draw.polygon([(x + w / 2, y), (x + w, y + h), (x, y + h)],
                     fill=_rgba(col, alpha) if col else None, outline=line_col)
        return
    rad = 0
    if "ROUNDED" in geom:
        try:
            if sh.adjustments and len(sh.adjustments):
                rad = int(min(w, h) * sh.adjustments[0])
        except Exception:
            rad = 0
    fill_rgba = _rgba(col, alpha) if col else None
    if "ROUNDED" in geom:
        draw.rounded_rectangle([x, y, x + w, y + h], radius=max(1, rad),
                               fill=fill_rgba, outline=line_col, width=2)
    else:
        draw.rectangle([x, y, x + w, y + h], fill=fill_rgba, outline=line_col, width=2)
    if sh.has_text_frame and sh.text_frame.text.strip():
        _draw_text_frame(draw, sh.text_frame, x, y, w, h)

if __name__ == "__main__":
    main()
