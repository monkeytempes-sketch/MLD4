
import argparse
import io
import json
import os
import time
import logging

import joblib
import numpy as np

from flask import Flask, jsonify, request, send_from_directory
from PIL import Image, ImageOps, UnidentifiedImageError

from glcm_utils import glcm_features, prepare
from db import simpan_riwayat, ambil_riwayat

BASE = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE, 'model')
STATIC_DIR = os.path.join(BASE, 'static')

app = Flask(
    __name__,
    static_folder=STATIC_DIR,
    static_url_path='/static'
)

app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024
Image.MAX_IMAGE_PIXELS = 200_000_000

logging.basicConfig(level=logging.INFO)

try:
    svm = joblib.load(os.path.join(MODEL_DIR, 'svm.joblib'))
    rf = joblib.load(os.path.join(MODEL_DIR, 'rf.joblib'))
    classes = joblib.load(os.path.join(MODEL_DIR, 'classes.joblib'))

    with open(os.path.join(MODEL_DIR, 'info.json'), encoding='utf-8') as f:
        info = json.load(f)

except Exception as e:
    raise RuntimeError(f'Gagal memuat model: {e}') from e

SVM_FEATURES = svm.n_features_in_
RF_FEATURES = rf.n_features_in_

app.logger.info('SVM features: %s', SVM_FEATURES)
app.logger.info('RF features: %s', RF_FEATURES)


def error(message, status=400):
    return jsonify({
        'ok': False,
        'pesan': message
    }), status


def ranked(scores):
    idx = np.argsort(scores)[::-1][:3]

    return [
        {
            'kode': str(classes[i]),
            'nilai': float(scores[i]),
            'contoh': f'/contoh/{classes[i]}.png'
        }
        for i in idx
    ]


def predict_svm(x):
    t0 = time.perf_counter()
    p = svm.predict_proba(x)[0]
    return ranked(p), (time.perf_counter() - t0) * 1000


def predict_rf(x):
    t0 = time.perf_counter()
    p = rf.predict_proba(x)[0]

    return ranked(p), (time.perf_counter() - t0) * 1000


@app.get('/')
def index():
    return send_from_directory(STATIC_DIR, 'index.html')


@app.get('/contoh/<path:name>')
def contoh(name):
    return send_from_directory(
        os.path.join(MODEL_DIR, 'contoh'),
        name
    )


@app.get('/api/info')
def api_info():
    return jsonify(info)


@app.get('/api/riwayat')
def api_riwayat():
    return jsonify(ambil_riwayat())


@app.post('/api/identifikasi')
def identifikasi():
    upload = request.files.get('gambar')

    if upload is None or upload.filename == '':
        return error('Tidak ada gambar yang dikirim.')

    try:
        raw = upload.read()

        if not raw:
            return error('File gambar kosong.')

        img = ImageOps.exif_transpose(
            Image.open(io.BytesIO(raw))
        )

        img.load()
        gray = np.asarray(img.convert('L'))

    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        Image.DecompressionBombError
    ):
        return error(
            'Berkas bukan gambar yang dapat dibaca. Gunakan JPG atau PNG.'
        )

    t0 = time.perf_counter()

    processed = prepare(gray)
    features = np.asarray(
        glcm_features(processed),
        dtype=np.float64
    )

    x = features.reshape(1, -1)
    feature_count = x.shape[1]

    t_glcm = (time.perf_counter() - t0) * 1000

    app.logger.info('GLCM features: %s', feature_count)
    app.logger.info('SVM expected: %s', SVM_FEATURES)
    app.logger.info('RF expected: %s', RF_FEATURES)

    if feature_count != SVM_FEATURES:
        return error(
            f'Fitur GLCM menghasilkan {feature_count} fitur, '
            f'SVM membutuhkan {SVM_FEATURES} fitur. '
            'Periksa konfigurasi training dan ekstraksi GLCM.',
            422
        )

    if feature_count != RF_FEATURES:
        return error(
            f'Fitur GLCM menghasilkan {feature_count} fitur, '
            f'Random Forest membutuhkan {RF_FEATURES} fitur. '
            'Periksa konfigurasi training dan ekstraksi GLCM.',
            422
        )

    svm_top, t_svm = predict_svm(x)
    rf_top, t_rf = predict_rf(x)

    best_svm = svm_top[0]['kode']
    best_rf = rf_top[0]['kode']

    if best_svm == best_rf:
        ringkasan = f'Kedua model sepakat: penulis {best_svm}.'
    else:
        ringkasan = (
            f'Model berbeda pendapat: SVM memilih {best_svm}, '
            f'Random Forest memilih {best_rf}.'
        )

    peringatan = []

    h, w = gray.shape

    if h > w:
        peringatan.append(
            'Gambar berbentuk potret, sedangkan model dilatih '
            'dengan potongan satu baris. Hasil mungkin kurang akurat.'
        )

    if min(h, w) < 30:
        peringatan.append(
            'Gambar sangat kecil. Gunakan gambar dengan resolusi lebih tinggi.'
        )

    lo, hi = np.percentile(gray, [1, 99])

    if hi - lo < 30:
        peringatan.append(
            'Goresan tulisan tidak terlihat jelas karena gambar '
            'hampir seragam. Hasil di bawah tidak bermakna.'
        )

    simpan_riwayat(
        upload.filename,
        best_svm,
        svm_top[0]['nilai'],
        best_rf,
        rf_top[0]['nilai'],
        t_glcm,
        t_svm,
        t_rf
    )

    return jsonify({
        'ok': True,
        'ringkasan': ringkasan,
        'peringatan': peringatan,
        'jumlah_fitur': feature_count,
        'waktu_glcm_ms': t_glcm,
        'svm': {
            'top': svm_top,
            'waktu_ms': t_svm
        },
        'rf': {
            'top': rf_top,
            'waktu_ms': t_rf
        }
    })


@app.errorhandler(413)
def too_large(_):
    return error(
        'Berkas terlalu besar. Batas ukuran 25 MB.',
        413
    )


@app.errorhandler(Exception)
def unexpected(e):
    if hasattr(e, 'code') and isinstance(e.code, int) and e.code < 500:
        return error(
            getattr(e, 'description', 'Permintaan tidak valid.'),
            e.code
        )

    app.logger.exception('Server error: %s', e)

    return error(
        'Terjadi kesalahan di server. Periksa Runtime Logs.',
        500
    )


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--host', default='127.0.0.1')
    ap.add_argument('--port', type=int, default=5000)

    a = ap.parse_args()

    app.run(
        host=a.host,
        port=a.port,
        threaded=True
    )
