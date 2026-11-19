# APLIKASI IDENTIFIKASI PENULIS TULISAN TANGAN

Aplikasi web untuk mengidentifikasi penulis berdasarkan karakteristik tulisan tangan menggunakan metode ekstraksi fitur **Gray Level Co-occurrence Matrix (GLCM)** dan algoritma klasifikasi **Support Vector Machine (SVM)** serta **Random Forest**.

Aplikasi dikembangkan menggunakan Python dan Flask. Sistem dapat dijalankan secara lokal pada laptop maupun diakses secara online melalui platform Vercel.

## 🌐 Demo Aplikasi

Aplikasi telah di-deploy menggunakan Vercel dan dapat diakses melalui tautan berikut:

https://mld-4.vercel.app/

Pengguna dapat membuka aplikasi melalui browser untuk mencoba fitur identifikasi penulis tulisan tangan tanpa perlu menjalankan server secara lokal.

## 1. Latar Belakang

Tulisan tangan memiliki karakteristik yang berbeda pada setiap individu. Perbedaan tersebut dapat dimanfaatkan untuk membantu proses identifikasi penulis.

Aplikasi ini dikembangkan untuk mengidentifikasi penulis berdasarkan karakteristik tekstur tulisan tangan melalui ekstraksi fitur GLCM dan proses klasifikasi menggunakan algoritma Machine Learning.

Dua algoritma yang digunakan adalah Support Vector Machine (SVM) dan Random Forest. Hasil dari kedua algoritma ditampilkan agar pengguna dapat membandingkan prediksi yang dihasilkan.

## 2. Tujuan

- Mengembangkan aplikasi identifikasi penulis tulisan tangan berbasis web.
- Menerapkan metode GLCM untuk ekstraksi fitur tekstur citra.
- Mengimplementasikan algoritma SVM dan Random Forest.
- Membandingkan hasil prediksi dari kedua algoritma.
- Menyediakan aplikasi yang dapat diakses secara lokal maupun online.

## 3. Teknologi yang Digunakan

| Teknologi | Kegunaan |
|---|---|
| Python | Bahasa pemrograman utama |
| Flask | Framework aplikasi web |
| OpenCV | Pemrosesan citra |
| NumPy | Pengolahan data numerik |
| Pillow | Membaca dan memproses gambar |
| Scikit-image | Ekstraksi fitur GLCM |
| Scikit-learn | Implementasi Machine Learning |
| Joblib | Penyimpanan dan pemuatan model |
| HTML, CSS, JavaScript | Antarmuka aplikasi |
| Supabase PostgreSQL | Penyimpanan riwayat identifikasi |
| Vercel | Deployment aplikasi online |
| GitHub | Penyimpanan source code |

## 4. Metode yang Digunakan

### A. Gray Level Co-occurrence Matrix (GLCM)

GLCM merupakan metode ekstraksi fitur tekstur citra berdasarkan hubungan intensitas keabuan antar piksel pada jarak dan arah tertentu.

Pada aplikasi ini, GLCM digunakan untuk memperoleh karakteristik tekstur dari gambar tulisan tangan.

Fitur yang digunakan:

- Dissimilarity
- Correlation
- Homogeneity
- Contrast
- ASM (Angular Second Moment)
- Energy

### B. Support Vector Machine (SVM)

SVM merupakan algoritma Machine Learning yang digunakan untuk melakukan klasifikasi dengan mencari batas pemisah terbaik antar kelas.

Pada aplikasi ini, SVM digunakan untuk memprediksi identitas penulis berdasarkan fitur GLCM yang telah diekstraksi.

### C. Random Forest

Random Forest merupakan algoritma klasifikasi berbasis kumpulan decision tree.

Algoritma ini digunakan sebagai metode pembanding terhadap SVM dalam proses identifikasi penulis tulisan tangan.

## 5. Alur Kerja Sistem

1. Pengguna mengunggah gambar tulisan tangan.
2. Sistem membaca dan memproses gambar.
3. Gambar dikonversi menjadi citra grayscale.
4. Sistem melakukan praproses gambar.
5. Sistem mengekstraksi fitur tekstur menggunakan GLCM.
6. Fitur GLCM dimasukkan ke model SVM dan Random Forest.
7. Kedua model menghasilkan prediksi penulis.
8. Sistem menampilkan tiga prediksi teratas dari masing-masing algoritma.
9. Hasil identifikasi disimpan sebagai riwayat apabila database telah dikonfigurasi.

## 6. Fitur Aplikasi

- Upload gambar tulisan tangan.
- Pengambilan gambar menggunakan kamera yang didukung browser.
- Praproses citra tulisan tangan.
- Ekstraksi fitur tekstur menggunakan GLCM.
- Identifikasi menggunakan algoritma SVM.
- Identifikasi menggunakan algoritma Random Forest.
- Menampilkan tiga hasil prediksi teratas.
- Menampilkan waktu proses identifikasi.
- Menampilkan informasi model.
- Menyimpan riwayat identifikasi menggunakan Supabase PostgreSQL.

## 7. Instalasi dan Penggunaan Lokal

Aplikasi diuji menggunakan Python 3.12. Gunakan Python 3.9 atau lebih baru.

### A. Persiapan

Pastikan Python sudah terinstal pada komputer.

Clone repository:

```bash
git clone URL_REPOSITORY_GITHUB
```

Masuk ke folder project:

```bash
cd MLD4
```

### B. Instalasi Pustaka

Jalankan perintah:

```bash
pip install -r requirements.txt
```

Jika perintah pip tidak dikenali:

```bash
python -m pip install -r requirements.txt
```

### C. Training Model

Training dilakukan menggunakan dataset tulisan tangan.

Contoh menggunakan dataset ZIP:

```bash
python train.py --data "C:\lokasi\MLD-20261108T011542Z-1-001.zip"
```

Folder dataset yang sudah diekstrak juga dapat digunakan:

```bash
python train.py --data MLD
```

Proses training menghasilkan model yang digunakan oleh aplikasi untuk melakukan identifikasi.

### D. Menjalankan Aplikasi

Jalankan:

```bash
python app.py
```

Buka browser dan akses:

```text
http://127.0.0.1:5000
```

Tekan `Ctrl + C` pada terminal untuk menghentikan aplikasi.

### E. Opsi Tambahan

Menggunakan port berbeda:

```bash
python app.py --port 5050
```

Mengakses aplikasi dari HP melalui jaringan Wi-Fi yang sama:

```bash
python app.py --host 0.0.0.0
```

Kemudian buka:

```text
http://ALAMAT-IP-LAPTOP:5000
```

## 8. Deployment ke Vercel

Aplikasi juga dapat dijalankan secara online menggunakan Vercel.

Tahapan deployment:

1. Source code project diunggah ke GitHub.
2. Repository GitHub dihubungkan dengan Vercel.
3. Repository project di-import ke Vercel.
4. File konfigurasi deployment disiapkan.
5. Environment variable database ditambahkan.
6. Project di-deploy melalui Vercel.
7. Aplikasi dapat diakses menggunakan URL deployment.

### File Konfigurasi Deployment

Beberapa file yang digunakan:

- `vercel.json` untuk konfigurasi deployment.
- `.python-version` untuk menentukan versi Python.
- `requirements.txt` untuk daftar pustaka Python.
- `app.py` sebagai aplikasi Flask.

## 9. Database Supabase

Supabase PostgreSQL digunakan untuk menyimpan data riwayat identifikasi.

Koneksi database menggunakan environment variable:

```text
DATABASE_URL
```

Konfigurasi dilakukan melalui bagian Environment Variables pada dashboard Vercel.

Dengan konfigurasi tersebut, aplikasi dapat terhubung ke database untuk menyimpan dan mengambil riwayat identifikasi.

## 10. Struktur Folder Project

```text
MLD4/
│
├── app.py
├── train.py
├── glcm_utils.py
├── db.py
├── requirements.txt
├── vercel.json
├── .python-version
├── README.md
│
├── model/
│   ├── svm.joblib
│   ├── rf.joblib
│   ├── classes.joblib
│   ├── info.json
│   └── contoh/
│
└── static/
    ├── index.html
    ├── app.js
    └── style.css
```

## 11. Keterangan File

| File atau Folder | Fungsi |
|---|---|
| `app.py` | Server Flask, endpoint API, dan proses prediksi |
| `train.py` | Proses training model |
| `glcm_utils.py` | Praproses gambar dan ekstraksi fitur GLCM |
| `db.py` | Koneksi dan pengelolaan riwayat database |
| `requirements.txt` | Daftar dependensi Python |
| `vercel.json` | Konfigurasi deployment Vercel |
| `.python-version` | Versi Python yang digunakan |
| `model/` | Menyimpan model hasil training |
| `static/` | Menyimpan HTML, CSS, dan JavaScript |

## 12. Catatan

- Training model dilakukan sebelum aplikasi dijalankan.
- File model hasil training harus tersedia di folder `model/`.
- Dataset tidak perlu diunggah ke Vercel apabila model sudah dilatih dan file model tersedia.
- Penggunaan lokal dapat dilakukan tanpa internet apabila seluruh pustaka dan file model sudah tersedia.
- Penggunaan online membutuhkan koneksi internet.
- Penyimpanan riwayat online membutuhkan konfigurasi database Supabase yang benar.
- Kamera browser dapat memiliki persyaratan keamanan koneksi, sehingga penggunaan kamera pada deployment online sebaiknya melalui HTTPS.

## 13. Pengembang

**Project:** Aplikasi Identifikasi Penulis Tulisan Tangan

**Metode:** GLCM, Support Vector Machine (SVM), dan Random Forest

**Platform:** Python, Flask, Supabase, dan Vercel

**Demo:** https://mld-4.vercel.app/
