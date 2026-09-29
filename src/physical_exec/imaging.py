from __future__ import annotations
import base64
from io import BytesIO
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw


def png_bytes(array: np.ndarray) -> bytes:
    buf = BytesIO(); Image.fromarray(array).save(buf, format="PNG")
    return buf.getvalue()


def data_url(array: np.ndarray, detail_edge: int | None = None) -> str:
    img = Image.fromarray(array)
    if detail_edge is not None:
        img.thumbnail((detail_edge, detail_edge))
    b = BytesIO(); img.save(b, format="JPEG", quality=90)
    return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode("ascii")


def panel(images: dict[str, np.ndarray], order: tuple[str, ...], max_edge: int = 640) -> np.ndarray:
    """Only real supplied views. Missing views are not fabricated/duplicated."""
    if set(order) != set(images) or len(order) != len(images):
        raise ValueError("panel order must exactly cover the camera names")
    tiles = []
    for role in order:
        im = Image.fromarray(images[role]); im.thumbnail((max_edge, max_edge))
        tile = Image.new("RGB", (im.width, im.height+24), (24, 24, 24))
        tile.paste(im, (0, 24)); ImageDraw.Draw(tile).text((6, 5), role, fill="white")
        tiles.append(tile)
    out = Image.new("RGB", (sum(t.width for t in tiles), max(t.height for t in tiles)), (24, 24, 24))
    x = 0
    for t in tiles:
        out.paste(t, (x, 0)); x += t.width
    return np.asarray(out)


def load_local_rgb(path: str | Path) -> np.ndarray:
    with Image.open(path) as im:
        if im.width > 4096 or im.height > 4096:
            raise ValueError("oversized RGB")
        return np.asarray(im.convert("RGB")).copy()
