import os
import psycopg

url = os.environ["DATABASE_URL"]
with psycopg.connect(url, connect_timeout=10) as conn:
    print("Terhubung:", conn.execute("select version()").fetchone()[0])
    conn.execute(
        "insert into riwayat (nama_file, hasil_svm, hasil_rf) values (%s, %s, %s)",
        ("tes.jpg", "D230212", "D230212"),
    )
    print("Jumlah baris riwayat:", conn.execute("select count(*) from riwayat").fetchone()[0])
