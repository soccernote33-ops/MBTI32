#!/usr/bin/env python3
"""台本JSONと音声クリップから、会話形式の動画を組み立てる。

音声は「行番号_キャラキー.wav」(例: 01_yuina.wav)で用意する。
台本の各行が指定する表情画像を、その行の音声が鳴っている間だけ表示する。

    python3 scripts/build_episode.py \
        --script data/scripts/ep01_chikoku.json \
        --voice-dir data/episodes/ep01/voices
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from compose_frame import compose

PAUSE_SECONDS = 0.25
FPS = 24


def probe_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def run(cmd: list[str]) -> None:
    subprocess.run(cmd + ["-v", "error"], check=True)


def find_expression(asset_dir: Path, number: int) -> Path:
    """ラベル除去済みの画像を優先し、無ければ切り出したままの画像を使う"""
    for folder in ("expressions_clean", "expressions"):
        matches = sorted((asset_dir / folder).glob(f"{number:02d}_*.png"))
        if matches:
            return matches[0]
    raise FileNotFoundError(f"表情{number}の画像が {asset_dir} にありません")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", required=True)
    ap.add_argument("--voice-dir", required=True)
    ap.add_argument("--output", default=None)
    ap.add_argument("--allow-missing", action="store_true",
                    help="音声が揃っていない行を飛ばして、途中までのプレビューを作る")
    args = ap.parse_args()

    script = json.loads(Path(args.script).read_text())
    voice_dir = Path(args.voice_dir)
    work = voice_dir.parent / "build"
    work.mkdir(parents=True, exist_ok=True)

    missing = []
    plan = []
    for line in script["lines"]:
        speaker = line["speaker"]
        wav = voice_dir / f"{line['no']:02d}_{speaker}.wav"
        if not wav.exists():
            missing.append(wav.name)
            continue
        asset_dir = script["cast"][speaker].get("asset_dir")
        if not asset_dir:
            missing.append(f"{speaker}の素材ディレクトリ未設定")
            continue
        plan.append((line, wav, find_expression(Path(asset_dir), line["expression"])))

    if missing and not args.allow_missing:
        print("以下が見つからないため中断します:", file=sys.stderr)
        for m in missing:
            print(f"  - {m}", file=sys.stderr)
        return 1
    if missing:
        print(f"未収録{len(missing)}行を飛ばします: {', '.join(missing)}")
    if not plan:
        print("使える音声が1本もありません", file=sys.stderr)
        return 1

    pause = work / "pause.wav"
    run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
         "-t", str(PAUSE_SECONDS), "-c:a", "pcm_s16le", str(pause)])

    audio_parts, segments = [], []
    for i, (line, wav, image) in enumerate(plan):
        if i:
            audio_parts.append(pause)
        audio_parts.append(wav)

        dur = probe_duration(wav) + (PAUSE_SECONDS if i < len(plan) - 1 else 0)

        cast = script["cast"][line["speaker"]]
        frame_path = work / f"frame{line['no']:02d}.png"
        compose(
            image,
            script["title"],
            f"{cast['name']}（{cast['mbti']}）",
            line["text"],
            tuple(cast.get("accent", [90, 100, 120])),
        ).save(frame_path)

        seg = work / f"seg{line['no']:02d}.mp4"
        run(["ffmpeg", "-y", "-loop", "1", "-i", str(frame_path), "-t", f"{dur:.3f}",
             "-vf", "format=yuv420p", "-r", str(FPS), "-an", str(seg)])
        segments.append(seg)

    audio_list = work / "audio_list.txt"
    audio_list.write_text("".join(f"file '{p.resolve()}'\n" for p in audio_parts))
    audio = work / "episode_audio.wav"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(audio_list),
         "-c:a", "pcm_s16le", str(audio)])

    video_list = work / "video_list.txt"
    video_list.write_text("".join(f"file '{s.resolve()}'\n" for s in segments))
    silent = work / "silent.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(video_list),
         "-c", "copy", str(silent)])

    output = Path(args.output) if args.output else voice_dir.parent / f"{script['episode_id']}.mp4"
    run(["ffmpeg", "-y", "-i", str(silent), "-i", str(audio),
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(output)])

    print(f"完成: {output} ({probe_duration(output):.1f}秒 / {len(plan)}カット)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
