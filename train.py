import argparse
import json
import os
import re
import tempfile
import time
import zipfile

import cv2
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.svm import SVC

from glcm_utils import glcm_features, prepare

# 'orignal' adalah typo yang memang ada di nama file dataset.
BAD_NAME = re.compile(r'orig|orign|camscanner', re.I)
IMAGE_EXT = ('.jpg', '.jpeg', '.png')


def read_gray(path):
    # imdecode agar path dengan karakter non-ASCII tetap terbaca di Windows.
    return cv2.imdecode(np.fromfile(path, np.uint8), cv2.IMREAD_GRAYSCALE)


def resolve_data_dir(path):
    if path.lower().endswith('.zip'):
        tmp = tempfile.mkdtemp(prefix='mld_')
        print('Mengekstrak', path)
        zipfile.ZipFile(path).extractall(tmp)
        path = tmp
    # Zip dari Google Drive berisi satu folder induk (MLD), turun satu tingkat.
    names = [n for n in os.listdir(path) if not n.startswith(('.', '__'))]
    dirs = [n for n in names if os.path.isdir(os.path.join(path, n))]
    if len(dirs) == 1 and len(names) == 1:
        path = os.path.join(path, dirs[0])
    return path


def load_dataset(root):
    imgs, labels, paths = [], [], []
    for writer in sorted(os.listdir(root)):
        folder = os.path.join(root, writer)
        if not os.path.isdir(folder):
            continue
        for f in sorted(os.listdir(folder)):
            if not f.lower().endswith(IMAGE_EXT) or BAD_NAME.search(f):
                continue
            g = read_gray(os.path.join(folder, f))
            if g is None or g.shape[0] > g.shape[1]:
                continue
            imgs.append(prepare(g))
            labels.append(writer)
            paths.append(os.path.join(folder, f))
    return imgs, labels, paths


def cleanest_example(class_paths):
    # Pilih contoh yang paling sedikit memuat sisa baris lain di tepi atas dan bawah.
    best, best_edge = None, 9.0
    for p in class_paths[:12]:
        g = read_gray(p)
        if g is None or g.shape[0] > g.shape[1]:
            continue
        dark = g < np.median(g) - 50
        k = max(1, int(g.shape[0] * 0.08))
        edge = dark[:k].mean() + dark[-k:].mean()
        if edge < best_edge:
            best, best_edge = g, edge
    return best


def score(yt, yp):
    return {'Precision': precision_score(yt, yp, average='macro', zero_division=0),
            'Recall': recall_score(yt, yp, average='macro', zero_division=0),
            'Akurasi': accuracy_score(yt, yp),
            'F1-Score': f1_score(yt, yp, average='macro', zero_division=0)}


def show(name, rows):
    t = pd.DataFrame(rows, index=range(1, len(rows) + 1))
    t.index.name = 'Eksperimen ke'
    t.loc['Rata-Rata'] = t.mean()
    print(f'\n{name}')
    print(t.round(4).to_string())
    return t.loc['Rata-Rata', 'Akurasi']


def main(data, runs, out):
    root = resolve_data_dir(data)
    imgs, labels, paths = load_dataset(root)
    le = LabelEncoder()
    y = le.fit_transform(labels)
    print(f'{len(y)} gambar, {len(le.classes_)} kelas')

    t0 = time.perf_counter()
    X = np.array([glcm_features(im) for im in imgs])
    t_glcm = time.perf_counter() - t0
    print(f'Waktu ekstraksi GLCM: {t_glcm:.2f} detik ({t_glcm / len(y) * 1000:.2f} ms/gambar)')

    rows = {'SVM': [], 'Random Forest': []}
    for seed in range(1, runs + 1):
        tr, te = train_test_split(np.arange(len(y)), test_size=0.2, stratify=y, random_state=seed)
        models = {'SVM': make_pipeline(StandardScaler(), SVC(kernel='rbf', C=10)),
                  'Random Forest': RandomForestClassifier(n_estimators=200, random_state=seed)}
        for name, model in models.items():
            t0 = time.perf_counter()
            model.fit(X[tr], y[tr])
            t_fit = time.perf_counter() - t0
            rows[name].append({**score(y[te], model.predict(X[te])), 'Waktu Pelatihan (detik)': t_fit})
    acc = {name: show(name, r) for name, r in rows.items()}

    # Model untuk aplikasi dilatih di seluruh data.
    svm = make_pipeline(StandardScaler(), SVC(kernel='rbf', C=10)).fit(X, y)
    rf = RandomForestClassifier(n_estimators=200, random_state=0, n_jobs=-1).fit(X, y)
    classes = [str(c) for c in le.classes_]

    os.makedirs(os.path.join(out, 'contoh'), exist_ok=True)
    joblib.dump(svm, os.path.join(out, 'svm.joblib'))
    joblib.dump(rf, os.path.join(out, 'rf.joblib'), compress=3)
    joblib.dump(classes, os.path.join(out, 'classes.joblib'))
    for cls in classes:
        g = cleanest_example([p for p, l in zip(paths, labels) if l == cls])
        w = max(1, round(g.shape[1] * 96 / g.shape[0]))
        ok, buf = cv2.imencode('.png', cv2.resize(g, (w, 96), interpolation=cv2.INTER_AREA))
        buf.tofile(os.path.join(out, 'contoh', f'{cls}.png'))
    with open(os.path.join(out, 'info.json'), 'w', encoding='utf-8') as f:
        json.dump({'jumlah_gambar': len(y), 'jumlah_penulis': len(classes), 'eksperimen': runs,
                   'akurasi_svm': acc['SVM'], 'akurasi_rf': acc['Random Forest']}, f)
    print(f'\nModel tersimpan di {out}/. Jalankan: python app.py')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', default='MLD', help='folder MLD atau berkas zip MLD')
    ap.add_argument('--runs', type=int, default=5)
    ap.add_argument('--out', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'model'))
    a = ap.parse_args()
    main(a.data, a.runs, a.out)
