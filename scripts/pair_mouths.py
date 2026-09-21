#!/usr/bin/env python3
"""口の開閉ペアを作る。

同じキャラの表情集を2枚用意すると、構図はほぼ同じで口の形だけが違う絵が
12組できる。どちらが開いた口かを口内の面積で推定し、結果を
data/assets/<キャラ>/mouth_pairs.json に書き出す。

推定は完全ではないので、出力されたJSONは目視で直せるようにしてある。
"""

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

# 自動判定が外れた組の手直し。値は開いている方のフォルダ
OVERRIDES = {
    "estp_kinjo_shun": {"04": "expressions"},
}


def mouth_area(path: Path) -> float:
    """顔の下半分から、口内に見える色の割合を出す"""
    a = np.array(Image.open(path).convert("RGB")).astype(int)
    h, w = a.shape[:2]
    roi = a[int(h * 0.45):int(h * 0.88), int(w * 0.25):int(w * 0.75)]
    r, g, b = roi[:, :, 0], roi[:, :, 1], roi[:, :, 2]
    mouth = (r > 85) & (r < 215) & (g < r * 0.62) & (b < r * 0.78)
    return float(mouth.sum()) / mouth.size


def main() -> int:
    root = Path("data/assets")
    for char_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        a_dir, b_dir = char_dir / "expressions", char_dir / "expressions_b"
        if not (a_dir.is_dir() and b_dir.is_dir()):
            continue

        pairs = {}
        for a_path in sorted(a_dir.glob("*.png")):
            b_path = b_dir / a_path.name
            if not b_path.exists():
                continue
            number = a_path.name[:2]
            forced = OVERRIDES.get(char_dir.name, {}).get(number)
            if forced:
                open_dir = forced
            else:
                open_dir = ("expressions" if mouth_area(a_path) >= mouth_area(b_path)
                            else "expressions_b")
            closed_dir = "expressions_b" if open_dir == "expressions" else "expressions"
            pairs[number] = {
                "open": str(char_dir / open_dir / a_path.name),
                "closed": str(char_dir / closed_dir / a_path.name),
            }

        out = char_dir / "mouth_pairs.json"
        out.write_text(json.dumps(pairs, ensure_ascii=False, indent=2))
        print(f"{char_dir.name}: {len(pairs)}組 -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
