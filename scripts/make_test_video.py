#!/usr/bin/env python3
"""表情画像と音声クリップから、表情を切り替えるテスト動画を生成する。

使い方:
    python3 scripts/make_test_video.py \
        --char-dir data/assets/isfj_mizuki_nagisa \
        --voice-id 1932338715 \
        --expressions 01_egao 03_yasashii_emi 09_tere
"""

import argparse
import subprocess
import sys
from pathlib import Path

GAP_SECONDS = 0.3
VIDEO_WIDTH = 480
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


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--char-dir", required=True)
    p.add_argument("--voice-id", required=True)
    p.add_argument("--expressions", nargs="+", required=True)
    p.add_argument("--output", default=None)
    args = p.parse_args()

    char_dir = Path(args.char_dir)
    work = char_dir / "test_video"
    work.mkdir(parents=True, exist_ok=True)

    clips = sorted((char_dir / "voice_samples").glob(f"{args.voice_id}_*.wav"))
    if not clips:
        print(f"音声が見つかりません: {args.voice_id}", file=sys.stderr)
        return 1
    if len(clips) != len(args.expressions):
        print(f"音声{len(clips)}本に対し表情{len(args.expressions)}枚が指定されています",
              file=sys.stderr)
        return 1

    gap = work / "gap.wav"
    run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
         "-t", str(GAP_SECONDS), "-c:a", "pcm_s16le", str(gap)])

    audio_list = work / "audio_list.txt"
    parts = []
    for i, clip in enumerate(clips):
        if i:
            parts.append(gap)
        parts.append(clip)
    audio_list.write_text("".join(f"file '{p.resolve()}'\n" for p in parts))

    audio = work / "combined_audio.wav"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(audio_list),
         "-c:a", "pcm_s16le", str(audio)])

    # 各セリフの長さ（＋後続の無音）に合わせて表情を切り替える
    segments = []
    for i, (clip, expr) in enumerate(zip(clips, args.expressions)):
        dur = probe_duration(clip) + (GAP_SECONDS if i < len(clips) - 1 else 0)
        img = char_dir / "expressions" / f"{expr}.png"
        if not img.exists():
            print(f"表情画像が見つかりません: {img}", file=sys.stderr)
            return 1
        seg = work / f"seg{i + 1}.mp4"
        run(["ffmpeg", "-y", "-loop", "1", "-i", str(img), "-t", f"{dur:.3f}",
             "-vf", f"scale={VIDEO_WIDTH}:-2,format=yuv420p", "-r", str(FPS),
             "-an", str(seg)])
        segments.append(seg)

    video_list = work / "video_list.txt"
    video_list.write_text("".join(f"file '{s.resolve()}'\n" for s in segments))
    silent = work / "silent_video.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(video_list),
         "-c", "copy", str(silent)])

    output = Path(args.output) if args.output else work / f"test_{char_dir.name}.mp4"
    run(["ffmpeg", "-y", "-i", str(silent), "-i", str(audio),
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(output)])

    print(f"生成しました: {output} ({probe_duration(output):.1f}秒)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
