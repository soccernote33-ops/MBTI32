#!/usr/bin/env python3
"""台本の各行を Gemini の音声合成で読み上げ、wav に落とす。

COEIROINKは画面から1行ずつ書き出す必要があり、20行のエピソードでも手間が大きい。
こちらは台本を渡せば全行がまとめて生成される。出力の名前と形式は
build_episode.py がそのまま読める形（01_yuina.wav）に揃えてある。

    # 環境の「API認証情報」に登録済みならキーの指定は不要
    #   許可ウェブサイト: generativelanguage.googleapis.com
    #   カスタムヘッダー: x-goog-api-key (プレフィックスなし)
    python3 scripts/tts_gemini.py --script data/scripts/ep01_chikoku.json \
                                  --out data/episodes/ep01/voices_gemini
    python3 scripts/tts_gemini.py --script ... --out ... --only 1   # 1行だけ試す

声はキャラごとに voice を割り当てる。話し方の指示 (style) も渡せるので、
同じ声でも演じ分けができる。使える voice 名は実際のAPIに合わせて直すこと。
"""

import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
import wave
from pathlib import Path

API = ("https://generativelanguage.googleapis.com/v1beta/models/"
       "{model}:generateContent")
DEFAULT_MODEL = "gemini-2.5-flash-preview-tts"

# 出力はヘッダのない PCM で返るため、wav に詰め直す
RETRIES = 4       # レート制限に当たったときの再試行回数
BACKOFF = 30      # 待ち時間の基準(秒)。試行ごとに伸ばす
PACE = 4          # 連続生成時に1行ごとに空ける間隔(秒)

SAMPLE_RATE = 24000
SAMPLE_WIDTH = 2
CHANNELS = 1

# キャラごとの声と話し方。声の名前は使うモデルで実在するものに合わせる。
VOICES = {
    "yuina": {"voice": "Aoede", "style": "明るく前向きに、少し早口で"},
    "nagisa": {"voice": "Kore", "style": "やわらかく、控えめに"},
    "riku": {"voice": "Charon", "style": "淡々と、抑揚を抑えて"},
    "shun": {"voice": "Puck", "style": "軽いノリで、元気よく"},
}


def synthesise(text: str, voice: str, style: str, model: str, key: str | None) -> bytes:
    prompt = f"{style}読み上げてください: {text}" if style else text
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}
            },
        },
    }).encode()

    # 環境のAPI認証情報に登録してある場合、キーは送信時に差し込まれるので
    # こちらでは付けない。環境変数がある時だけ自前で付ける。
    headers = {"Content-Type": "application/json"}
    if key:
        headers["x-goog-api-key"] = key

    request = urllib.request.Request(API.format(model=model), data=body, headers=headers)
    with urllib.request.urlopen(request, timeout=120) as response:
        payload = json.load(response)

    for part in payload["candidates"][0]["content"]["parts"]:
        data = part.get("inlineData") or part.get("inline_data")
        if data:
            return base64.b64decode(data["data"])
    raise RuntimeError(f"音声が返りませんでした: {json.dumps(payload)[:400]}")


def write_wav(path: Path, pcm: bytes) -> None:
    with wave.open(str(path), "wb") as w:
        w.setnchannels(CHANNELS)
        w.setsampwidth(SAMPLE_WIDTH)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(pcm)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--only", type=int, help="この行番号だけ生成する")
    ap.add_argument("--force", action="store_true", help="生成済みも作り直す")
    args = ap.parse_args()

    # 環境のAPI認証情報を使う場合は未設定で正しい
    key = os.environ.get("GEMINI_API_KEY")

    script = json.loads(Path(args.script).read_text())
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    lines = script["lines"]
    if args.only:
        lines = [l for l in lines if l["no"] == args.only]
        if not lines:
            print(f"{args.only}行目が台本にありません", file=sys.stderr)
            return 1

    for line in lines:
        speaker = line["speaker"]
        setting = VOICES.get(speaker, {})
        target = out_dir / f"{line['no']:02d}_{speaker}.wav"

        # 生成済みは飛ばす。レート制限で中断しても続きから再開できる
        if target.exists() and not args.force:
            print(f"{target.name}  生成済みのため省略")
            continue

        pcm = None
        for attempt in range(RETRIES):
            try:
                pcm = synthesise(line["text"], setting.get("voice", "Kore"),
                                 setting.get("style", ""), args.model, key)
                break
            except urllib.error.HTTPError as err:
                if err.code != 429 or attempt == RETRIES - 1:
                    print(f"{target.name}: {err.code} {err.read().decode()[:300]}",
                          file=sys.stderr)
                    return 1
                wait = BACKOFF * (attempt + 1)
                print(f"{target.name}: レート制限のため{wait}秒待ちます")
                time.sleep(wait)

        write_wav(target, pcm)
        print(f"{target.name}  {len(pcm) / (SAMPLE_RATE * SAMPLE_WIDTH):.1f}秒  {line['text'][:20]}")
        time.sleep(PACE)

    return 0


if __name__ == "__main__":
    sys.exit(main())
