# Evaluasi Diri Fase 3: Data Quality, Monitoring & Alerting

## 1. Apa keputusan desain yang paling sulit di fase ini, dan kenapa?
Memisahkan logika *alerting* dari Airflow ke n8n. Secara insting, menulis *hook* Telegram langsung di Airflow `callbacks.py` menggunakan pustaka `python-telegram-bot` atau `requests` mungkin terasa lebih cepat. Namun, hal ini akan membuat DAG Airflow semakin gemuk (membengkak karena urusan integrasi notifikasi) dan sulit di-*maintenance*. Keputusan membuang tugas *routing* dan *formatting* pesan ke n8n diambil untuk menerapkan konsep *Separation of Concerns* (SoC), di mana Airflow hanya fokus pada "deteksi" sedangkan n8n fokus pada "reaksi/distribusi". Tantangannya adalah perlunya menyiapkan satu tambahan container n8n dan memastikan jaringan *webhook* berjalan lancar.

## 2. Kalau harus jelaskan arsitektur ini ke orang lain dalam 2 menit tanpa membuka kode, apa yang akan disampaikan?
"Kita punya pipeline ELT yang sudah berjalan. Di Fase 3 ini, kita tambahkan dua 'satpam'. Satpam pertama adalah **Soda Core**; dia mencegat data di awal (MinIO) dan di akhir (PostgreSQL) untuk memastikan isinya tidak kosong dan sesuai ekspektasi kualitas kita, sebelum data dibaca oleh *dashboard*. Satpam kedua adalah **n8n**; jika Soda Core menemukan masalah atau jika Airflow gagal, n8n bertugas menerima laporan (lewat webhook) lalu meneruskan peringatan tersebut secara otomatis ke chat Telegram kita. Airflow fokus menjalankan tugas, n8n fokus menyebarkan berita."

## 3. Trade-off apa yang disadari sudah diambil, dan alternatif apa yang tidak dipilih?
- **Soda Core vs Great Expectations (GX):** Kita memilih Soda Core karena pendekatannya berbasis YAML yang sangat ringan dan mudah dimengerti. Kita tidak menggunakan Great Expectations karena GX mengharuskan *scaffolding* direktori yang berat, *boilerplate code* Python yang lumayan panjang, dan terkadang *overkill* untuk proyek portofolio skala ini. Trade-off: komunitas GX lebih besar, namun Soda lebih ramah pengembang untuk integrasi cepat.
- **n8n vs Airflow Telegram Operator:** Kita menggunakan n8n via webhook alih-alih pustaka spesifik Airflow Telegram. Trade-off-nya adalah penambahan memori/CPU untuk menjalankan *container* n8n, tapi keuntungan jangka panjangnya adalah perubahan isi pesan dan platform *alert* (ke Slack/Email) bisa dilakukan tanpa *deploy* ulang Airflow.

## 4. Bug atau masalah teknis apa yang ditemui selama pengerjaan, dan bagaimana penyelesaiannya?
1. **Konflik DuckDB di Soda Core**: Sempat terjadi masalah ketika `soda_check_raw` memanggil DuckDB karena *dialect* PostgreSQL yang bentrok saat membaca ekstensi DuckLake. Diselesaikan dengan membuat koneksi `TYPE POSTGRES` standar untuk mengelabui katalog secara in-memory.
2. **Environment Variables n8n**: *Environment variable* seperti `TELEGRAM_CHAT_ID` tidak mau terekspos di UI (frontend) n8n demi keamanan (menghasilkan *undefined*). Hal ini diselesaikan dengan menyuntikkan `VUE_APP_TELEGRAM_CHAT_ID` agar *frontend* n8n tetap menampilkannya, sehingga *workflow* n8n mudah dites secara lokal.

## 5. Jika mengulang fase ini dari awal, apa yang akan dilakukan berbeda?
Saya mungkin akan langsung menyiapkan environment terpisah (contoh: dev, prod) di n8n menggunakan fitur *Environments* miliknya sejak awal, agar testing *webhook* tidak tercampur dengan *trigger* produksi. Saya juga akan mempertimbangkan penambahan log notifikasi (seperti menuliskannya juga ke sebuah tabel audit) menggunakan *branching* tambahan di n8n untuk pelaporan kualiti data bulanan.
