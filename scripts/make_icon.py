#!/usr/bin/env python3
"""拡張機能のアイコン (虫眼鏡) を生成する。

高解像度 (1024px) で描画してから各サイズに縮小し、輪郭を滑らかにする。
出力: ../icons/icon16.png, icon32.png, icon48.png, icon128.png

色: ブランド青 (#0d6efd) の角丸背景に白い虫眼鏡。
依存: Pillow のみ。外部サービスには一切アクセスしない。
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw

ICONS_DIR = Path(__file__).resolve().parent.parent / "icons"
MASTER = 1024
BG = (13, 110, 253, 255)      # #0d6efd
GLASS = (255, 255, 255, 255)  # 白
SIZES = [16, 32, 48, 128]


def rounded_handle(draw: ImageDraw.ImageDraw, p0, p1, width: int, fill) -> None:
    """両端が丸い太線 (虫眼鏡の柄)。線 + 両端の円で丸キャップを作る。"""
    draw.line([p0, p1], fill=fill, width=width)
    r = width // 2
    for (x, y) in (p0, p1):
        draw.ellipse([x - r, y - r, x + r, y + r], fill=fill)


def draw_master() -> Image.Image:
    img = Image.new("RGBA", (MASTER, MASTER), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # 角丸の背景 (少し余白をとる)
    pad = 70
    d.rounded_rectangle([pad, pad, MASTER - pad, MASTER - pad], radius=210, fill=BG)

    # 虫眼鏡のレンズ (白いリング)
    cx, cy, r_out = 430, 430, 215
    ring = 86
    d.ellipse([cx - r_out, cy - r_out, cx + r_out, cy + r_out], outline=GLASS, width=ring)

    # 柄 (レンズ右下から外側へ。レンズと少し重ねて繋ぐ)
    ang = math.radians(45)
    start = (cx + (r_out - ring // 2) * math.cos(ang), cy + (r_out - ring // 2) * math.sin(ang))
    end = (cx + 360 * math.cos(ang), cy + 360 * math.sin(ang))
    rounded_handle(d, start, end, width=96, fill=GLASS)

    return img


def main() -> None:
    ICONS_DIR.mkdir(parents=True, exist_ok=True)
    master = draw_master()
    for s in SIZES:
        out = master.resize((s, s), Image.LANCZOS)
        out.save(ICONS_DIR / f"icon{s}.png")
        print(f"作成: icons/icon{s}.png ({s}x{s})")


if __name__ == "__main__":
    main()
