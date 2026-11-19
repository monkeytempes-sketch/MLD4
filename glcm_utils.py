import cv2
import numpy as np
from skimage.feature import graycomatrix, graycoprops

H, W = 64, 512
LEVELS = 32
DISTS = [1, 3, 5]
ANGLES = [0, np.pi / 4, np.pi / 2, 3 * np.pi / 4]
PROPS = ['dissimilarity', 'correlation', 'homogeneity', 'contrast', 'ASM', 'energy']


def stretch_contrast(img):
    # Menyamakan rentang keabuan agar fitur tidak bergantung pada terang gelapnya foto.
    lo, hi = np.percentile(img, [1, 99])
    if hi - lo < 30:
        return img
    return np.clip((img.astype(np.float32) - lo) / (hi - lo) * 255, 0, 255).astype(np.uint8)


def prepare(img):
    h, w = img.shape
    s = min(H / h, W / w)
    nh, nw = max(1, int(h * s)), max(1, int(w * s))
    img = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_LINEAR)
    canvas = np.full((H, W), 255, np.uint8)
    canvas[:nh, :nw] = stretch_contrast(img)
    return canvas


def glcm_features(img):
    q = (img // (256 // LEVELS)).astype(np.uint8)
    glcm = graycomatrix(q, distances=DISTS, angles=ANGLES,
                        levels=LEVELS, symmetric=True, normed=True)
    feat = []
    for p in PROPS:
        feat.extend(graycoprops(glcm, p).flatten())
    return np.nan_to_num(np.array(feat))
