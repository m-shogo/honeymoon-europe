#!/usr/bin/env python3
"""旅行誌（magazine/）のアイコンを描く。コーラルの地に白いハート、点線の航路と飛行機。

  python3 scripts/make-magazine-icons.py   （Pillowが必要）

出力：magazine/assets/ の icon-180.png（iPhoneのホーム画面）, icon-192.png, icon-512.png,
      icon-maskable-512.png（Androidの丸・角丸に切り抜かれても欠けない余白つき）, favicon-32.png, favicon.svg
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent.parent / "magazine" / "assets"
S = 1024  # 描画は大きく描いて縮小（なめらかにする）
CORAL_TOP, CORAL_BOTTOM = (255, 118, 92), (232, 70, 52)
CREAM, SUN, NAVY = (255, 251, 243), (255, 210, 63), (24, 48, 107)


def background(img, radius=0):
    d = ImageDraw.Draw(img)
    for y in range(S):
        t = y / (S - 1)
        c = tuple(round(a + (b - a) * t) for a, b in zip(CORAL_TOP, CORAL_BOTTOM))
        d.line([(0, y), (S, y)], fill=c)
    if radius:
        mask = Image.new("L", (S, S), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, S - 1, S - 1], radius=radius, fill=255)
        img.putalpha(mask)


def heart(d, cx, cy, size, fill):
    pts = []
    for i in range(400):
        t = 2 * math.pi * i / 400
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((cx + x * size / 32, cy - y * size / 32))
    d.polygon(pts, fill=fill)


def plane(d, x, y, size, angle, fill):
    # 上から見た飛行機（機首は +x 方向）
    shape = [(1.0, 0), (0.55, 0.09), (0.15, 0.09), (-0.25, 0.62), (-0.42, 0.62), (-0.15, 0.09), (-0.6, 0.09),
             (-0.78, 0.32), (-0.9, 0.32), (-0.8, 0), (-0.9, -0.32), (-0.78, -0.32), (-0.6, -0.09), (-0.15, -0.09),
             (-0.42, -0.62), (-0.25, -0.62), (0.15, -0.09), (0.55, -0.09)]
    a = math.radians(angle)
    pts = [(x + size * (px * math.cos(a) - py * math.sin(a)), y + size * (px * math.sin(a) + py * math.cos(a))) for px, py in shape]
    d.polygon(pts, fill=fill)


def trail(d, cx, cy, r, start, end, dot, gap):
    a = start
    while a < end:
        x, y = cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))
        d.ellipse([x - dot, y - dot, x + dot, y + dot], fill=SUN)
        a += gap


def draw(scale=1.0, radius=0, with_plane=True):
    img = Image.new("RGBA", (S, S))
    background(img, radius)
    d = ImageDraw.Draw(img)
    c = S / 2
    k = scale
    if with_plane:
        trail(d, c, c + 20 * k, 360 * k, 150, 318, 13 * k, 13)
    heart(d, c, c + 40 * k, 560 * k, CREAM)
    heart(d, c, c + 40 * k, 250 * k, (255, 226, 210))  # ハートの中の小さなハート（やわらかい影）
    heart(d, c, c + 34 * k, 230 * k, CORAL_BOTTOM)
    if with_plane:
        a = math.radians(318)
        px, py = c + 360 * k * math.cos(a), c + 20 * k + 360 * k * math.sin(a)
        plane(d, px, py, 112 * k, 318 + 90, NAVY)
    return img


def save(img, name, size):
    img.resize((size, size), Image.LANCZOS).save(OUT / name, optimize=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    full = draw()
    save(full.convert("RGB"), "icon-180.png", 180)   # iOSは角丸を自動で付ける
    save(full, "icon-192.png", 192)
    save(full, "icon-512.png", 512)
    save(draw(scale=0.78).convert("RGB"), "icon-maskable-512.png", 512)  # 中央80%に収める
    save(draw(radius=230, with_plane=False), "favicon-32.png", 32)
    (OUT / "favicon.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
        '<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ff765c"/><stop offset="1" stop-color="#e84634"/></linearGradient></defs>'
        '<rect width="64" height="64" rx="15" fill="url(#g)"/>'
        '<path d="M32 52C18 42 10 34 10 24.5 10 18 15 13 21 13c4.6 0 8.6 2.6 11 6.4C34.4 15.6 38.4 13 43 13c6 0 11 5 11 11.5C54 34 46 42 32 52z" fill="#fffbf3"/>'
        '<path d="M32 40c-5.4-3.9-8.5-7-8.5-10.6 0-2.5 1.9-4.4 4.2-4.4 1.8 0 3.3 1 4.3 2.5 1-1.5 2.5-2.5 4.3-2.5 2.3 0 4.2 1.9 4.2 4.4C40.5 33 37.4 36.1 32 40z" fill="#e84634"/>'
        '</svg>')
    print("icons ->", OUT)


if __name__ == "__main__":
    main()
