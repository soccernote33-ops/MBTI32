#!/usr/bin/env python3
"""口以外が動かないコマを作る。

表情集を2枚に分けて作ると、AIが別々に描くため髪や輪郭まで微妙に変わる。
そのまま交互に出すと画面全体がチラついて、口パクに見えない。

そこで開いた口の絵を土台に固定し、口のあたりだけを閉じた口の絵から
貼り替えたコマを作る。変化するのは口だけになる。

貼り替える範囲は画像比で決め打ちしている。顔の大きさと位置は12枚を通して
ほぼ一定なので、これで全キャラ・全表情の口が収まることを目視で確認済み。

    crop_expressions.py -> align_variants.py -> pair_mouths.py -> このスクリプト
"""

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

# キャラごとの口の位置 (左, 上, 右, 下 / 画像比)。
# 顔の大きさも向きもキャラで違うため共通の値は使えない。差分や口内の色から
# 自動で探す方法も試したが、髪の描き分けや目の影に引っ張られて当てにならず、
# 12枚すべてに口が収まることを目で見て決めている。
# シートを作り直したら check_mouth_box.py で再確認すること。
# 顎の輪郭まで入れると、2枚で形が違うぶん貼り替えのたびに線が動く。
# 口とそのすぐ周りに絞ってある。
MOUTH_BOXES = {
    "enfj_hanamori_yuina": (0.34, 0.47, 0.64, 0.72),
    "isfj_mizuki_nagisa": (0.44, 0.54, 0.74, 0.76),
    "intp_fujimiya_riku": (0.33, 0.65, 0.63, 0.88),
    "estp_kinjo_shun": (0.36, 0.60, 0.68, 0.84),
}
FEATHER = 0.04                          # ふちのぼかし幅 (画像比)
SEARCH = 8                              # 位置合わせで探すずれ幅 (画素)


def mouth_mask(size: tuple[int, int], box: tuple[float, float, float, float]) -> Image.Image:
    w, h = size
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).ellipse((w * box[0], h * box[1], w * box[2], h * box[3]), fill=255)
    return mask.filter(ImageFilter.GaussianBlur(w * FEATHER))


def ring_mask(size: tuple[int, int], box: tuple[float, float, float, float]) -> np.ndarray:
    """口のすぐ外側。ここが合っていれば、貼っても顎や頬がずれない"""
    w, h = size
    yy, xx = np.mgrid[0:h, 0:w]
    cx, cy = (box[0] + box[2]) / 2 * w, (box[1] + box[3]) / 2 * h
    rx, ry = (box[2] - box[0]) / 2 * w, (box[3] - box[1]) / 2 * h
    r = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2
    return (r > 1.0) & (r < 1.8)


def fit_locally(open_img: Image.Image, closed_img: Image.Image,
                box: tuple[float, float, float, float]) -> Image.Image:
    """口の周りが最も重なる位置まで、閉じた絵をずらす

    2枚は別々に描かれているので、顔全体を合わせても口元は数画素ずれる。
    ずれたまま貼ると口が動くたびに顎の線が飛んで、歪んで見える。
    """
    a = np.array(open_img).astype(float)
    b = np.array(closed_img).astype(float)
    ring = ring_mask(open_img.size, box)

    best = (np.abs(a - b).mean(axis=2)[ring].mean(), 0, 0)
    for dy in range(-SEARCH, SEARCH + 1):
        for dx in range(-SEARCH, SEARCH + 1):
            shifted = np.roll(np.roll(b, dy, axis=0), dx, axis=1)
            score = np.abs(a - shifted).mean(axis=2)[ring].mean()
            if score < best[0]:
                best = (score, dx, dy)

    _, dx, dy = best
    if dx or dy:
        closed_img = closed_img.transform(closed_img.size, Image.AFFINE,
                                          (1, 0, -dx, 0, 1, -dy), resample=Image.BICUBIC)
    return closed_img


def main() -> int:
    for char_dir in sorted(p for p in Path("data/assets").iterdir() if p.is_dir()):
        pairs_file = char_dir / "mouth_pairs.json"
        if not pairs_file.exists():
            continue
        box = MOUTH_BOXES.get(char_dir.name)
        if box is None:
            print(f"skip {char_dir.name}: 口の位置が未設定")
            continue
        pairs = json.loads(pairs_file.read_text())
        out_dir = char_dir / "mouth_frames"
        out_dir.mkdir(exist_ok=True)

        for number, pair in sorted(pairs.items()):
            open_img = Image.open(pair["open"]).convert("RGB")
            closed_img = Image.open(pair["closed"]).convert("RGB").resize(open_img.size)

            closed_img = fit_locally(open_img, closed_img, box)
            merged = open_img.copy()
            merged.paste(closed_img, (0, 0), mouth_mask(open_img.size, box))

            open_img.save(out_dir / f"{number}_open.png")
            merged.save(out_dir / f"{number}_closed.png")
            pairs[number] = {"open": str(out_dir / f"{number}_open.png"),
                             "closed": str(out_dir / f"{number}_closed.png")}

        pairs_file.write_text(json.dumps(pairs, ensure_ascii=False, indent=2))
        print(f"{char_dir.name}: {len(pairs)}組")
    return 0


if __name__ == "__main__":
    sys.exit(main())
