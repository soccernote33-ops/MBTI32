#!/usr/bin/env python3
"""表情集シートを12枚のパネルに切り出す。

段ごとの高さがシートによって微妙に違うため、パネルの上下境界は
「明るく均一な余白の帯」を検出して決める。列は等間隔なので計算で出す。
ラベル帯を持つシートは、切り出したあと下端を落として文字を除去する。
"""

import sys
from pathlib import Path

import numpy as np
from PIL import Image

SHEETS = {
    "enfj_hanamori_yuina": {
        "left": 29, "right": 12, "col_gap": 10, "bottom_trim": 0,
        "labels": ["nikkori", "tanoshisou", "yasashii_hohoemi", "ikari",
                   "kuyashii", "kanashii", "naku", "odoroki",
                   "tere", "kangaeru", "ketsui", "panic"],
    },
    "isfj_mizuki_nagisa": {
        # ラベルは空欄だが帯そのものが残るので、下端を落として消す
        "left": 205, "right": 8, "col_gap": 10, "bottom_trim": 26,
        "labels": ["egao", "warau", "yasashii_emi", "ikari",
                   "frustration", "kanashii", "naku", "odoroki",
                   "tere", "kangaeru", "ketsui", "panic"],
    },
    "estp_kinjo_shun": {
        "left": 14, "right": 14, "col_gap": 12, "bottom_trim": 62,
        "labels": ["egao", "warai", "yasashii_egao", "ikari",
                   "frustration", "kanashii", "naku", "odoroki",
                   "tere", "kangaeru", "ketsui", "panic"],
    },
    "intp_fujimiya_riku": {
        "left": 14, "right": 14, "col_gap": 12, "bottom_trim": 48,
        "labels": ["egao", "oowarai", "yasashii_egao", "ikari",
                   "frustration", "kanashimi", "naku", "odoroki",
                   "tere", "kangaechu", "ketsui", "panic"],
    },
}


def gutter_runs(gray: np.ndarray, min_len: int = 4) -> list[tuple[int, int]]:
    """明るく均一な行(パネル間の余白)の連続区間を返す"""
    flags = [gray[y].mean() > 238 and gray[y].std() < 12 for y in range(gray.shape[0])]
    runs, start = [], None
    for y, is_gutter in enumerate(flags + [False]):
        if is_gutter and start is None:
            start = y
        elif not is_gutter and start is not None:
            if y - start >= min_len:
                runs.append((start, y - 1))
            start = None
    return runs


def row_bounds(gray: np.ndarray) -> list[tuple[int, int]]:
    """余白の帯にはさまれた区間のうち、背の高い3つを段として返す

    ヘッダの有無やラベル帯の作りがシートごとに違うので、区間の位置ではなく
    高さで選ぶ。シート上端・下端も区切りとして扱う。
    """
    edges = [0] + [(a + b) // 2 for a, b in gutter_runs(gray)] + [gray.shape[0] - 1]
    bands = [(edges[i], edges[i + 1]) for i in range(len(edges) - 1)]
    tallest = sorted(bands, key=lambda b: b[1] - b[0], reverse=True)[:3]
    if len(tallest) < 3:
        raise ValueError(f"段の検出に失敗しました (検出数={len(tallest)})")
    return sorted(tallest)


def detect_columns(gray: np.ndarray) -> list[tuple[int, int]] | None:
    """余白から4列の左右位置を読む。等幅に割れなければ諦める"""
    edges = [(a + b) // 2 for a, b in gutter_runs(gray.T)]
    bands = sorted(((edges[i], edges[i + 1]) for i in range(len(edges) - 1)),
                   key=lambda b: b[1] - b[0], reverse=True)[:4]
    if len(bands) < 4:
        return None
    widths = [b - a for a, b in bands]
    if max(widths) / min(widths) > 1.15:
        return None
    return sorted(bands)


def cut_sheet(src: Path, dst: Path, cfg: dict) -> list[tuple[int, int]]:
    sheet = Image.open(src).convert("RGB")
    gray = np.array(sheet.convert("L")).astype(float)
    bands = row_bounds(gray)

    columns = detect_columns(gray)
    if columns is None:
        col_w = (sheet.width - cfg["left"] - cfg["right"] - 3 * cfg["col_gap"]) / 4
        columns = [(int(cfg["left"] + c * (col_w + cfg["col_gap"])),
                    int(cfg["left"] + c * (col_w + cfg["col_gap"]) + col_w)) for c in range(4)]

    dst.mkdir(parents=True, exist_ok=True)
    for old in dst.glob("*.png"):
        old.unlink()

    for i, label in enumerate(cfg["labels"]):
        r, c = divmod(i, 4)
        top, bottom = bands[r]
        x0, x1 = columns[c]
        sheet.crop((x0 + 2, top + 3, x1 - 2,
                    bottom - 3 - cfg["bottom_trim"])).save(dst / f"{i + 1:02d}_{label}.png")
    return bands


def main() -> int:
    for char, cfg in SHEETS.items():
        base = Path("data/assets") / char
        # 2枚目のシートは口の開閉ペアに使う
        for suffix, folder in (("", "expressions"), ("_b", "expressions_b")):
            src = base / "source" / f"expression_sheet{suffix}.webp"
            if not src.exists():
                if not suffix:
                    print(f"skip {char}: シートがありません")
                continue
            geometry = {**cfg, **cfg.get("sheet_b", {})} if suffix else cfg
            bands = cut_sheet(src, base / folder, geometry)
            print(f"{char}/{folder}: 12枚 (段の位置 {bands})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
