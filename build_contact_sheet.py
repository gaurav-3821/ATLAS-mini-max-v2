from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "atlas-review-board.png"
IMAGES = [
    ("Home", ROOT / "review-home.png"),
    ("Dashboard", ROOT / "review-dashboard.png"),
    ("Climate Signals", ROOT / "review-signals.png"),
    ("Global Map", ROOT / "review-global-map.png"),
    ("Risk Intelligence", ROOT / "review-risk.png"),
    ("Predictions", ROOT / "review-predictions.png"),
    ("Data Explorer", ROOT / "review-explorer.png"),
    ("Settings", ROOT / "review-settings.png"),
]

BG = "#0B0F1A"
CARD = "#151A2E"
BORDER = "#000000"
TEXT = "#FFFFFF"
MUTED = "#9CA3AF"
ACCENT = "#00E5FF"

PADDING = 36
GAP = 28
HEADER_H = 140
LABEL_H = 52
CARD_BORDER = 3
SHADOW = 8
COLS = 2
CELL_W = 920
THUMB_H = 520


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = []
    if bold:
        candidates.extend(
            [
                "C:/Windows/Fonts/seguisb.ttf",
                "C:/Windows/Fonts/arialbd.ttf",
            ]
        )
    else:
        candidates.extend(
            [
                "C:/Windows/Fonts/segoeui.ttf",
                "C:/Windows/Fonts/arial.ttf",
            ]
        )
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def fit_image(image: Image.Image, width: int, height: int) -> Image.Image:
    source_ratio = image.width / image.height
    target_ratio = width / height
    if source_ratio > target_ratio:
        new_height = height
        new_width = int(height * source_ratio)
    else:
        new_width = width
        new_height = int(width / source_ratio)
    resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    left = max((new_width - width) // 2, 0)
    top = max((new_height - height) // 2, 0)
    return resized.crop((left, top, left + width, top + height))


def main() -> None:
    rows = (len(IMAGES) + COLS - 1) // COLS
    canvas_w = PADDING * 2 + COLS * CELL_W + (COLS - 1) * GAP
    card_h = LABEL_H + THUMB_H + 28
    canvas_h = PADDING * 2 + HEADER_H + rows * card_h + (rows - 1) * GAP

    canvas = Image.new("RGB", (canvas_w, canvas_h), BG)
    draw = ImageDraw.Draw(canvas)

    title_font = load_font(46, bold=True)
    subtitle_font = load_font(24, bold=False)
    label_font = load_font(24, bold=True)

    draw.text((PADDING, PADDING), "ATLAS Review Board", font=title_font, fill=TEXT)
    draw.text(
        (PADDING, PADDING + 62),
        "Current build screenshots for final UI review before deployment",
        font=subtitle_font,
        fill=MUTED,
    )
    draw.rounded_rectangle(
        (canvas_w - 250, PADDING + 10, canvas_w - PADDING, PADDING + 58),
        radius=16,
        fill=CARD,
        outline=BORDER,
        width=CARD_BORDER,
    )
    draw.text((canvas_w - 226, PADDING + 21), "Climate Intelligence", font=subtitle_font, fill=ACCENT)

    y = PADDING + HEADER_H
    for index, (label, path) in enumerate(IMAGES):
        row = index // COLS
        col = index % COLS
        x = PADDING + col * (CELL_W + GAP)
        y = PADDING + HEADER_H + row * (card_h + GAP)

        draw.rounded_rectangle(
            (x + SHADOW, y + SHADOW, x + CELL_W + SHADOW, y + card_h + SHADOW),
            radius=18,
            fill=BORDER,
        )
        draw.rounded_rectangle(
            (x, y, x + CELL_W, y + card_h),
            radius=18,
            fill=CARD,
            outline=BORDER,
            width=CARD_BORDER,
        )
        draw.text((x + 22, y + 14), label, font=label_font, fill=TEXT)

        image = Image.open(path).convert("RGB")
        thumb = fit_image(image, CELL_W - 28, THUMB_H)
        canvas.paste(thumb, (x + 14, y + LABEL_H))

    canvas.save(OUTPUT, quality=95)
    print(OUTPUT)


if __name__ == "__main__":
    main()
