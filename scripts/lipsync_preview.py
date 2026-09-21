#!/usr/bin/env python3
"""1キャラ分の口パクだけを、顔を大きく映して確認する。

本編サイズだと口が小さく、良し悪しが判断しづらい。テロップも動きも省いて
口の開閉だけを見るためのプレビュー。しきい値を変えて見比べられる。

    python3 scripts/lipsync_preview.py \
        --char data/assets/enfj_hanamori_yuina \
        --voice data/episodes/ep01/voices/01_yuina.wav \
        --expression 1
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from compose_frame import speech_envelope

FPS = 24
SIZE = 720


def run(cmd: list[str]) -> None:
    subprocess.run(cmd + ["-v", "error"], check=True)


def probe_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def mouth_states(envelope, count: int, on: float, off: float, hold: int) -> list[str]:
    states, current, held = [], "closed", 0
    for n in range(count):
        level = float(envelope[n])
        want = "open" if level > on else ("closed" if level < off else current)
        if want != current and held >= hold:
            current, held = want, 0
        held += 1
        states.append(current)
    return states


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--char", required=True, help="キャラの素材ディレクトリ")
    ap.add_argument("--voice", required=True)
    ap.add_argument("--expression", type=int, required=True)
    ap.add_argument("--on", type=float, default=0.5, help="口を開く音量")
    ap.add_argument("--off", type=float, default=0.3, help="口を閉じる音量")
    ap.add_argument("--hold", type=int, default=2, help="同じ状態を保つ最低コマ数")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    char = Path(args.char)
    pair = json.loads((char / "mouth_pairs.json").read_text()).get(f"{args.expression:02d}")
    if not pair:
        print(f"表情{args.expression}の口ペアがありません", file=sys.stderr)
        return 1

    frames = {state: Image.open(path).convert("RGB").resize((SIZE, SIZE), Image.LANCZOS)
              for state, path in pair.items()}

    wav = Path(args.voice)
    dur = probe_duration(wav)
    count = max(1, int(round(dur * FPS)))
    states = mouth_states(speech_envelope(wav, FPS, count, smooth=False),
                          count, args.on, args.off, args.hold)

    work = Path(args.output).with_suffix("")
    work.mkdir(parents=True, exist_ok=True)
    for old in work.glob("*.png"):
        old.unlink()
    for n, state in enumerate(states):
        frames[state].save(work / f"{n:04d}.png")

    silent = work / "silent.mp4"
    run(["ffmpeg", "-y", "-framerate", str(FPS), "-i", str(work / "%04d.png"),
         "-vf", "format=yuv420p", "-r", str(FPS), "-an", str(silent)])
    run(["ffmpeg", "-y", "-i", str(silent), "-i", str(wav),
         "-c:v", "copy", "-c:a", "aac", "-shortest", str(args.output)])

    opens = sum(1 for s in states if s == "open")
    toggles = sum(1 for i in range(1, len(states)) if states[i] != states[i - 1])
    print(f"{args.output}  {dur:.1f}秒 / 開いている割合 {100*opens/count:.0f}% / "
          f"開閉 {toggles/dur:.1f}回per秒")
    return 0


if __name__ == "__main__":
    sys.exit(main())
