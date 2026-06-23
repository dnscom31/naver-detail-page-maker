from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import math

from PIL import Image, ImageDraw, ImageFont, ImageOps

MAX_JPEG_HEIGHT = 60000
MAX_EXTRA_IMAGES = 30
STANDARD_CARD_MARGIN = 34
STANDARD_CARD_PADDING = 18
STANDARD_CARD_RADIUS = 16


FONT_CANDIDATES = {
    "sans_regular": [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ],
    "sans_bold": [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ],
    "serif_regular": [
        "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
        "/usr/share/fonts/truetype/nanum/NanumMyeongjo.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    ],
    "serif_bold": [
        "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc",
        "/usr/share/fonts/truetype/nanum/NanumMyeongjoBold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    ],
}


def _hex(color: str) -> Tuple[int, int, int]:
    color = color.lstrip("#")
    if len(color) == 3:
        color = "".join(ch * 2 for ch in color)
    return tuple(int(color[i : i + 2], 16) for i in (0, 2, 4))


def _font_path(kind: str) -> str:
    for candidate in FONT_CANDIDATES[kind]:
        if Path(candidate).exists():
            return candidate
    raise FileNotFoundError(
        "한글 폰트를 찾지 못했습니다. GitHub 저장소에 packages.txt 파일을 추가하고 "
        "fonts-noto-cjk를 설치해야 합니다."
    )


def get_font(font_choice: str, size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    serif = font_choice in {"명조 계열", "바탕"}
    kind = f"{'serif' if serif else 'sans'}_{'bold' if bold else 'regular'}"
    return ImageFont.truetype(_font_path(kind), size=size)


def _text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> int:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0]


def _line_height(draw: ImageDraw.ImageDraw, font: ImageFont.FreeTypeFont) -> int:
    box = draw.textbbox((0, 0), "가Ag", font=font)
    return max(1, box[3] - box[1])


def wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
) -> List[str]:
    result: List[str] = []
    for paragraph in str(text).splitlines() or [""]:
        if not paragraph:
            result.append("")
            continue
        current = ""
        for char in paragraph:
            trial = current + char
            if current and _text_width(draw, trial, font) > max_width:
                result.append(current.rstrip())
                current = char.lstrip()
            else:
                current = trial
        if current or not result:
            result.append(current.rstrip())
    return result


def draw_wrapped(
    draw: ImageDraw.ImageDraw,
    xy: Tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: Tuple[int, int, int],
    max_width: int,
    align: str = "left",
    line_gap: int = 10,
) -> int:
    x, y = xy
    lines = wrap_text(draw, text, font, max_width)
    line_h = _line_height(draw, font)
    for line in lines:
        w = _text_width(draw, line, font)
        if align == "center":
            tx = x + (max_width - w) // 2
        elif align == "right":
            tx = x + max_width - w
        else:
            tx = x
        draw.text((tx, y), line, font=font, fill=fill)
        y += line_h + line_gap
    return len(lines) * line_h + max(0, len(lines) - 1) * line_gap


def text_height(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
    line_gap: int = 10,
) -> int:
    lines = wrap_text(draw, text, font, max_width)
    line_h = _line_height(draw, font)
    return len(lines) * line_h + max(0, len(lines) - 1) * line_gap


def uploaded_to_image(uploaded) -> Image.Image | None:
    if uploaded is None:
        return None
    try:
        image = Image.open(BytesIO(uploaded.getvalue()))
        image = ImageOps.exif_transpose(image)
        return image.convert("RGB")
    except Exception:
        return None




def _sample_background_color(image: Image.Image) -> Tuple[int, int, int]:
    rgb = image.convert("RGB")
    w, h = rgb.size
    sample_points = [
        (0, 0),
        (w - 1, 0),
        (0, h - 1),
        (w - 1, h - 1),
        (w // 2, 0),
        (w // 2, h - 1),
        (0, h // 2),
        (w - 1, h // 2),
    ]
    colors = [rgb.getpixel((max(0, min(w - 1, x)), max(0, min(h - 1, y)))) for x, y in sample_points]
    return tuple(int(sum(channel) / len(colors)) for channel in zip(*colors))


def _detect_subject_bbox(image: Image.Image) -> Tuple[float, float, float, float] | None:
    rgb = image.convert("RGB")
    src_w, src_h = rgb.size
    if src_w == 0 or src_h == 0:
        return None

    bg = _sample_background_color(rgb)
    preview = rgb.copy()
    preview.thumbnail((420, 420), Image.Resampling.LANCZOS)
    px = preview.load()
    pw, ph = preview.size
    xs, ys = [], []

    threshold = 28
    for y in range(ph):
        for x in range(pw):
            r, g, b = px[x, y]
            diff = abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2])
            if diff > threshold * 3:
                xs.append(x)
                ys.append(y)

    if not xs or not ys:
        return None

    left_p, right_p = min(xs), max(xs)
    top_p, bottom_p = min(ys), max(ys)
    scale_x = src_w / pw
    scale_y = src_h / ph
    return (left_p * scale_x, top_p * scale_y, right_p * scale_x, bottom_p * scale_y)


def suggest_square_crop_params(image: Image.Image | None, mode: str = "자동") -> Dict[str, float]:
    if image is None:
        return {"zoom": 1.0, "offset_x": 0.0, "offset_y": 0.0, "trim": 0.0}

    rgb = image.convert("RGB")
    src_w, src_h = rgb.size
    side_base = min(src_w, src_h)
    bbox = _detect_subject_bbox(rgb)

    inferred_mode = mode
    if mode == "자동" and bbox is not None:
        bbox_w = max(1.0, bbox[2] - bbox[0])
        bbox_h = max(1.0, bbox[3] - bbox[1])
        occupancy = max(bbox_w / src_w, bbox_h / src_h)
        inferred_mode = "마네킹컷" if occupancy > 0.78 else "모델컷"

    if bbox is not None:
        bbox_w = max(1.0, bbox[2] - bbox[0])
        bbox_h = max(1.0, bbox[3] - bbox[1])

        if inferred_mode == "마네킹컷":
            desired_side = max(bbox_w, bbox_h) * 1.04
            desired_side = max(side_base * 0.90, min(side_base, desired_side))
            zoom = max(1.0, min(1.12, side_base / desired_side))
            center_x = (bbox[0] + bbox[2]) / 2
            center_y = (bbox[1] + bbox[3]) / 2
            trim = 8.0
        else:
            desired_side = max(bbox_w, bbox_h) * 1.15
            desired_side = max(side_base * 0.72, min(side_base, desired_side))
            zoom = max(1.0, min(1.45, side_base / desired_side))
            center_x = (bbox[0] + bbox[2]) / 2
            center_y = (bbox[1] + bbox[3]) / 2 - desired_side * 0.04
            trim = 4.0
    else:
        zoom = 1.0
        center_x = src_w / 2
        center_y = src_h / 2
        trim = 0.0

    crop_side = side_base / max(1.0, zoom)
    max_shift_x = max(0.0, (src_w - crop_side) / 2)
    max_shift_y = max(0.0, (src_h - crop_side) / 2)
    offset_x = 0.0 if max_shift_x == 0 else ((center_x - src_w / 2) / max_shift_x) * 100
    offset_y = 0.0 if max_shift_y == 0 else ((center_y - src_h / 2) / max_shift_y) * 100
    offset_x = max(-100.0, min(100.0, offset_x))
    offset_y = max(-100.0, min(100.0, offset_y))
    return {"zoom": round(float(zoom), 2), "offset_x": round(float(offset_x), 1), "offset_y": round(float(offset_y), 1), "trim": trim}


def _trim_edges(image: Image.Image, trim_percent: float) -> Image.Image:
    src = image.convert("RGB")
    if trim_percent <= 0:
        return src

    w, h = src.size
    trim_x = int(w * (trim_percent / 100.0) / 2)
    trim_y = int(h * (trim_percent / 100.0) / 2)
    left = min(max(0, trim_x), max(0, w - 2))
    top = min(max(0, trim_y), max(0, h - 2))
    right = max(left + 1, w - trim_x)
    bottom = max(top + 1, h - trim_y)
    return src.crop((left, top, right, bottom))


def _edge_extend_canvas(image: Image.Image, canvas_size: int, bg_color: Tuple[int, int, int] = (255, 255, 255)) -> Image.Image:
    """원본 비율을 유지해 정사각형에 배치하고, 남는 영역은 사진 가장자리 픽셀을 늘려 채웁니다.

    resize 크기 중 하나가 0이면 Pillow에서 ValueError가 발생하므로,
    상/하/좌/우 여백이 0인 경우 해당 확장 처리를 건너뜁니다.
    """
    src = image.convert("RGB")
    ratio = min(canvas_size / src.width, canvas_size / src.height)
    new_w = max(1, int(src.width * ratio))
    new_h = max(1, int(src.height * ratio))
    fitted = src.resize((new_w, new_h), Image.Resampling.LANCZOS)

    canvas = Image.new("RGB", (canvas_size, canvas_size), bg_color)
    x = (canvas_size - new_w) // 2
    y = (canvas_size - new_h) // 2
    canvas.paste(fitted, (x, y))

    if new_w < canvas_size:
        left_margin = max(0, x)
        right_margin = max(0, canvas_size - (x + new_w))

        if left_margin > 0:
            left_strip = fitted.crop((0, 0, 1, new_h)).resize((left_margin, new_h), Image.Resampling.BILINEAR)
            canvas.paste(left_strip, (0, y))

        if right_margin > 0:
            right_strip = fitted.crop((new_w - 1, 0, new_w, new_h)).resize((right_margin, new_h), Image.Resampling.BILINEAR)
            canvas.paste(right_strip, (x + new_w, y))

    if new_h < canvas_size:
        top_margin = max(0, y)
        bottom_margin = max(0, canvas_size - (y + new_h))

        if top_margin > 0:
            top_strip = canvas.crop((0, y, canvas_size, y + 1)).resize((canvas_size, top_margin), Image.Resampling.BILINEAR)
            canvas.paste(top_strip, (0, 0))

        if bottom_margin > 0:
            bottom_strip = canvas.crop((0, y + new_h - 1, canvas_size, y + new_h)).resize((canvas_size, bottom_margin), Image.Resampling.BILINEAR)
            canvas.paste(bottom_strip, (0, y + new_h))

    return canvas


def render_square_image(
    image: Image.Image,
    canvas_size: int = 1000,
    zoom: float = 1.0,
    offset_x: float = 0.0,
    offset_y: float = 0.0,
    bg_color: Tuple[int, int, int] = (255, 255, 255),
    mode: str = "자동",
    trim_percent: float = 0.0,
) -> Image.Image:
    src = _trim_edges(image, trim_percent)
    src_w, src_h = src.size

    if mode == "마네킹컷":
        return _edge_extend_canvas(src, canvas_size, bg_color)

    if mode == "자동":
        bbox = _detect_subject_bbox(src)
        if bbox is not None:
            bbox_w = bbox[2] - bbox[0]
            bbox_h = bbox[3] - bbox[1]
            if max(bbox_w / src_w, bbox_h / src_h) > 0.78:
                return _edge_extend_canvas(src, canvas_size, bg_color)

    side_base = float(min(src_w, src_h))
    zoom = max(1.0, min(2.0, float(zoom)))
    crop_side = max(1.0, side_base / zoom)

    base_x = src_w / 2
    base_y = src_h / 2
    auto = suggest_square_crop_params(src, mode="모델컷" if mode == "모델컷" else "자동")
    if auto:
        auto_side = side_base / max(1.0, float(auto.get("zoom", 1.0)))
        auto_shift_x = max(0.0, (src_w - auto_side) / 2)
        auto_shift_y = max(0.0, (src_h - auto_side) / 2)
        base_x = src_w / 2 + auto_shift_x * float(auto.get("offset_x", 0.0)) / 100.0
        base_y = src_h / 2 + auto_shift_y * float(auto.get("offset_y", 0.0)) / 100.0

    max_shift_x = max(0.0, (src_w - crop_side) / 2)
    max_shift_y = max(0.0, (src_h - crop_side) / 2)
    center_x = base_x + max_shift_x * (float(offset_x) / 100.0)
    center_y = base_y + max_shift_y * (float(offset_y) / 100.0)

    half = crop_side / 2
    left = min(max(0.0, center_x - half), max(0.0, src_w - crop_side))
    top = min(max(0.0, center_y - half), max(0.0, src_h - crop_side))
    crop = src.crop((int(round(left)), int(round(top)), int(round(left + crop_side)), int(round(top + crop_side))))
    crop = crop.resize((canvas_size, canvas_size), Image.Resampling.LANCZOS)

    canvas = Image.new("RGB", (canvas_size, canvas_size), bg_color)
    canvas.paste(crop, (0, 0))
    return canvas


def square_image_bytes(
    uploaded,
    canvas_size: int = 1000,
    zoom: float = 1.0,
    offset_x: float = 0.0,
    offset_y: float = 0.0,
    quality: int = 95,
    mode: str = "자동",
    trim_percent: float = 0.0,
) -> bytes | None:
    image = uploaded_to_image(uploaded)
    if image is None:
        return None

    result = render_square_image(
        image,
        canvas_size=canvas_size,
        zoom=zoom,
        offset_x=offset_x,
        offset_y=offset_y,
        mode=mode,
        trim_percent=trim_percent,
    )
    buffer = BytesIO()
    result.save(buffer, format="JPEG", quality=int(quality), optimize=True, progressive=True, subsampling=1)
    return buffer.getvalue()



def fit_into_box(image: Image.Image, box_width: int, box_height: int) -> Image.Image:
    ratio = min(box_width / image.width, box_height / image.height)
    new_w = max(1, int(image.width * ratio))
    new_h = max(1, int(image.height * ratio))
    return image.resize((new_w, new_h), Image.Resampling.LANCZOS)


def make_uniform_image_block(
    uploaded,
    width: int,
    bg: str,
    box_height: int = 980,
) -> Image.Image | None:
    image = uploaded_to_image(uploaded)
    if image is None:
        return None

    margin_x = 28
    pad_y = 18
    block = solid_block(width, box_height + pad_y * 2, bg)
    inner_w = width - margin_x * 2
    inner_h = box_height
    fitted = fit_into_box(image, inner_w, inner_h)

    x = margin_x + (inner_w - fitted.width) // 2
    y = pad_y + (inner_h - fitted.height) // 2
    block.paste(fitted, (x, y))
    return block


def make_uniform_two_image_block(
    left_file,
    right_file,
    width: int,
    bg: str,
    box_height: int = 760,
    gap: int = 16,
) -> Image.Image | None:
    files = [f for f in [left_file, right_file] if f is not None]
    if not files:
        return None
    if len(files) == 1:
        return make_uniform_image_block(files[0], width, bg, box_height=box_height)

    margin_x = 28
    pad_y = 18
    inner_w = width - margin_x * 2
    cell_w = (inner_w - gap) // 2
    cell_h = box_height
    block = solid_block(width, box_height + pad_y * 2, bg)

    x = margin_x
    for uploaded in files:
        img = uploaded_to_image(uploaded)
        if img is None:
            x += cell_w + gap
            continue
        fitted = fit_into_box(img, cell_w, cell_h)
        y = pad_y + (cell_h - fitted.height) // 2
        block.paste(fitted, (x + (cell_w - fitted.width) // 2, y))
        x += cell_w + gap
    return block


def make_uniform_gallery(
    files: Sequence,
    width: int,
    bg: str,
    columns: int = 1,
    gap: int = 16,
    box_height: int = 820,
) -> Image.Image | None:
    valid = [f for f in files if f is not None]
    if not valid:
        return None

    blocks: List[Image.Image] = []
    if columns <= 1:
        for uploaded in valid:
            block = make_uniform_image_block(uploaded, width, bg, box_height=box_height)
            if block is not None:
                blocks.append(block)
    else:
        for i in range(0, len(valid), columns):
            row_files = valid[i : i + columns]
            if len(row_files) == 1:
                block = make_uniform_image_block(row_files[0], width, bg, box_height=box_height)
            else:
                block = make_uniform_two_image_block(row_files[0], row_files[1], width, bg, box_height=box_height, gap=gap)
            if block is not None:
                blocks.append(block)

    return stitch(blocks, width, bg, gap=gap) if blocks else None



def fit_image(
    image: Image.Image,
    target_width: int,
    max_height: int = 1150,
) -> Image.Image:
    ratio = target_width / image.width
    new_h = max(1, int(image.height * ratio))
    if new_h > max_height:
        ratio = max_height / image.height
        new_w = max(1, int(image.width * ratio))
        resized = image.resize((new_w, max_height), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (target_width, max_height), "white")
        canvas.paste(resized, ((target_width - new_w) // 2, 0))
        return canvas
    return image.resize((target_width, new_h), Image.Resampling.LANCZOS)


def solid_block(width: int, height: int, color: str) -> Image.Image:
    return Image.new("RGB", (width, max(1, height)), _hex(color))


def make_heading_block(
    width: int,
    bg: str,
    point: str,
    text_color: str,
    muted: str,
    heading_font: str,
    body_font: str,
    label: str,
    title: str,
    description: str = "",
    align: str = "center",
    padding_top: int = 60,
    padding_bottom: int = 42,
    base_size: int = 17,
) -> Image.Image:
    temp = Image.new("RGB", (width, 10), "white")
    draw = ImageDraw.Draw(temp)
    label_font = get_font(body_font, max(13, base_size - 3), bold=True)
    title_font = get_font(heading_font, max(28, int(base_size * 2.0)), bold=True)
    desc_font = get_font(body_font, base_size)
    inner_w = width - 100
    label_h = text_height(draw, label, label_font, inner_w, 4)
    title_h = text_height(draw, title, title_font, inner_w, 12)
    desc_h = text_height(draw, description, desc_font, inner_w, 8) if description else 0
    height = padding_top + label_h + 14 + title_h + (18 + desc_h if description else 0) + padding_bottom
    block = solid_block(width, height, bg)
    draw = ImageDraw.Draw(block)
    x = 50
    y = padding_top
    draw_wrapped(draw, (x, y), label, label_font, _hex(point), inner_w, align, 4)
    y += label_h + 14
    draw_wrapped(draw, (x, y), title, title_font, _hex(text_color), inner_w, align, 12)
    y += title_h
    if description:
        y += 18
        draw_wrapped(draw, (x, y), description, desc_font, _hex(muted), inner_w, align, 8)
    return block


def make_hero(
    width: int,
    theme: Dict[str, str],
    config: Dict,
    hero_file,
) -> List[Image.Image]:
    temp = Image.new("RGB", (width, 10), "white")
    draw = ImageDraw.Draw(temp)
    body_choice = config["body_font"]
    heading_choice = config["heading_font"]
    label_font = get_font(body_choice, max(13, config["base_font_size"] - 3), bold=True)
    title_font = get_font(heading_choice, max(34, int(config["base_font_size"] * 2.45)), bold=True)
    sub_font = get_font(body_choice, config["base_font_size"] + 1)
    inner_w = width - 100
    brand_h = text_height(draw, config["brand_line"], label_font, inner_w, 4)
    title_h = text_height(draw, config["main_title"], title_font, inner_w, 14)
    sub_h = text_height(draw, config["main_subtitle"], sub_font, inner_w, 9)
    height = 70 + brand_h + 16 + title_h + 22 + sub_h + 58
    canvas = solid_block(width, height, theme["hero_bg"])
    d = ImageDraw.Draw(canvas)
    y = 70
    draw_wrapped(d, (50, y), config["brand_line"], label_font, _hex(theme["point"]), inner_w, "center", 4)
    y += brand_h + 16
    draw_wrapped(d, (50, y), config["main_title"], title_font, _hex(theme["hero_text"]), inner_w, "center", 14)
    y += title_h + 22
    subtitle_color = "#e3e3e3" if config["theme"] == "모던 블랙" else theme["muted"]
    draw_wrapped(d, (50, y), config["main_subtitle"], sub_font, _hex(subtitle_color), inner_w, "center", 9)
    blocks = [canvas]
    hero = uploaded_to_image(hero_file)
    if hero is not None:
        blocks.append(fit_image(hero, width, 1300))
    return blocks


def make_badges(width: int, theme: Dict[str, str], config: Dict) -> Image.Image:
    badges = [
        (config["badge1_title"], config["badge1_text"]),
        (config["badge2_title"], config["badge2_text"]),
        (config["badge3_title"], config["badge3_text"]),
    ]
    cell_w = width // 3
    height = 170
    block = solid_block(width, height, theme["section_bg"])
    draw = ImageDraw.Draw(block)
    title_font = get_font(config["body_font"], config["base_font_size"] + 1, bold=True)
    text_font = get_font(config["body_font"], max(13, config["base_font_size"] - 3))
    for idx, (title, text) in enumerate(badges):
        x0 = idx * cell_w
        if idx:
            draw.line((x0, 0, x0, height), fill=_hex(theme["line"]), width=1)
        inner = cell_w - 32
        title_h = text_height(draw, title, title_font, inner, 6)
        text_h = text_height(draw, text, text_font, inner, 5)
        y = (height - title_h - 8 - text_h) // 2
        draw_wrapped(draw, (x0 + 16, y), title, title_font, _hex(theme["text"]), inner, "center", 6)
        y += title_h + 8
        draw_wrapped(draw, (x0 + 16, y), text, text_font, _hex(theme["muted"]), inner, "center", 5)
    return block


def make_list_section(
    width: int,
    theme: Dict[str, str],
    config: Dict,
    label: str,
    title: str,
    items: Sequence[str],
    soft: bool = True,
) -> Image.Image:
    bg = theme["soft_bg"] if soft else theme["section_bg"]
    text_color = "#f2f2f2" if soft and config["theme"] == "모던 블랙" else theme["text"]
    muted = "#c8c8c8" if soft and config["theme"] == "모던 블랙" else theme["muted"]
    head = make_heading_block(
        width,
        bg,
        theme["point"],
        text_color,
        muted,
        config["heading_font"],
        config["body_font"],
        label,
        title,
        align="center",
        padding_bottom=28,
        base_size=config["base_font_size"],
    )
    temp = Image.new("RGB", (width, 10), "white")
    draw = ImageDraw.Draw(temp)
    font = get_font(config["body_font"], config["base_font_size"])
    inner_w = width - 140
    item_heights = [max(34, text_height(draw, item, font, inner_w - 42, 8) + 24) for item in items]
    body_h = sum(item_heights) + 60
    body = solid_block(width, body_h, bg)
    d = ImageDraw.Draw(body)
    y = 20
    x = 70
    d.line((x, y, width - x, y), fill=_hex(theme["line"]), width=1)
    for item, h in zip(items, item_heights):
        d.text((x + 5, y + 15), "✓", font=get_font(config["body_font"], config["base_font_size"], bold=True), fill=_hex(theme["point"]))
        draw_wrapped(d, (x + 38, y + 12), item, font, _hex(muted), inner_w - 42, "left", 8)
        y += h
        d.line((x, y, width - x, y), fill=_hex(theme["line"]), width=1)
    return stitch([head, body], width, bg)


def make_full_image_block(uploaded, width: int, bg: str, max_height: int = 1150) -> Image.Image | None:
    return make_uniform_image_block(uploaded, width, bg, box_height=max_height)


def make_two_image_block(
    left_file,
    right_file,
    width: int,
    bg: str,
    gap: int = 16,
    max_height: int = 900,
) -> Image.Image | None:
    return make_uniform_two_image_block(left_file, right_file, width, bg, box_height=max_height, gap=gap)


def make_gallery(
    files: Sequence,
    width: int,
    bg: str,
    columns: int = 1,
    gap: int = 16,
    max_height: int = 950,
) -> Image.Image | None:
    return make_uniform_gallery(files, width, bg, columns=columns, gap=gap, box_height=max_height)


def make_points_section(width: int, theme: Dict[str, str], config: Dict) -> Image.Image:
    soft = config["theme"] == "모던 블랙"
    bg = theme["soft_bg"]
    text_color = "#f2f2f2" if soft else theme["text"]
    muted = "#c8c8c8" if soft else theme["muted"]
    head = make_heading_block(
        width,
        bg,
        theme["point"],
        text_color,
        muted,
        config["heading_font"],
        config["body_font"],
        "KEY POINT",
        "입을수록 만족스러운 이유",
        align="center",
        padding_bottom=28,
        base_size=config["base_font_size"],
    )
    cards = [
        (config["point1_title"], config["point1_text"]),
        (config["point2_title"], config["point2_text"]),
        (config["point3_title"], config["point3_text"]),
        (config["point4_title"], config["point4_text"]),
    ]
    margin = 34
    gap = 16
    cell_w = (width - margin * 2 - gap) // 2
    cell_h = 220
    body_h = margin + cell_h * 2 + gap + margin
    body = solid_block(width, body_h, bg)
    d = ImageDraw.Draw(body)
    small_font = get_font(config["body_font"], max(13, config["base_font_size"] - 3), bold=True)
    title_font = get_font(config["body_font"], config["base_font_size"] + 2, bold=True)
    text_font = get_font(config["body_font"], max(14, config["base_font_size"] - 1))
    for index, (title, text) in enumerate(cards):
        row, col = divmod(index, 2)
        x = margin + col * (cell_w + gap)
        y = margin + row * (cell_h + gap)
        d.rounded_rectangle((x, y, x + cell_w, y + cell_h), radius=12, fill=_hex(theme["card_bg"]), outline=_hex(theme["line"]), width=1)
        d.text((x + 22, y + 20), f"POINT {index + 1:02d}", font=small_font, fill=_hex(theme["point"]))
        draw_wrapped(d, (x + 22, y + 54), title, title_font, _hex(theme["text"]), cell_w - 44, "left", 7)
        draw_wrapped(d, (x + 22, y + 105), text, text_font, _hex(theme["muted"]), cell_w - 44, "left", 7)
    return stitch([head, body], width, bg)


def make_copy_block(
    width: int,
    theme: Dict[str, str],
    config: Dict,
    title: str,
    text: str,
    bg: str | None = None,
) -> Image.Image:
    bg = bg or theme["section_bg"]
    temp = Image.new("RGB", (width, 10), "white")
    draw = ImageDraw.Draw(temp)
    title_font = get_font(config["body_font"], config["base_font_size"] + 4, bold=True)
    text_font = get_font(config["body_font"], config["base_font_size"])
    inner = width - 100
    title_h = text_height(draw, title, title_font, inner, 8)
    text_h = text_height(draw, text, text_font, inner, 8)
    height = 34 + title_h + 12 + text_h + 42
    block = solid_block(width, height, bg)
    d = ImageDraw.Draw(block)
    y = 34
    draw_wrapped(d, (50, y), title, title_font, _hex(theme["text"]), inner, "left", 8)
    y += title_h + 12
    draw_wrapped(d, (50, y), text, text_font, _hex(theme["muted"]), inner, "left", 8)
    return block


def make_korea_box(width: int, theme: Dict[str, str], config: Dict) -> Image.Image:
    bg = theme["soft_bg"]
    dark_soft = config["theme"] == "모던 블랙"
    text_color = "#f2f2f2" if dark_soft else theme["text"]
    muted = "#c8c8c8" if dark_soft else theme["muted"]
    head = make_heading_block(
        width,
        bg,
        theme["point"],
        text_color,
        muted,
        config["heading_font"],
        config["body_font"],
        "MADE IN KOREA",
        "원단부터 완성까지, 국내에서",
        align="center",
        padding_bottom=28,
        base_size=config["base_font_size"],
    )
    margin = 38
    inner_w = width - margin * 2
    temp = Image.new("RGB", (width, 10), "white")
    draw = ImageDraw.Draw(temp)
    title_font = get_font(config["body_font"], config["base_font_size"] + 5, bold=True)
    text_font = get_font(config["body_font"], config["base_font_size"])
    title_h = text_height(draw, config["korea_title"], title_font, inner_w - 50, 8)
    text_h = text_height(draw, config["korea_text"], text_font, inner_w - 50, 8)
    box_h = 38 + title_h + 14 + text_h + 38
    body = solid_block(width, box_h + 50, bg)
    d = ImageDraw.Draw(body)
    d.rounded_rectangle((margin, 0, width - margin, box_h), radius=12, fill=_hex(theme["card_bg"]), outline=_hex(theme["point"]), width=2)
    y = 38
    draw_wrapped(d, (margin + 25, y), config["korea_title"], title_font, _hex(theme["text"]), inner_w - 50, "center", 8)
    y += title_h + 14
    draw_wrapped(d, (margin + 25, y), config["korea_text"], text_font, _hex(theme["muted"]), inner_w - 50, "center", 8)
    return stitch([head, body], width, bg)


def make_story_section(width: int, theme: Dict[str, str], config: Dict) -> Image.Image:
    bg = theme["section_bg"]
    head = make_heading_block(
        width,
        bg,
        theme["point"],
        theme["text"],
        theme["muted"],
        config["heading_font"],
        config["body_font"],
        "BRAND STORY",
        "왜 이 제품을 선보이게 되었는지 전합니다",
        "만드는 기준과 고객을 대하는 마음을 담았습니다.",
        align=theme.get("heading_align", "center"),
        padding_bottom=28,
        base_size=config["base_font_size"],
    )
    blocks = [head]
    story_items = [
        (config.get("story_intro_title", ""), config.get("story_intro_text", "")),
        (config.get("story_making_title", ""), config.get("story_making_text", "")),
        (config.get("story_customer_title", ""), config.get("story_customer_text", "")),
    ]
    for title, text in story_items:
        if str(title).strip() or str(text).strip():
            blocks.append(make_copy_block(width, theme, config, str(title).strip(), str(text).strip(), bg=bg))
    return stitch(blocks, width, bg)


def make_group_order_section(width: int, theme: Dict[str, str], config: Dict) -> Image.Image:
    """단체 주문과 도소매 상담 안내를 강조하는 독립 구역을 만듭니다."""
    bg = theme["section_bg"]
    outer_margin = 38
    inner_width = width - outer_margin * 2
    temp = Image.new("RGB", (width, 10), "white")
    draw = ImageDraw.Draw(temp)

    label_font = get_font(config["body_font"], max(13, config["base_font_size"] - 3), bold=True)
    title_font = get_font(config["heading_font"], max(28, int(config["base_font_size"] * 1.8)), bold=True)
    text_font = get_font(config["body_font"], config["base_font_size"])
    contact_font = get_font(config["body_font"], max(15, config["base_font_size"] - 1), bold=True)

    label = "GROUP & WHOLESALE"
    title = config.get("group_order_title", "단체 주문 및 도소매 상담 가능합니다")
    text = config.get("group_order_text", "")
    contact = config.get("group_order_contact", "")

    label_h = text_height(draw, label, label_font, inner_width - 70, 4)
    title_h = text_height(draw, title, title_font, inner_width - 70, 10)
    text_h = text_height(draw, text, text_font, inner_width - 70, 8)
    contact_h = text_height(draw, contact, contact_font, inner_width - 70, 6) if contact else 0
    box_h = 46 + label_h + 16 + title_h + 20 + text_h + (20 + contact_h if contact else 0) + 46

    block = solid_block(width, box_h + 70, bg)
    d = ImageDraw.Draw(block)
    d.rounded_rectangle(
        (outer_margin, 35, width - outer_margin, 35 + box_h),
        radius=18,
        fill=_hex(theme["soft_bg"]),
        outline=_hex(theme["point"]),
        width=2,
    )
    x = outer_margin + 35
    y = 35 + 46
    content_width = inner_width - 70
    draw_wrapped(d, (x, y), label, label_font, _hex(theme["point"]), content_width, "center", 4)
    y += label_h + 16
    draw_wrapped(d, (x, y), title, title_font, _hex(theme["text"]), content_width, "center", 10)
    y += title_h + 20
    draw_wrapped(d, (x, y), text, text_font, _hex(theme["muted"]), content_width, "center", 8)
    if contact:
        y += text_h + 20
        draw_wrapped(d, (x, y), contact, contact_font, _hex(theme["point"]), content_width, "center", 6)
    return block


def make_uses_section(width: int, theme: Dict[str, str], config: Dict, uses: Sequence[Sequence[str]]) -> Image.Image:
    head = make_heading_block(
        width,
        theme["section_bg"],
        theme["point"],
        theme["text"],
        theme["muted"],
        config["heading_font"],
        config["body_font"],
        "STYLING",
        "격식 있는 순간부터 편안한 외출까지",
        align=theme.get("heading_align", "center"),
        padding_bottom=28,
        base_size=config["base_font_size"],
    )
    margin, gap = 34, 16
    cell_w = (width - margin * 2 - gap) // 2
    rows = (len(uses) + 1) // 2
    cell_h = 150
    body_h = margin + rows * cell_h + max(0, rows - 1) * gap + margin
    body = solid_block(width, body_h, theme["section_bg"])
    d = ImageDraw.Draw(body)
    title_font = get_font(config["body_font"], config["base_font_size"] + 1, bold=True)
    text_font = get_font(config["body_font"], max(13, config["base_font_size"] - 2))
    for idx, pair in enumerate(uses):
        title = pair[0]
        text = pair[1] if len(pair) > 1 else ""
        row, col = divmod(idx, 2)
        x = margin + col * (cell_w + gap)
        y = margin + row * (cell_h + gap)
        d.rounded_rectangle((x, y, x + cell_w, y + cell_h), radius=12, fill=_hex(theme["card_bg"]), outline=_hex(theme["line"]), width=1)
        title_h = text_height(d, title, title_font, cell_w - 36, 6)
        text_h = text_height(d, text, text_font, cell_w - 36, 6)
        ty = y + (cell_h - title_h - 8 - text_h) // 2
        draw_wrapped(d, (x + 18, ty), title, title_font, _hex(theme["text"]), cell_w - 36, "center", 6)
        ty += title_h + 8
        draw_wrapped(d, (x + 18, ty), text, text_font, _hex(theme["muted"]), cell_w - 36, "center", 6)
    return stitch([head, body], width, theme["section_bg"])


def make_table_section(
    width: int,
    theme: Dict[str, str],
    config: Dict,
    label: str,
    title: str,
    rows: Sequence[Sequence[str]],
    soft: bool = True,
) -> Image.Image:
    bg = theme["soft_bg"] if soft else theme["section_bg"]
    dark_soft = soft and config["theme"] == "모던 블랙"
    text_color = "#f2f2f2" if dark_soft else theme["text"]
    muted = "#c8c8c8" if dark_soft else theme["muted"]
    head = make_heading_block(
        width,
        bg,
        theme["point"],
        text_color,
        muted,
        config["heading_font"],
        config["body_font"],
        label,
        title,
        align="center",
        padding_bottom=28,
        base_size=config["base_font_size"],
    )
    margin = 34
    label_w = int((width - margin * 2) * 0.34)
    value_w = width - margin * 2 - label_w
    font = get_font(config["body_font"], max(14, config["base_font_size"] - 1))
    bold_font = get_font(config["body_font"], max(14, config["base_font_size"] - 1), bold=True)
    temp = Image.new("RGB", (width, 10), "white")
    d0 = ImageDraw.Draw(temp)
    heights = []
    for row in rows:
        left = row[0] if row else ""
        right = row[1] if len(row) > 1 else ""
        h = max(
            text_height(d0, left, bold_font, label_w - 28, 6),
            text_height(d0, right, font, value_w - 28, 6),
        ) + 28
        heights.append(max(54, h))
    table_h = sum(heights)
    body = solid_block(width, table_h + 68, bg)
    d = ImageDraw.Draw(body)
    y = 16
    for row, h in zip(rows, heights):
        left = row[0] if row else ""
        right = row[1] if len(row) > 1 else ""
        d.rectangle((margin, y, margin + label_w, y + h), fill=_hex(theme["card_bg"]), outline=_hex(theme["line"]), width=1)
        d.rectangle((margin + label_w, y, width - margin, y + h), fill=_hex(theme["section_bg"]), outline=_hex(theme["line"]), width=1)
        draw_wrapped(d, (margin + 14, y + 14), left, bold_font, _hex(theme["text"]), label_w - 28, "left", 6)
        draw_wrapped(d, (margin + label_w + 14, y + 14), right, font, _hex(theme["text"]), value_w - 28, "left", 6)
        y += h
    return stitch([head, body], width, bg)


def make_size_section(width: int, theme: Dict[str, str], config: Dict) -> Image.Image:
    head = make_heading_block(
        width,
        theme["section_bg"],
        theme["point"],
        theme["text"],
        theme["muted"],
        config["heading_font"],
        config["body_font"],
        "SIZE GUIDE",
        "실측 사이즈",
        "측정 위치와 방법에 따라 1~3cm 정도 오차가 발생할 수 있습니다.",
        align=theme.get("heading_align", "center"),
        padding_bottom=28,
        base_size=config["base_font_size"],
    )

    headers = ["사이즈"] + [
        str(config.get(f"size_header_{index}", default)).strip() or default
        for index, default in enumerate(["어깨", "가슴단면", "소매길이", "암홀", "총장"], 1)
    ]

    row_count = max(1, min(8, int(config.get("size_row_count", 1))))
    rows = []
    for row_index in range(1, row_count + 1):
        if row_index == 1:
            fallback = [
                config.get("size_name", "FREE"),
                config.get("size_shoulder", ""),
                config.get("size_chest", ""),
                config.get("size_sleeve", ""),
                config.get("size_armhole", ""),
                config.get("size_length", ""),
            ]
        else:
            fallback = ["", "", "", "", "", ""]
        row = [str(config.get(f"size_{row_index}_name", fallback[0]))]
        for col_index in range(1, 6):
            row.append(str(config.get(f"size_{row_index}_{col_index}", fallback[col_index])))
        rows.append(row)

    margin = 24
    column_count = len(headers)
    cell_w = (width - margin * 2) // column_count
    header_h = 58
    row_h = 64
    body_h = header_h + row_h * len(rows) + 64
    body = solid_block(width, body_h, theme["section_bg"])
    d = ImageDraw.Draw(body)
    head_font = get_font(config["body_font"], max(13, config["base_font_size"] - 3), bold=True)
    value_font = get_font(config["body_font"], max(13, config["base_font_size"] - 3))
    y = 14

    for idx, header in enumerate(headers):
        x = margin + idx * cell_w
        right = width - margin if idx == column_count - 1 else x + cell_w
        d.rectangle((x, y, right, y + header_h), fill=_hex(theme["card_bg"]), outline=_hex(theme["line"]), width=1)
        draw_wrapped(d, (x + 6, y + 17), header, head_font, _hex(theme["text"]), right - x - 12, "center", 5)

    for row_number, row in enumerate(rows):
        row_y = y + header_h + row_number * row_h
        for idx, value in enumerate(row):
            x = margin + idx * cell_w
            right = width - margin if idx == column_count - 1 else x + cell_w
            d.rectangle((x, row_y, right, row_y + row_h), fill=_hex(theme["section_bg"]), outline=_hex(theme["line"]), width=1)
            draw_wrapped(d, (x + 6, row_y + 18), value, value_font, _hex(theme["text"]), right - x - 12, "center", 5)

    return stitch([head, body], width, theme["section_bg"])


def make_notice_section(width: int, theme: Dict[str, str], config: Dict, notices: Sequence[str]) -> Image.Image:
    bg = theme["soft_bg"]
    dark_soft = config["theme"] == "모던 블랙"
    text_color = "#f2f2f2" if dark_soft else theme["text"]
    muted = "#c8c8c8" if dark_soft else theme["muted"]
    head = make_heading_block(
        width,
        bg,
        theme["point"],
        text_color,
        muted,
        config["heading_font"],
        config["body_font"],
        "NOTICE",
        "구매 전 확인해 주세요",
        align="center",
        padding_bottom=28,
        base_size=config["base_font_size"],
    )
    margin = 34
    font = get_font(config["body_font"], max(14, config["base_font_size"] - 1))
    temp = Image.new("RGB", (width, 10), "white")
    d0 = ImageDraw.Draw(temp)
    inner = width - margin * 2 - 52
    heights = [text_height(d0, item, font, inner, 7) + 20 for item in notices]
    box_h = sum(heights) + 40
    body = solid_block(width, box_h + 60, bg)
    d = ImageDraw.Draw(body)
    d.rounded_rectangle((margin, 0, width - margin, box_h), radius=12, fill=_hex(theme["card_bg"]), outline=_hex(theme["line"]), width=1)
    y = 20
    for item, h in zip(notices, heights):
        d.ellipse((margin + 20, y + 9, margin + 26, y + 15), fill=_hex(theme["point"]))
        draw_wrapped(d, (margin + 40, y), item, font, _hex(theme["text"]), inner, "left", 7)
        y += h
    return stitch([head, body], width, bg)


def make_footer(width: int, theme: Dict[str, str], config: Dict) -> Image.Image:
    temp = Image.new("RGB", (width, 10), "white")
    d0 = ImageDraw.Draw(temp)
    title_font = get_font(config["heading_font"], max(28, int(config["base_font_size"] * 1.7)), bold=True)
    text_font = get_font(config["body_font"], config["base_font_size"])
    inner = width - 100
    title_h = text_height(d0, config["footer_title"], title_font, inner, 10)
    text_h = text_height(d0, config["footer_text"], text_font, inner, 8)
    height = 70 + title_h + 18 + text_h + 90
    block = solid_block(width, height, theme["section_bg"])
    d = ImageDraw.Draw(block)
    y = 70
    draw_wrapped(d, (50, y), config["footer_title"], title_font, _hex(theme["text"]), inner, "center", 10)
    y += title_h + 18
    draw_wrapped(d, (50, y), config["footer_text"], text_font, _hex(theme["muted"]), inner, "center", 8)
    return block


def stitch(
    blocks: Iterable[Image.Image | None],
    width: int,
    bg: str,
    gap: int = 0,
) -> Image.Image:
    valid = [block for block in blocks if block is not None]
    if not valid:
        return solid_block(width, 1, bg)
    total_h = sum(block.height for block in valid) + gap * max(0, len(valid) - 1)
    canvas = solid_block(width, total_h, bg)
    y = 0
    for block in valid:
        canvas.paste(block, ((width - block.width) // 2, y))
        y += block.height + gap
    return canvas


def build_detail_jpg(
    config: Dict,
    theme: Dict[str, str],
    core_images: Dict[str, object],
    extra_model_images: Sequence,
    extra_detail_images: Sequence,
    extra_gallery_images: Sequence,
    quality: int = 90,
) -> Tuple[bytes, int, int, int]:
    width = int(config["page_width"])
    width = max(720, min(1000, width))
    extras = list(extra_model_images) + list(extra_detail_images) + list(extra_gallery_images)
    if len(extras) > MAX_EXTRA_IMAGES:
        remaining = MAX_EXTRA_IMAGES
        extra_model_images = list(extra_model_images)[:remaining]
        remaining -= len(extra_model_images)
        extra_detail_images = list(extra_detail_images)[: max(0, remaining)]
        remaining -= len(extra_detail_images)
        extra_gallery_images = list(extra_gallery_images)[: max(0, remaining)]

    problems = [line.strip() for line in config["problems"].splitlines() if line.strip()]
    uses = []
    for line in config["uses"].splitlines():
        if not line.strip():
            continue
        if "|" in line:
            left, right = line.split("|", 1)
        else:
            left, right = line, ""
        uses.append([left.strip(), right.strip()])
    specs = []
    for line in config["specs"].splitlines():
        if not line.strip():
            continue
        if "|" in line:
            left, right = line.split("|", 1)
        else:
            left, right = line, ""
        specs.append([left.strip(), right.strip()])
    notices = [line.strip() for line in config["notices"].splitlines() if line.strip()]

    mode = config.get("detail_page_mode", "혼합형 상세페이지")

    hero_blocks: List[Image.Image | None] = []
    hero_blocks.extend(make_hero(width, theme, config, core_images.get("hero")))
    hero_blocks.append(make_badges(width, theme, config))

    problem_block = make_list_section(width, theme, config, "FOR YOU", "이런 옷을 찾고 계셨나요?", problems, True)

    silhouette_blocks: List[Image.Image | None] = []
    silhouette_blocks.append(
        make_heading_block(
            width,
            theme["section_bg"],
            theme["point"],
            theme["text"],
            theme["muted"],
            config["heading_font"],
            config["body_font"],
            "SILHOUETTE",
            "우아하게 정돈되는 실루엣",
            config["look_description"],
            align=theme.get("heading_align", "center"),
            padding_bottom=32,
            base_size=config["base_font_size"],
        )
    )
    silhouette_blocks.append(make_full_image_block(core_images.get("front"), width, theme["section_bg"], 1250))
    silhouette_blocks.append(make_two_image_block(core_images.get("angle"), core_images.get("back"), width, theme["section_bg"], max_height=900))
    silhouette_blocks.append(make_gallery(extra_model_images, width, theme["section_bg"], columns=2, max_height=900))

    detail_blocks: List[Image.Image | None] = []
    detail_blocks.append(make_points_section(width, theme, config))
    detail_blocks.append(
        make_heading_block(
            width,
            theme["section_bg"],
            theme["point"],
            theme["text"],
            theme["muted"],
            config["heading_font"],
            config["body_font"],
            "DETAIL",
            "눈으로 확인하는 섬세한 디테일",
            align=theme.get("heading_align", "center"),
            padding_bottom=32,
            base_size=config["base_font_size"],
        )
    )
    fabric = make_full_image_block(core_images.get("fabric"), width, theme["section_bg"], 1100)
    if fabric is not None:
        detail_blocks.append(fabric)
    detail_blocks.append(make_copy_block(width, theme, config, config["fabric_title"], config["fabric_text"]))
    button = make_full_image_block(core_images.get("button"), width, theme["section_bg"], 1100)
    if button is not None:
        detail_blocks.append(button)
    detail_blocks.append(make_copy_block(width, theme, config, config["button_title"], config["button_text"]))
    detail_blocks.append(make_two_image_block(core_images.get("collar"), core_images.get("sleeve"), width, theme["section_bg"], max_height=900))
    detail_blocks.append(make_gallery(extra_detail_images, width, theme["section_bg"], columns=1, max_height=950))

    korea_block = make_full_image_block(core_images.get("korea"), width, theme["soft_bg"], 1100)
    story_block = make_story_section(width, theme, config) if config.get("story_enabled", True) else None
    group_order_block = make_group_order_section(width, theme, config) if config.get("group_order_enabled", True) else None
    uses_block = make_uses_section(width, theme, config, uses)
    styling_block = make_full_image_block(core_images.get("styling"), width, theme["section_bg"], 1200)
    gallery_block = make_gallery(extra_gallery_images, width, theme["section_bg"], columns=1, max_height=950)
    info_block = make_table_section(width, theme, config, "PRODUCT INFO", "상품 정보", specs, True)
    size_block = make_size_section(width, theme, config)
    size_image_block = make_full_image_block(core_images.get("size"), width, theme["section_bg"], 1100)
    notice_block = make_notice_section(width, theme, config, notices)
    footer_block = make_footer(width, theme, config)

    blocks: List[Image.Image | None] = []
    blocks.extend(hero_blocks)

    if mode == "스토리형 상세페이지":
        blocks.append(korea_block)
        blocks.append(story_block)
        blocks.append(problem_block)
        blocks.extend(silhouette_blocks)
        blocks.extend(detail_blocks)
        blocks.append(uses_block)
        blocks.append(styling_block)
        blocks.append(gallery_block)
        blocks.append(group_order_block)
    elif mode == "판매집중형 상세페이지":
        blocks.append(problem_block)
        blocks.extend(silhouette_blocks)
        blocks.extend(detail_blocks)
        blocks.append(korea_block)
        blocks.append(uses_block)
        blocks.append(group_order_block)
        if config.get("story_enabled", False):
            blocks.append(story_block)
        blocks.append(styling_block)
        blocks.append(gallery_block)
    else:
        blocks.append(korea_block)
        blocks.append(story_block)
        blocks.append(problem_block)
        blocks.extend(silhouette_blocks)
        blocks.extend(detail_blocks)
        blocks.append(uses_block)
        blocks.append(group_order_block)
        blocks.append(styling_block)
        blocks.append(gallery_block)

    blocks.append(info_block)
    blocks.append(size_block)
    blocks.append(size_image_block)
    blocks.append(notice_block)
    blocks.append(footer_block)

    final = stitch(blocks, width, theme["page_bg"])
    if final.height > MAX_JPEG_HEIGHT:
        ratio = MAX_JPEG_HEIGHT / final.height
        new_width = max(1, int(final.width * ratio))
        final = final.resize((new_width, MAX_JPEG_HEIGHT), Image.Resampling.LANCZOS)

    buffer = BytesIO()
    final.save(buffer, format="JPEG", quality=int(quality), optimize=True, progressive=True, subsampling=1)
    data = buffer.getvalue()
    return data, final.width, final.height, min(len(extras), MAX_EXTRA_IMAGES)
