"""Generate DeepSleep launcher icons from the reference artwork.

Run with the harness Pillow runtime:
  python scripts/make-icon.py <source image> <android res dir>
"""

import sys
from pathlib import Path

from PIL import Image

# Square crop around the character's face inside the 1008x1006 source artwork.
CROP = (128, 96, 1008, 976)

# Adaptive icon foreground safe zone: 72dp of 108dp.
FOREGROUND_SCALE = 0.74

LEGACY = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}
ADAPTIVE = {"mdpi": 108, "hdpi": 162, "xhdpi": 216, "xxhdpi": 324, "xxxhdpi": 432}


def rounded(image: Image.Image, radius_ratio: float) -> Image.Image:
    """Round the corners so launchers that do not mask still look intentional."""
    from PIL import ImageDraw

    size = image.size[0]
    mask = Image.new("L", (size * 4, size * 4), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, size * 4 - 1, size * 4 - 1), radius=int(size * 4 * radius_ratio), fill=255
    )
    mask = mask.resize((size, size), Image.LANCZOS)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(image, (0, 0), mask)
    return out


def main() -> None:
    source = Image.open(sys.argv[1]).convert("RGB")
    res = Path(sys.argv[2])
    art = source.crop(CROP)
    edge = source.getpixel((4, 4))

    for density, size in LEGACY.items():
        folder = res / f"mipmap-{density}"
        folder.mkdir(parents=True, exist_ok=True)
        icon = art.resize((size, size), Image.LANCZOS)
        icon = rounded(icon, 0.22)
        icon.save(folder / "ic_launcher.png", optimize=True)

    for density, size in ADAPTIVE.items():
        folder = res / f"mipmap-{density}"
        folder.mkdir(parents=True, exist_ok=True)
        canvas = Image.new("RGB", (size, size), edge)
        inner = int(size * FOREGROUND_SCALE)
        canvas.paste(art.resize((inner, inner), Image.LANCZOS), ((size - inner) // 2,) * 2)
        canvas.save(folder / "ic_launcher_foreground.png", optimize=True)

    art.resize((512, 512), Image.LANCZOS).save(res.parent / "icon-512.png", optimize=True)
    print(f"edge={edge} crop={art.size}")


main()
