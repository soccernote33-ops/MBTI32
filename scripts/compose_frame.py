#!/usr/bin/env python3
"""1セリフ分の縦型フレームを組む。

上にテーマ、中央に話者の立ち絵、下に話者名つきの字幕を置く。
字幕は話者ごとに色を変えて、誰の発言か一目で分かるようにする。

立ち絵はカットの間ゆっくり寄り、声の大きいところで軽く弾む。背景のぼかしは
1カット内で変わらないので、使い回して1フレームあたりの処理を軽くしている。
"""

import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT = "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"
W, H = 1080, 1920

TITLE_TOP, TITLE_H = 70, 132
PORTRAIT_W = 1000
PORTRAIT_TOP = TITLE_TOP + TITLE_H + 120
SUBTITLE_BOTTOM, SUBTITLE_MIN_H = 150, 230
SIDE = 60
BODY_SIZE, NAME_SIZE, TITLE_SIZE = 52, 34, 58
CHARS_PER_LINE = 17

ZOOM_PER_CUT = 0.035      # カット中にゆっくり寄る量
POP_IN_SEC = 0.22         # カット頭の飛び込み
BOB_PIXELS = 14           # 声に合わせて弾む幅
SUBTITLE_SLIDE_SEC = 0.18


def wrap_japanese(text: str, limit: int) -> list[str]:
    """句読点で優先的に折り、無ければ文字数で折る"""
    lines, current = [], ""
    for ch in text:
        current += ch
        if len(current) >= limit or (ch in "、。！？" and len(current) >= limit - 4):
            lines.append(current)
            current = ""
    if current:
        lines.append(current)
    return lines or [""]


def speech_envelope(wav_path: Path, fps: int, frames: int) -> np.ndarray:
    """音量の起伏を0〜1で返す。立ち絵の弾みに使う"""
    with wave.open(str(wav_path), "rb") as w:
        rate = w.getframerate()
        data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(float)
        if w.getnchannels() == 2:
            data = data.reshape(-1, 2).mean(axis=1)

    window = max(1, rate // fps)
    env = np.zeros(frames)
    for i in range(frames):
        chunk = data[i * window:(i + 1) * window]
        if len(chunk):
            env[i] = np.sqrt((chunk ** 2).mean())
    peak = env.max()
    if peak > 0:
        env /= peak
    # 急に跳ねないようにならす
    return np.convolve(env, np.ones(3) / 3, mode="same")


def make_background(portrait: Image.Image) -> Image.Image:
    scale = max(W / portrait.width, H / portrait.height)
    bg = portrait.resize((int(portrait.width * scale), int(portrait.height * scale)),
                         Image.LANCZOS)
    left, top = (bg.width - W) // 2, (bg.height - H) // 2
    bg = bg.crop((left, top, left + W, top + H)).filter(ImageFilter.GaussianBlur(45))
    return Image.blend(bg, Image.new("RGB", (W, H), (20, 22, 30)), 0.35)


def _rounded(img: Image.Image, radius: int) -> Image.Image:
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, img.width - 1, img.height - 1],
                                           radius=radius, fill=255)
    img.putalpha(mask)
    return img


def render_frame(background: Image.Image, portrait: Image.Image, title: str,
                 speaker: str, text: str, accent: tuple[int, int, int],
                 progress: float = 1.0, loudness: float = 0.0,
                 elapsed: float = 99.0) -> Image.Image:
    frame = background.copy().convert("RGBA")

    # 立ち絵: ゆっくり寄りつつ、カット頭は少し小さいところから入る
    scale = 1.0 + ZOOM_PER_CUT * progress
    if elapsed < POP_IN_SEC:
        t = elapsed / POP_IN_SEC
        scale *= 0.94 + 0.06 * (1 - (1 - t) ** 3)
    width = int(PORTRAIT_W * scale)
    height = int(portrait.height * width / portrait.width)
    fg = _rounded(portrait.resize((width, height), Image.LANCZOS).convert("RGBA"), 40)

    y = PORTRAIT_TOP - int((height - portrait.height * PORTRAIT_W / portrait.width) / 2)
    frame.alpha_composite(fg, ((W - width) // 2, int(y - BOB_PIXELS * loudness)))

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    f_title = ImageFont.truetype(FONT, TITLE_SIZE)
    draw.rounded_rectangle([SIDE, TITLE_TOP, W - SIDE, TITLE_TOP + TITLE_H],
                           radius=28, fill=(24, 26, 34, 225))
    tw = draw.textlength(title, font=f_title)
    draw.text(((W - tw) / 2, TITLE_TOP + 34), title, font=f_title, fill=(255, 255, 255, 255))

    # 字幕: カット頭で下から入る
    slide = 0
    alpha = 255
    if elapsed < SUBTITLE_SLIDE_SEC:
        t = elapsed / SUBTITLE_SLIDE_SEC
        slide = int(34 * (1 - t) ** 2)
        alpha = int(255 * t)

    f_body = ImageFont.truetype(FONT, BODY_SIZE)
    f_name = ImageFont.truetype(FONT, NAME_SIZE)
    lines = wrap_japanese(text, CHARS_PER_LINE)
    box_h = max(SUBTITLE_MIN_H, 118 + len(lines) * (BODY_SIZE + 16))
    y1 = H - SUBTITLE_BOTTOM + slide
    y0 = y1 - box_h

    draw.rounded_rectangle([SIDE, y0, W - SIDE, y1], radius=30,
                           fill=(18, 20, 28, int(232 * alpha / 255)))
    draw.rounded_rectangle([SIDE, y0, SIDE + 14, y1], radius=7, fill=accent + (alpha,))
    draw.text((SIDE + 44, y0 + 26), speaker, font=f_name,
              fill=tuple(min(255, c + 90) for c in accent) + (alpha,))
    for i, line in enumerate(lines):
        draw.text((SIDE + 44, y0 + 84 + i * (BODY_SIZE + 16)), line,
                  font=f_body, fill=(255, 255, 255, alpha))

    return Image.alpha_composite(frame, layer).convert("RGB")


def compose(portrait_path: Path, title: str, speaker: str, text: str,
            accent: tuple[int, int, int]) -> Image.Image:
    """静止画1枚だけ欲しいとき用"""
    portrait = Image.open(portrait_path).convert("RGB")
    return render_frame(make_background(portrait), portrait, title, speaker, text, accent)
