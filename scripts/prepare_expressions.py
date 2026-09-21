#!/usr/bin/env python3
"""切り出した表情画像に名前プレートを重ね、動画用の素材を作る。

ラベルの除去は crop_expressions.py が済ませている前提。ここでは誰の発言か
分かるように、キャラ名のプレートを乗せるだけ。出力は expressions_clean/。
"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT = "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"

CHARACTERS = {
    # ENFJのシートはラベルが絵に直接重なっているため、必ず左上を覆う必要がある
    "enfj_hanamori_yuina": {"name": "花森 結菜", "subtitle": "ENFJ 主人公",
                            "accent": (74, 110, 60), "corner": "tl"},
    "isfj_mizuki_nagisa": {"name": "水城 凪沙", "subtitle": "ISFJ 擁護者",
                           "accent": (58, 92, 150)},
    "intp_fujimiya_riku": {"name": "藤宮 理玖", "subtitle": "INTP 論理学者",
                           "accent": (98, 80, 155)},
    "estp_kinjo_shun": {"name": "金城 瞬", "subtitle": "ESTP 起業家",
                        "accent": (150, 105, 10)},
}

PLATE_W, PLATE_H, MARGIN = 192, 124, 4
CORNERS = ("tl", "tr", "bl", "br")


def plate_box(size: tuple[int, int], corner: str) -> tuple[int, int, int, int]:
    w, h = size
    x0 = MARGIN if corner in ("tl", "bl") else w - PLATE_W - MARGIN
    y0 = MARGIN if corner in ("tl", "tr") else h - PLATE_H - MARGIN
    return x0, y0, x0 + PLATE_W, y0 + PLATE_H


def face_coverage(panel: Image.Image, corner: str) -> float:
    """プレートを置いたとき、肌色の画素をどれだけ隠すか"""
    x0, y0, x1, y1 = plate_box(panel.size, corner)
    px = panel.convert("RGB").crop((x0, y0, x1, y1)).getdata()
    skin = sum(1 for r, g, b in px
               if r > 175 and 110 < g < 215 and 100 < b < 200 and r > g > b)
    return skin / max(1, len(px))


def pick_corner(panels: list[Image.Image]) -> str:
    """12枚を通して、最も顔を隠さない角を選ぶ"""
    return min(CORNERS, key=lambda c: max(face_coverage(p, c) for p in panels))


def add_nameplate(panel: Image.Image, cfg: dict, corner: str) -> Image.Image:
    im = panel.convert("RGBA")
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    x0, y0, x1, y1 = plate_box(im.size, corner)

    draw.rounded_rectangle([x0, y0, min(x1, im.width - MARGIN), y1],
                           radius=16, fill=cfg["accent"] + (240,))
    draw.text((x0 + 16, y0 + 22), cfg["name"],
              font=ImageFont.truetype(FONT, 28), fill=(255, 255, 255, 255))
    draw.text((x0 + 16, y0 + 62), cfg["subtitle"],
              font=ImageFont.truetype(FONT, 18), fill=(255, 255, 255, 215))
    return Image.alpha_composite(im, layer).convert("RGB")


def main() -> int:
    for char, cfg in CHARACTERS.items():
        src = Path("data/assets") / char / "expressions"
        dst = Path("data/assets") / char / "expressions_clean"
        if not src.is_dir():
            print(f"skip {char}: 表情画像がありません")
            continue
        dst.mkdir(exist_ok=True)
        for old in dst.glob("*.png"):
            old.unlink()

        paths = sorted(src.glob("*.png"))
        panels = [Image.open(p).convert("RGB") for p in paths]
        corner = cfg.get("corner") or pick_corner(panels)
        for path, panel in zip(paths, panels):
            add_nameplate(panel, cfg, corner).save(dst / path.name)
        print(f"{char}: {len(paths)}枚 (プレート位置 {corner})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
