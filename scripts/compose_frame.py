#!/usr/bin/env python3
"""1セリフ分の縦型フレームを組む。

上にテーマ、中央に話者の立ち絵、下に話者名つきの字幕を置く。
字幕は話者ごとに色を変えて、誰の発言か一目で分かるようにする。
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT = "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"
W, H = 1080, 1920

TITLE_TOP, TITLE_H = 70, 132
PORTRAIT_W = 1000
SUBTITLE_BOTTOM, SUBTITLE_MIN_H = 150, 230
SUBTITLE_SIDE = 60
BODY_SIZE, NAME_SIZE, TITLE_SIZE = 52, 34, 58
CHARS_PER_LINE = 17


def wrap_japanese(text: str, limit: int) -> list[str]:
    """句読点で優先的に折り、無ければ文字数で折る"""
    lines, current = [], ""
    for ch in text:
        current += ch
        if len(current) >= limit or (ch in "、。！？" and len(current) >= limit - 4):
            lines.append(current)
            current = ""
    if current:
        lines.append(current)
    return lines or [""]


def compose(portrait_path: Path, title: str, speaker: str, text: str,
            accent: tuple[int, int, int]) -> Image.Image:
    portrait = Image.open(portrait_path).convert("RGB")

    # 背景: 立ち絵を画面いっぱいに広げてぼかす
    scale = max(W / portrait.width, H / portrait.height)
    bg = portrait.resize((int(portrait.width * scale), int(portrait.height * scale)),
                         Image.LANCZOS)
    bg = bg.crop(((bg.width - W) // 2, (bg.height - H) // 2,
                  (bg.width - W) // 2 + W, (bg.height - H) // 2 + H))
    bg = bg.filter(ImageFilter.GaussianBlur(45))
    bg = Image.blend(bg, Image.new("RGB", (W, H), (20, 22, 30)), 0.35)

    # 立ち絵: 幅を揃え、角を丸めて中央に置く
    fg = portrait.resize((PORTRAIT_W, int(portrait.height * PORTRAIT_W / portrait.width)),
                         Image.LANCZOS)
    corner = Image.new("L", fg.size, 0)
    ImageDraw.Draw(corner).rounded_rectangle([0, 0, fg.width - 1, fg.height - 1],
                                             radius=40, fill=255)
    fg_y = TITLE_TOP + TITLE_H + 120
    frame = bg.copy()
    frame.paste(fg, ((W - PORTRAIT_W) // 2, fg_y), corner)

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    # テーマ帯
    f_title = ImageFont.truetype(FONT, TITLE_SIZE)
    draw.rounded_rectangle([SUBTITLE_SIDE, TITLE_TOP, W - SUBTITLE_SIDE, TITLE_TOP + TITLE_H],
                           radius=28, fill=(24, 26, 34, 225))
    tw = draw.textlength(title, font=f_title)
    draw.text(((W - tw) / 2, TITLE_TOP + 34), title, font=f_title, fill=(255, 255, 255, 255))

    # 字幕
    f_body = ImageFont.truetype(FONT, BODY_SIZE)
    f_name = ImageFont.truetype(FONT, NAME_SIZE)
    lines = wrap_japanese(text, CHARS_PER_LINE)
    box_h = max(SUBTITLE_MIN_H, 118 + len(lines) * (BODY_SIZE + 16))
    y1 = H - SUBTITLE_BOTTOM
    y0 = y1 - box_h
    draw.rounded_rectangle([SUBTITLE_SIDE, y0, W - SUBTITLE_SIDE, y1],
                           radius=30, fill=(18, 20, 28, 232))
    draw.rounded_rectangle([SUBTITLE_SIDE, y0, SUBTITLE_SIDE + 14, y1],
                           radius=7, fill=accent + (255,))

    draw.text((SUBTITLE_SIDE + 44, y0 + 26), speaker, font=f_name,
              fill=tuple(min(255, c + 90) for c in accent) + (255,))
    for i, line in enumerate(lines):
        draw.text((SUBTITLE_SIDE + 44, y0 + 84 + i * (BODY_SIZE + 16)),
                  line, font=f_body, fill=(255, 255, 255, 255))

    return Image.alpha_composite(frame.convert("RGBA"), layer).convert("RGB")
