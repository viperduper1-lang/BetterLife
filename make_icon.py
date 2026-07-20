#!/usr/bin/env python3
"""Generează icon.ico pentru BetterLife (fundal gradient emerald + emoji salată)."""
from PIL import Image, ImageDraw, ImageFont

SIZE = 256
RADIUS = 58
EMOJI = "🥗"
TOP = (52, 211, 153)      # #34d399
BOTTOM = (5, 150, 105)    # #059669


def gradient(size, top, bottom):
    img = Image.new("RGB", (size, size), top)
    px = img.load()
    for y in range(size):
        t = y / (size - 1)
        for x in range(size):
            tt = (t + x / (size - 1)) / 2  # diagonal
            px[x, y] = (
                int(top[0] + (bottom[0] - top[0]) * tt),
                int(top[1] + (bottom[1] - top[1]) * tt),
                int(top[2] + (bottom[2] - top[2]) * tt),
            )
    return img


def rounded_mask(size, radius):
    mask = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    return mask


def build():
    base = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    bg = gradient(SIZE, TOP, BOTTOM).convert("RGBA")
    base.paste(bg, (0, 0), rounded_mask(SIZE, RADIUS))

    # emoji color, centrat
    drew = False
    try:
        font = ImageFont.truetype("seguiemj.ttf", 168)
        layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        bbox = d.textbbox((0, 0), EMOJI, font=font, embedded_color=True)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        pos = ((SIZE - w) // 2 - bbox[0], (SIZE - h) // 2 - bbox[1] - 4)
        d.text(pos, EMOJI, font=font, embedded_color=True)
        base = Image.alpha_composite(base, layer)
        drew = True
    except Exception as exc:  # noqa: BLE001
        print("emoji fallback:", exc)

    if not drew:
        d = ImageDraw.Draw(base)
        try:
            font = ImageFont.truetype("segoeuib.ttf", 130)
        except Exception:  # noqa: BLE001
            font = ImageFont.load_default()
        d.text((SIZE // 2, SIZE // 2 - 8), "BL", font=font, fill="white", anchor="mm")

    base.save("icon_preview.png")
    base.save("icon.png")  # folosit ca iconiță în notificările de pe telefon
    sizes = [(s, s) for s in (16, 24, 32, 48, 64, 128, 256)]
    base.save("icon.ico", sizes=sizes)
    print("Scris: icon.ico + icon.png + icon_preview.png")


if __name__ == "__main__":
    build()
