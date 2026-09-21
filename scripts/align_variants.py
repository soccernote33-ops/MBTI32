#!/usr/bin/env python3
"""口の開閉ペアの位置を揃える。

表情集を2枚に分けて作ると、シートごとに余白の取り方が変わり、同じ表情でも
キャラの大きさや位置が少しずれる。そのまま切り替えると絵が跳ねて見えるので、
口以外の部分(額から目のあたり)が重なるよう、2枚目を拡大縮小して動かす。
"""

import sys
from pathlib import Path

import numpy as np
from PIL import Image

PROBE = 160          # 位置合わせの計算に使う縮小サイズ
TOP_REGION = 0.45    # 口が入らない上側だけで比べる


def to_probe(img: Image.Image) -> np.ndarray:
    return np.array(img.convert("L").resize((PROBE, PROBE), Image.LANCZOS)).astype(float)


def transform(img: Image.Image, scale: float, dx: int, dy: int,
              size: tuple[int, int]) -> Image.Image:
    w, h = size
    scaled = img.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)
    canvas = Image.new("RGB", size, (255, 255, 255))
    canvas.paste(scaled, ((w - scaled.width) // 2 + dx, (h - scaled.height) // 2 + dy))
    return canvas


def mismatch(a_probe: np.ndarray, b_img: Image.Image, scale: float,
             dx: int, dy: int) -> float:
    moved = transform(b_img, scale, dx, dy, (PROBE, PROBE))
    diff = np.abs(a_probe - np.array(moved.convert("L")).astype(float))
    return float(diff[:int(PROBE * TOP_REGION)].mean())


def best_fit(a: Image.Image, b: Image.Image) -> tuple[float, int, int, float]:
    a_probe = to_probe(a)
    b_probe = b.convert("L").resize((PROBE, PROBE), Image.LANCZOS).convert("RGB")

    best = (1.0, 0, 0, mismatch(a_probe, b_probe, 1.0, 0, 0))
    for scale in np.arange(0.88, 1.13, 0.02):
        for dx in range(-14, 15, 2):
            for dy in range(-14, 15, 2):
                score = mismatch(a_probe, b_probe, float(scale), dx, dy)
                if score < best[3]:
                    best = (float(scale), dx, dy, score)
    return best


def main() -> int:
    for char_dir in sorted(p for p in Path("data/assets").iterdir() if p.is_dir()):
        a_dir, b_dir = char_dir / "expressions", char_dir / "expressions_b"
        if not (a_dir.is_dir() and b_dir.is_dir()):
            continue

        moved = 0
        for a_path in sorted(a_dir.glob("*.png")):
            b_path = b_dir / a_path.name
            if not b_path.exists():
                continue
            a_img = Image.open(a_path).convert("RGB")
            b_img = Image.open(b_path).convert("RGB")

            scale, dx, dy, _ = best_fit(a_img, b_img)
            # 縮小版で測った移動量を実寸に直す
            ratio = a_img.width / PROBE
            fitted = transform(b_img.resize(a_img.size, Image.LANCZOS), scale,
                               int(round(dx * ratio)), int(round(dy * ratio)), a_img.size)
            fitted.save(b_path)
            if abs(scale - 1.0) > 0.01 or dx or dy:
                moved += 1

        print(f"{char_dir.name}: {moved}枚を調整")
    return 0


if __name__ == "__main__":
    sys.exit(main())
