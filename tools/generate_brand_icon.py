"""Generate the multi-resolution Windows icon for the 0.3 brand mark."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
CANVAS = 1024
SCALE = CANVAS / 80


def point(value: float) -> int:
    return round(value * SCALE)


def polygon_mask(points: list[tuple[float, float]]) -> Image.Image:
    mask = Image.new("L", (CANVAS, CANVAS), 0)
    ImageDraw.Draw(mask).polygon([(point(x), point(y)) for x, y in points], fill=255)
    return mask


def gradient(start: tuple[int, int, int, int], end: tuple[int, int, int, int]) -> Image.Image:
    image = Image.new("RGBA", (CANVAS, CANVAS))
    pixels = image.load()
    for y in range(CANVAS):
        ratio = y / (CANVAS - 1)
        color = tuple(round(a + (b - a) * ratio) for a, b in zip(start, end))
        for x in range(CANVAS):
            pixels[x, y] = color
    return image


def ellipse(draw: ImageDraw.ImageDraw, box: tuple[float, float, float, float], fill: str) -> None:
    draw.ellipse(tuple(point(value) for value in box), fill=fill)


def build_icon() -> Image.Image:
    image = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    back = [(40, 24), (68, 39), (68, 56), (40, 72), (12, 56), (12, 39)]
    image.alpha_composite(
        Image.composite(
            gradient((139, 124, 255, 205), (85, 72, 201, 205)),
            Image.new("RGBA", image.size),
            polygon_mask(back),
        )
    )

    middle = [(40, 18), (67, 33), (67, 51), (40, 67), (13, 51), (13, 33)]
    draw.polygon([(point(x), point(y)) for x, y in middle], fill="#101829", outline="#8B7CFF", width=point(1.8))

    front = [(40, 8), (64, 22), (64, 45), (40, 59), (16, 45), (16, 22)]
    image.alpha_composite(
        Image.composite(
            gradient((140, 247, 233, 255), (32, 175, 163, 255)),
            Image.new("RGBA", image.size),
            polygon_mask(front),
        )
    )
    draw = ImageDraw.Draw(image)
    draw.line([(point(x), point(y)) for x, y in front + [front[0]]], fill="#DFFFFA", width=point(2), joint="curve")
    draw.line([(point(17), point(44)), (point(40), point(57)), (point(63), point(44))], fill=(229, 255, 251, 135), width=point(1.5))
    draw.line([(point(18), point(23)), (point(40), point(36)), (point(62), point(23))], fill=(244, 255, 253, 105), width=point(1.5))

    dark = "#080B14"
    ellipse(draw, (30.8, 35.3, 49.2, 49.7), dark)
    ellipse(draw, (25.4, 29.6, 32.8, 39.2), dark)
    ellipse(draw, (33.5, 25.1, 40.7, 34.5), dark)
    ellipse(draw, (42.2, 25.8, 49.4, 35.2), dark)
    ellipse(draw, (48.9, 31.1, 56.1, 40.5), dark)
    draw.arc((point(34.5), point(39.7), point(45.5), point(47.8)), 205, 335, fill="#8B7CFF", width=point(2))
    return image


def main() -> None:
    image = build_icon()
    image.resize((512, 512), Image.Resampling.LANCZOS).save(
        ROOT / "frontend/public/brand/palworld-save-studio-icon.png"
    )
    image.save(
        ROOT / "icon.ico",
        format="ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )


if __name__ == "__main__":
    main()
