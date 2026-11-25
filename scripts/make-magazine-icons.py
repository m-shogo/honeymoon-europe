#!/usr/bin/env python3
"""旅行誌（magazine/）のアイコンを描く：「Just Married」の札が付いたスーツケース。

  python3 scripts/make-magazine-icons.py   （Pillowと、macOSのSnell Roundhandフォントを使用）

出力：magazine/assets/ の icon-180.png（iPhoneのホーム画面）, icon-192.png, icon-512.png,
      icon-maskable-512.png（Androidで丸く切り抜かれても欠けない余白つき）, favicon-32.png, favicon.svg
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "magazine" / "assets"
S = 1024
SNELL = "/System/Library/Fonts/Supplemental/SnellRoundhand.ttc"
PINK_TOP, PINK_BOTTOM = (255, 176, 168), (236, 104, 112)
CREAM, LEATHER, BELT, RED, SUN, NAVY = (255, 248, 236), (120, 66, 52), (200, 140, 110), (226, 64, 78), (255, 210, 63), (24, 48, 107)


def heart_pts(cx, cy, size, n=400):
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((cx + x * size / 32, cy - y * size / 32))
    return pts


def plane(d, x, y, size, angle, fill):
    shape = [(1.0, 0), (0.55, 0.09), (0.15, 0.09), (-0.25, 0.62), (-0.42, 0.62), (-0.15, 0.09), (-0.6, 0.09),
             (-0.78, 0.32), (-0.9, 0.32), (-0.8, 0), (-0.9, -0.32), (-0.78, -0.32), (-0.6, -0.09), (-0.15, -0.09),
             (-0.42, -0.62), (-0.25, -0.62), (0.15, -0.09), (0.55, -0.09)]
    a = math.radians(angle)
    d.polygon([(x + size * (px * math.cos(a) - py * math.sin(a)), y + size * (px * math.sin(a) + py * math.cos(a))) for px, py in shape], fill=fill)


def draw(k=1.0, small=False, radius=0):
    """k: 絵柄の縮尺（maskable用に0.8）。small: タブ用（細部を省く）。radius: 角丸（favicon用）。"""
    img = Image.new("RGBA", (S, S))
    d = ImageDraw.Draw(img)
    for y in range(S):
        t = y / (S - 1)
        d.line([(0, y), (S, y)], fill=tuple(round(a + (b - a) * t) for a, b in zip(PINK_TOP, PINK_BOTTOM)))
    c = S / 2
    P = lambda x, y: (c + (x - c) * k, c + (y - c) * k)  # 中心から縮尺
    R = lambda x0, y0, x1, y1: [*P(x0, y0), *P(x1, y1)]
    w = lambda v: max(1, round(v * k))
    if small:  # タブ用は大きく、細部なし
        d.rounded_rectangle(R(372, 150, 652, 300), radius=w(60), outline=LEATHER, width=w(70))
        d.rounded_rectangle(R(110, 260, 914, 900), radius=w(120), fill=CREAM)
        d.polygon([P(x, y) for x, y in heart_pts(512, 600, 420)], fill=RED)
    else:
        d.rounded_rectangle(R(392, 250, 632, 350), radius=w(40), outline=LEATHER, width=w(34))  # 取っ手
        d.rounded_rectangle(R(212, 330, 812, 800), radius=w(70), fill=CREAM)
        d.rectangle(R(212, 470, 812, 500), fill=BELT)
        d.rectangle(R(340, 330, 372, 800), fill=BELT)
        d.rectangle(R(652, 330, 684, 800), fill=BELT)
        d.polygon([P(x, y) for x, y in heart_pts(512, 650, 230)], fill=RED)
        d.ellipse(R(250, 360, 380, 460), fill=SUN)  # 旅のステッカー
        d.ellipse(R(660, 540, 780, 660), fill=NAVY)
        px, py = P(720, 600)
        plane(d, px, py, 38 * k, -20, CREAM)
        d.line([P(812, 520), P(870, 600)], fill=LEATHER, width=w(8))  # 札のひも
        tw, th = w(372), w(118)
        tag = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
        td = ImageDraw.Draw(tag)
        td.rounded_rectangle([0, 0, tw - 1, th - 1], radius=w(26), fill=(255, 255, 255))
        td.text((tw / 2, th / 2), "Just Married", font=ImageFont.truetype(SNELL, w(60)), fill=RED, anchor="mm")
        tag = tag.rotate(-14, expand=True, resample=Image.BICUBIC)
        tx, ty = P(578, 618)
        img.paste(tag, (round(tx), round(ty)), tag)
    if radius:
        mask = Image.new("L", (S, S), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, S - 1, S - 1], radius=radius, fill=255)
        img.putalpha(mask)
    return img


def save(img, name, size):
    img.resize((size, size), Image.LANCZOS).save(OUT / name, optimize=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    full = draw()
    save(full.convert("RGB"), "icon-180.png", 180)  # iOSは角丸を自動で付ける
    save(full, "icon-192.png", 192)
    save(full, "icon-512.png", 512)
    save(draw(k=0.78).convert("RGB"), "icon-maskable-512.png", 512)
    save(draw(small=True, radius=200), "favicon-32.png", 32)
    (OUT / "favicon.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
        '<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffb0a8"/><stop offset="1" stop-color="#ec6870"/></linearGradient></defs>'
        '<rect width="64" height="64" rx="13" fill="url(#g)"/>'
        '<rect x="24.5" y="10" width="15" height="9" rx="3.5" fill="none" stroke="#784234" stroke-width="4"/>'
        '<rect x="7" y="16.5" width="50" height="40" rx="7.5" fill="#fff8ec"/>'
        '<path d="M32 50C24.6 44.6 20.5 40.6 20.5 35.6c0-3.4 2.6-6 5.8-6 2.4 0 4.6 1.4 5.7 3.4 1.1-2 3.3-3.4 5.7-3.4 3.2 0 5.8 2.6 5.8 6 0 5-4.1 9-11.5 14.4z" fill="#e2404e"/>'
        '</svg>')
    print("icons ->", OUT)


if __name__ == "__main__":
    main()
