import argparse
import io
import json
import os
import sys
import time

import joblib
import numpy as np
from flask import Flask, jsonify, request, send_from_directory
from PIL import Image, ImageOps, UnidentifiedImageError

from glcm_utils import glcm_features, prepare

BASE = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE, 'model')

app = Flask(__name__, static_folder=os.path.join(BASE, 'static'), static_url_path='/static')
app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024
Image.MAX_IMAGE_PIXELS = 200_000_000

try:
    svm = joblib.load(os.path.join(MODEL_DIR, 'svm.joblib'))
    rf = joblib.load(os.path.join(MODEL_DIR, 'rf.joblib'))
    classes = joblib.load(os.path.join(MODEL_DIR, 'classes.joblib'))
    with open(os.path.join(MODEL_DIR, 'info.json'), encoding='utf-8') as f:
        info = json.load(f)
except FileNotFoundError:
    sys.exit('Model belum ada. Jalankan dulu: python train.py --data MLD')


def ranked(scores):
    idx = np.argsort(scores)[::-1][:3]
    return [{'kode': classes[i], 'nilai': float(scores[i]), 'contoh': f'/contoh/{classes[i]}.png'} for i in idx]


def predict_svm(x):
    t0 = time.perf_counter()
    d = svm.decision_function(x)[0]
    # Bagian bulat skor adalah jumlah duel satu lawan satu yang dimenangkan tiap kelas.
    share = np.clip(np.round(d), 0, None) / (len(classes) - 1)
    order = np.argsort(d)[::-1][:3]
    top = [{'kode': classes[i], 'nilai': float(share[i]), 'contoh': f'/contoh/{classes[i]}.png'} for i in order]
    return top, (time.perf_counter() - t0) * 1000


def predict_rf(x):
    t0 = time.perf_counter()
    p = rf.predict_proba(x)[0]
    return ranked(p), (time.perf_counter() - t0) * 1000


def error(message, status=400):
    return jsonify({'ok': False, 'pesan': message}), status


@app.get('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')


@app.get('/contoh/<path:name>')
def contoh(name):
    return send_from_directory(os.path.join(MODEL_DIR, 'contoh'), name)


@app.get('/api/info')
def api_info():
    return jsonify(info)


@app.post('/api/identifikasi')
def identifikasi():
    upload = request.files.get('gambar')
    if upload is None or upload.filename == '':
        return error('Tidak ada gambar yang dikirim.')
    try:
        img = ImageOps.exif_transpose(Image.open(io.BytesIO(upload.read())))
        gray = np.asarray(img.convert('L'))
    except (UnidentifiedImageError, OSError, ValueError):
        return error('Berkas bukan gambar yang dapat dibaca. Gunakan JPG atau PNG.')

    t0 = time.perf_counter()
    x = glcm_features(prepare(gray)).reshape(1, -1)
    t_glcm = (time.perf_counter() - t0) * 1000
    svm_top, t_svm = predict_svm(x)
    rf_top, t_rf = predict_rf(x)

    best_svm, best_rf = svm_top[0]['kode'], rf_top[0]['kode']
    if best_svm == best_rf:
        ringkasan = f'Kedua model sepakat: penulis {best_svm}.'
    else:
        ringkasan = f'Model berbeda pendapat: SVM memilih {best_svm}, Random Forest memilih {best_rf}.'

    peringatan = []
    h, w = gray.shape
    if h > w:
        peringatan.append('Gambar berbentuk potret, sedangkan model dilatih dengan potongan satu baris. Hasil mungkin kurang akurat.')
    if min(h, w) < 30:
        peringatan.append('Gambar sangat kecil. Gunakan gambar dengan resolusi lebih tinggi.')
    lo, hi = np.percentile(gray, [1, 99])
    if hi - lo < 30:
        peringatan.append('Goresan tulisan tidak terlihat jelas karena gambar hampir seragam. Hasil di bawah tidak bermakna.')

    return jsonify({'ok': True, 'ringkasan': ringkasan, 'peringatan': peringatan, 'waktu_glcm_ms': t_glcm,
                    'svm': {'top': svm_top, 'waktu_ms': t_svm}, 'rf': {'top': rf_top, 'waktu_ms': t_rf}})


@app.errorhandler(413)
def too_large(_):
    return error('Berkas terlalu besar. Batas ukuran 25 MB.', 413)


@app.errorhandler(Exception)
def unexpected(e):
    if hasattr(e, 'code') and isinstance(e.code, int) and e.code < 500:
        return error(getattr(e, 'description', 'Permintaan tidak valid.'), e.code)
    app.logger.exception(e)
    return error('Terjadi kesalahan di server. Coba gambar lain.', 500)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--host', default='127.0.0.1', help='gunakan 0.0.0.0 agar bisa dibuka dari perangkat lain di jaringan yang sama')
    ap.add_argument('--port', type=int, default=5000)
    a = ap.parse_args()
    print(f'Buka http://{"127.0.0.1" if a.host == "0.0.0.0" else a.host}:{a.port} di browser. Tekan Ctrl+C untuk berhenti.')
    app.run(host=a.host, port=a.port, threaded=True)
