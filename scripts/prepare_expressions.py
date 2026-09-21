#!/usr/bin/env python3
"""ラベルが絵に重なっているシートを、名前プレートで覆って使えるようにする。

ラベルが絵の下にあるシートは crop_expressions.py の切り出しだけで文字が消える
ため、ここでは扱わない。話者名は動画の字幕側で出す。出力は expressions_clean/。
"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT = "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"

CHARACTERS = {
    # ENFJのシートはラベルが絵に直接重なっているため、必ず左上を覆う必要がある
    "enfj_hanamori_yuina": {"name": "花森 結菜", "subtitle": "ENFJ 主人公",
                            "accent": (74, 110, 60), "corner": "tl", "plate_w": 218},
}

PLATE_W, PLATE_H, MARGIN = 192, 124, 4
CORNERS = ("tl", "tr", "bl", "br")


def plate_box(size: tuple[int, int], corner: str,
              plate_w: int = PLATE_W) -> tuple[int, int, int, int]:
    w, h = size
    x0 = MARGIN if corner in ("tl", "bl") else w - plate_w - MARGIN
    y0 = MARGIN if corner in ("tl", "tr") else h - PLATE_H - MARGIN
    return x0, y0, x0 + plate_w, y0 + PLATE_H


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
    x0, y0, x1, y1 = plate_box(im.size, corner, cfg.get("plate_w", PLATE_W))

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
