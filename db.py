
import os
import psycopg

DATABASE_URL = os.environ.get('DATABASE_URL')


def get_connection():
    if not DATABASE_URL:
        raise RuntimeError('DATABASE_URL belum dikonfigurasi.')

    return psycopg.connect(
        DATABASE_URL,
        connect_timeout=10,
        sslmode='require',
        prepare_threshold=None
    )


def simpan_riwayat(
    nama_file,
    hasil_svm,
    skor_svm,
    hasil_rf,
    skor_rf,
    ms_glcm,
    ms_svm,
    ms_rf
):
    if not DATABASE_URL:
        print('DATABASE_URL belum dikonfigurasi.')
        return False

    data = (
        nama_file,
        hasil_svm,
        skor_svm,
        hasil_rf,
        skor_rf,
        ms_glcm,
        ms_svm,
        ms_rf
    )

    try:
        with get_connection() as conn:
            conn.execute(
                '''
                INSERT INTO riwayat (
                    nama_file,
                    hasil_svm,
                    skor_svm,
                    hasil_rf,
                    skor_rf,
                    waktu_ekstraksi_ms,
                    waktu_svm_ms,
                    waktu_rf_ms
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ''',
                data
            )

        return True

    except Exception as e:
        print('Gagal menyimpan riwayat:', str(e))
        return False


def ambil_riwayat(limit=20):
    if not DATABASE_URL:
        return []

    limit = max(1, min(int(limit), 100))

    try:
        with get_connection() as conn:
            rows = conn.execute(
                '''
                SELECT
                    waktu,
                    nama_file,
                    hasil_svm,
                    skor_svm,
                    hasil_rf,
                    skor_rf,
                    waktu_ekstraksi_ms,
                    waktu_svm_ms,
                    waktu_rf_ms
                FROM riwayat
                ORDER BY id DESC
                LIMIT %s
                ''',
                (limit,)
            ).fetchall()

        return [
            {
                'waktu': r[0].isoformat(),
                'nama_file': r[1],
                'hasil_svm': r[2],
                'skor_svm': float(r[3]),
                'hasil_rf': r[4],
                'skor_rf': float(r[5]),
                'waktu_glcm_ms': float(r[6]),
                'waktu_svm_ms': float(r[7]),
                'waktu_rf_ms': float(r[8])
            }
            for r in rows
        ]

    except Exception as e:
        print('Gagal membaca riwayat:', str(e))
        return []
