import os, glob
import numpy as np
from PIL import Image, ImageOps, ImageFilter

AUTHOR = "D230212"
NIM = "535230212"
SRC = os.path.join("ML", "MLD", AUTHOR, f"{NIM}_Original")
DST = os.path.join("ML", "MLD", AUTHOR)


def segment_lines(path, min_h=25, pad=12, ink_thr=0.012, merge_gap=18):
    img = Image.open(path).convert("L")
    img = ImageOps.autocontrast(img, cutoff=1)
    a = np.array(img).astype(np.float32)

    # ambil tinta gelap saja, abaikan tulisan tembus dari balik kertas
    bg = np.array(img.filter(ImageFilter.GaussianBlur(40))).astype(np.float32)
    ink = (bg - a) > 60
    ink[:, : int(0.02 * a.shape[1])] = False
    ink[:, -int(0.02 * a.shape[1]):] = False

    prof = np.convolve(ink.mean(axis=1), np.ones(9) / 9, mode="same")
    rows = prof > ink_thr

    bands, start = [], None
    for i, v in enumerate(rows):
        if v and start is None:
            start = i
        elif not v and start is not None:
            bands.append([start, i]); start = None
    if start is not None:
        bands.append([start, len(rows)])

    merged = []
    for b in bands:
        if merged and b[0] - merged[-1][1] < merge_gap:
            merged[-1][1] = b[1]
        else:
            merged.append(b)
    merged = [b for b in merged if b[1] - b[0] >= min_h]

    crops = []
    for y0, y1 in merged:
        y0, y1 = max(0, y0 - pad), min(a.shape[0], y1 + pad)
        cols = np.where(ink[y0:y1].mean(axis=0) > 0.003)[0]
        if len(cols) == 0:
            continue
        x0, x1 = max(0, cols[0] - pad), min(a.shape[1], cols[-1] + pad)
        crop = img.crop((x0, y0, x1, y1))
        if crop.size[0] / crop.size[1] >= 3:
            crops.append(crop)
    return crops


n = 0
for p in sorted(glob.glob(os.path.join(SRC, "*.jpg"))):
    for c in segment_lines(p):
        n += 1
        c.save(os.path.join(DST, f"{NIM}_{n}.jpg"), quality=95)
print("Potongan dibuat:", n)
