#!/usr/bin/env python3
"""Chrome ウェブストア用スクリーンショット (1280x800, アルファなし) を作る。

Playwright で撮った拡張パネルの実画像 (~/finder_*.png) を、
ブランド色の背景＋日本語キャプション付きで 1280x800 に合成する。

出力: ~/Desktop/ebayカテゴリー発見君_提出用/スクショ{n}_*.png (RGB / 24bit / アルファなし)
依存: Pillow のみ。外部アクセスなし。
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HOME = Path.home()
OUT_DIR = HOME / "Desktop" / "ebayカテゴリー発見君_提出用"
ICON = HOME / "Desktop" / "ebay-category-finder" / "icons" / "icon128.png"
W, H = 1280, 800
TOP = (220, 233, 255)
BOTTOM = (247, 250, 255)
INK = (11, 42, 74)
SUB = (71, 85, 105)
MUTED = (120, 134, 156)

F_BOLD = "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc"
F_REG = "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc"

SHOTS = [
    ("finder_toreka.png", "スクショ1_検索.png",
     "日本語で、ぴったりのカテゴリを。",
     "「トレカ」「まとめ」「シングル」など日本語で検索。eBay 出品のカテゴリ ID がすぐ見つかります。"),
    ("finder_watch.png", "スクショ2_日本語訳.png",
     "英語が読めなくても大丈夫。",
     "主要 4,931 カテゴリに日本語訳つき。各候補に日本語を大きく表示します。"),
    ("finder_tree.png", "スクショ3_ツリー.png",
     "ツリーでたどって選べる。",
     "34 の大分類から枝をたどって、目的のカテゴリへ。"),
    ("finder_verify.png", "スクショ4_検証.png",
     "カテゴリ ID を検証。",
     "手元の ID が現在のカテゴリ表にあるか、ワンタッチで確認できます。"),
]


def gradient() -> Image.Image:
    img = Image.new("RGB", (W, H))
    px = img.load()
    for y in range(H):
        t = y / (H - 1)
        r = round(TOP[0] + (BOTTOM[0] - TOP[0]) * t)
        g = round(TOP[1] + (BOTTOM[1] - TOP[1]) * t)
        b = round(TOP[2] + (BOTTOM[2] - TOP[2]) * t)
        for x in range(W):
            px[x, y] = (r, g, b)
    return img


def rounded(im: Image.Image, radius: int) -> Image.Image:
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, im.size[0], im.size[1]], radius=radius, fill=255)
    out = im.convert("RGBA")
    out.putalpha(mask)
    return out


def wrap(draw, text, font, max_w):
    lines, cur = [], ""
    for ch in text:
        if ch == "\n":
            lines.append(cur); cur = ""; continue
        if draw.textlength(cur + ch, font=font) <= max_w:
            cur += ch
        else:
            lines.append(cur); cur = ch
    if cur:
        lines.append(cur)
    return lines


def compose(panel_path: Path, out_name: str, headline: str, sub: str) -> None:
    canvas = gradient()
    draw = ImageDraw.Draw(canvas)

    # --- 右側: パネル実画像 (角丸＋影) ---
    panel = Image.open(panel_path).convert("RGB")
    target_h = 724
    scale = target_h / panel.height
    pw, ph = round(panel.width * scale), target_h
    panel = panel.resize((pw, ph), Image.LANCZOS)
    px0, py0 = W - pw - 76, (H - ph) // 2

    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        [px0 + 8, py0 + 14, px0 + pw + 8, py0 + ph + 14], radius=20, fill=(15, 40, 80, 70))
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), shadow).convert("RGB")
    draw = ImageDraw.Draw(canvas)

    panel_r = rounded(panel, 20)
    canvas.paste(panel_r, (px0, py0), panel_r)
    draw.rounded_rectangle([px0, py0, px0 + pw, py0 + ph], radius=20, outline=(210, 220, 236), width=2)

    # --- 左側: アイコン + 名前 + 見出し + 説明 ---
    lx = 78
    icon = Image.open(ICON).convert("RGBA").resize((92, 92), Image.LANCZOS)
    canvas.paste(icon, (lx, 92), icon)
    name_font = ImageFont.truetype(F_BOLD, 30)
    draw.text((lx + 110, 118), "ebayカテゴリー発見君", font=name_font, fill=INK)

    head_font = ImageFont.truetype(F_BOLD, 46)
    sub_font = ImageFont.truetype(F_REG, 26)
    max_w = px0 - lx - 48

    y = 250
    for line in wrap(draw, headline, head_font, max_w):
        draw.text((lx, y), line, font=head_font, fill=INK)
        y += 62
    y += 16
    for line in wrap(draw, sub, sub_font, max_w):
        draw.text((lx, y), line, font=sub_font, fill=SUB)
        y += 40

    # 信頼バッジ (下部・青いピル)
    badge_font = ImageFont.truetype(F_BOLD, 22)
    label = "完全オフライン ・ eBay 非アクセス"
    tw = draw.textlength(label, font=badge_font)
    bx, by = lx, H - 96
    draw.rounded_rectangle([bx, by, bx + tw + 44, by + 46], radius=23, fill=(13, 110, 253))
    draw.text((bx + 22, by + 9), label, font=badge_font, fill=(255, 255, 255))

    canvas.save(OUT_DIR / out_name)  # RGB PNG = 24bit アルファなし
    print(f"作成: {out_name} ({canvas.size[0]}x{canvas.size[1]}, {canvas.mode})")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for src, name, head, sub in SHOTS:
        p = HOME / src
        if not p.exists():
            print(f"スキップ (元画像なし): {p}")
            continue
        compose(p, name, head, sub)


if __name__ == "__main__":
    main()
