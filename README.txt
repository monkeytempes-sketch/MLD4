APLIKASI IDENTIFIKASI PENULIS TULISAN TANGAN
Aplikasi web yang berjalan di laptop sendiri, tanpa internet.
Diuji di Python 3.12. Gunakan Python 3.9 atau lebih baru.

1. Instal pustaka (sekali saja)
   pip install -r requirements.txt
   Jika perintah pip tidak dikenali: python -m pip install -r requirements.txt

2. Latih model dari dataset (sekali saja, sekitar 1 menit)
   python train.py --data "C:\lokasi\MLD-20261108T011542Z-1-001.zip"
   Folder MLD yang sudah diekstrak juga bisa dipakai: python train.py --data MLD
   Tabel 5 eksperimen (Precision, Recall, Akurasi, F1, waktu pelatihan) dan
   waktu ekstraksi GLCM tercetak di layar. Salin untuk bab hasil di paper.

3. Jalankan aplikasi
   python app.py
   Buka http://127.0.0.1:5000 di browser. Tekan Ctrl+C di terminal untuk berhenti.

Opsi
   Port 5000 terpakai:          python app.py --port 5050
   Dibuka dari HP (Wi-Fi sama): python app.py --host 0.0.0.0
                                lalu buka http://ALAMAT-IP-LAPTOP:5000 di HP.
                                Tombol kamera tidak berfungsi lewat alamat ini,
                                gunakan Pilih berkas.

Berkas
   train.py        membaca dataset, mengekstrak GLCM, menjalankan eksperimen, menyimpan model
   app.py          server web (Flask) dan fungsi prediksi
   glcm_utils.py   praproses gambar dan fitur GLCM, dipakai bersama oleh train.py dan app.py
   static/         halaman web (HTML, CSS, JavaScript)
   model/          dibuat oleh train.py
