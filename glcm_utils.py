import cv2
import numpy as np
from skimage.feature import graycomatrix, graycoprops

H, W = 64, 512
LEVELS = 32
DISTS = [1, 3, 5]
ANGLES = [0, np.pi / 4, np.pi / 2, 3 * np.pi / 4]
PROPS = ['dissimilarity', 'correlation', 'homogeneity', 'contrast', 'energy']


def to_gray(img):
    if img is None or img.size == 0:
        raise ValueError('Gambar kosong.')

    if img.dtype == np.uint16:
        img = (img // 257).astype(np.uint8)
    elif img.dtype != np.uint8:
        img = np.clip(img, 0, 255).astype(np.uint8)

    if img.ndim == 2:
        return img

    if img.ndim != 3 or img.shape[2] not in (1, 3, 4):
        raise ValueError('Format gambar tidak didukung: %s.' % (img.shape,))

    if img.shape[2] == 1:
        return img[:, :, 0]

    if img.shape[2] == 4:
        alpha = img[:, :, 3:4].astype(np.float32) / 255
        rgb = img[:, :, :3].astype(np.float32)
        img = (rgb * alpha + 255 * (1 - alpha)).astype(np.uint8)

    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def stretch_contrast(img):
    lo, hi = np.percentile(img, [1, 99])
    if hi - lo < 30:
        return img
    return np.clip((img.astype(np.float32) - lo) / (hi - lo) * 255, 0, 255).astype(np.uint8)


def prepare(img):
    img = to_gray(img)
    h, w = img.shape
    s = min(H / h, W / w)
    nh, nw = max(1, int(h * s)), max(1, int(w * s))
    img = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_LINEAR)
    return stretch_contrast(img)


def glcm_features(img):
    q = (img // (256 // LEVELS)).astype(np.uint8)
    glcm = graycomatrix(q, distances=DISTS, angles=ANGLES,
                        levels=LEVELS, symmetric=True, normed=True)
    feat = []
    for p in PROPS:
        feat.extend(graycoprops(glcm, p).flatten())
    return np.nan_to_num(np.array(feat))
