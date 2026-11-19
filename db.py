import os
import threading

import psycopg

DATABASE_URL = os.environ.get('DATABASE_URL')


def _simpan(data):
    try:
        with psycopg.connect(DATABASE_URL, connect_timeout=5) as conn:
            conn.execute(
                'insert into riwayat '
                '(nama_file, hasil_svm, skor_svm, hasil_rf, skor_rf, '
                ' waktu_ekstraksi_ms, waktu_svm_ms, waktu_rf_ms) '
                'values (%s, %s, %s, %s, %s, %s, %s, %s)',
                data,
            )
    except Exception as e:
        print('Gagal menyimpan riwayat:', e)


def simpan_riwayat(nama_file, hasil_svm, skor_svm, hasil_rf, skor_rf,
                   ms_glcm, ms_svm, ms_rf):
    """Simpan di thread terpisah supaya respons ke pengguna tidak tertahan."""
    if not DATABASE_URL:
        return
    data = (nama_file, hasil_svm, skor_svm, hasil_rf, skor_rf, ms_glcm, ms_svm, ms_rf)
    threading.Thread(target=_simpan, args=(data,), daemon=True).start()


def ambil_riwayat(limit=20):
    if not DATABASE_URL:
        return []
    try:
        with psycopg.connect(DATABASE_URL, connect_timeout=5) as conn:
            rows = conn.execute(
                'select waktu, nama_file, hasil_svm, skor_svm, hasil_rf, skor_rf, '
                '       waktu_ekstraksi_ms, waktu_svm_ms, waktu_rf_ms '
                'from riwayat order by id desc limit %s',
                (limit,),
            ).fetchall()
        return [
            {
                'waktu': r[0].isoformat(),
                'nama_file': r[1],
                'hasil_svm': r[2], 'skor_svm': r[3],
                'hasil_rf': r[4], 'skor_rf': r[5],
                'waktu_glcm_ms': r[6], 'waktu_svm_ms': r[7], 'waktu_rf_ms': r[8],
            }
            for r in rows
        ]
    except Exception as e:
        print('Gagal membaca riwayat:', e)
        return []