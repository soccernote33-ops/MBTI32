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

from PIL import Image, ImageDraw, ImageFilter

# キャラごとの口の位置 (左, 上, 右, 下 / 画像比)。
# 顔の大きさも向きもキャラで違うため共通の値は使えない。差分や口内の色から
# 自動で探す方法も試したが、髪の描き分けや目の影に引っ張られて当てにならず、
# 12枚すべてに口が収まることを目で見て決めている。
# シートを作り直したら check_mouth_box.py で再確認すること。
MOUTH_BOXES = {
    "enfj_hanamori_yuina": (0.30, 0.46, 0.68, 0.78),
    "isfj_mizuki_nagisa": (0.40, 0.50, 0.80, 0.82),
    "intp_fujimiya_riku": (0.30, 0.62, 0.70, 0.94),
    "estp_kinjo_shun": (0.32, 0.56, 0.72, 0.90),
}
FEATHER = 0.04                          # ふちのぼかし幅 (画像比)


def mouth_mask(size: tuple[int, int], box: tuple[float, float, float, float]) -> Image.Image:
    w, h = size
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).ellipse((w * box[0], h * box[1], w * box[2], h * box[3]), fill=255)
    return mask.filter(ImageFilter.GaussianBlur(w * FEATHER))


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
