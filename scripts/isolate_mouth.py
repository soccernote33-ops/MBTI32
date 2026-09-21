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

MOUTH_BOX = (0.32, 0.54, 0.74, 0.90)   # 左, 上, 右, 下 (画像比)
FEATHER = 0.05                          # ふちのぼかし幅 (画像比)


def mouth_mask(size: tuple[int, int]) -> Image.Image:
    w, h = size
    box = (w * MOUTH_BOX[0], h * MOUTH_BOX[1], w * MOUTH_BOX[2], h * MOUTH_BOX[3])
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).ellipse(box, fill=255)
    return mask.filter(ImageFilter.GaussianBlur(w * FEATHER))


def main() -> int:
    for char_dir in sorted(p for p in Path("data/assets").iterdir() if p.is_dir()):
        pairs_file = char_dir / "mouth_pairs.json"
        if not pairs_file.exists():
            continue
        pairs = json.loads(pairs_file.read_text())
        out_dir = char_dir / "mouth_frames"
        out_dir.mkdir(exist_ok=True)

        for number, pair in sorted(pairs.items()):
            open_img = Image.open(pair["open"]).convert("RGB")
            closed_img = Image.open(pair["closed"]).convert("RGB").resize(open_img.size)

            merged = open_img.copy()
            merged.paste(closed_img, (0, 0), mouth_mask(open_img.size))

            open_img.save(out_dir / f"{number}_open.png")
            merged.save(out_dir / f"{number}_closed.png")
            pairs[number] = {"open": str(out_dir / f"{number}_open.png"),
                             "closed": str(out_dir / f"{number}_closed.png")}

        pairs_file.write_text(json.dumps(pairs, ensure_ascii=False, indent=2))
        print(f"{char_dir.name}: {len(pairs)}組")
    return 0


if __name__ == "__main__":
    sys.exit(main())
