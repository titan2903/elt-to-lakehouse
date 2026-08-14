# Self Evaluation: Fase 2 - Lakehouse Migration

**1. Keputusan desain paling sulit dan kenapa**
Memutuskan cara menghubungkan hasil akhir dbt (DuckDB in-memory) ke PostgreSQL serving layer. Keputusannya menggunakan fitur `ATTACH` dari DuckDB POSTGRES extension. Kesulitannya adalah mengonfigurasi dbt-duckdb `profiles.yml` dengan benar (menggunakan `alias` daripada `id`) agar adapter mengetahui ke mana harus mematerialisasi `mart` schema, serta mengelola perbedaan tipe data antara file Parquet dan tabel Postgres yang ada.

**2. Penjelasan arsitektur 2 menit tanpa kode**
Sistem mengambil data mentah dari GitHub setiap hari dan menyimpannya ke dalam storage MinIO dalam bentuk file Parquet yang sangat efisien, bukan langsung ke database. Kemudian, DuckDB, sebuah engine analisis super cepat yang berjalan in-memory, membaca file-file ini dari MinIO. Di dalam DuckDB, dbt membersihkan, menggabungkan, dan merapikan data tersebut. Setelah bersih, DuckDB mengirim data jadinya langsung ke PostgreSQL, yang kini hanya berfungsi sebagai "etalase" (serving layer) yang ringan, cepat, dan siap disambungkan ke dashboard Metabase untuk diakses oleh user.

**3. Trade-off yang diambil vs alternatif yang tidak dipilih**
Kami memilih menggunakan dbt-duckdb untuk komputasi dan membiarkan Postgres sebagai serving layer (melalui koneksi `ATTACH`). Alternatifnya adalah memuat data parquet dari MinIO langsung ke Postgres (misalnya dengan ekstensi Postgres tertentu atau Airflow Python) dan menggunakan dbt-postgres seperti di Fase 1. Kami menolak alternatif ini karena DuckDB jauh lebih cepat dalam memproses analytical workload dari file Parquet di S3 (MinIO) dibanding membebani Postgres untuk meng-ingest file Parquet. Trade-off-nya adalah penambahan kompleksitas pada Airflow/dbt container yang membutuhkan instalasi library ekstra untuk DuckDB dan AWS/httpfs extensions, serta konfigurasi plugin DuckDB.

**4. Bug/masalah teknis yang ditemui dan solusinya**
- **MinIO Container Panics**: Versi MinIO lama (RELEASE.2023-...) mengalami panic saat mounting Docker volumes. Solusinya: menggunakan image `minio/minio:latest`.
- **dbt-duckdb ATTACH Config**: Terjadi error dbt yang tidak bisa mengenali relasi karena konfigurasi `attach` di `profiles.yml` awalnya menggunakan `id: pg`. Solusinya: mengganti menjadi `alias: pg`.
- **Perubahan Struktur DLT**: Skema yang dihasilkan dlt dari file JSON mengubah nama field (misal dari `user.id` menjadi `user__id`) dan mengekstrak nested list (labels) ke dalam tabel terpisah (`issues__labels`). Solusinya: Mengupdate dbt source declarations (`schema.yml`) dan memodifikasi model `stg_users.sql` dan `dim_labels.sql` untuk menyesuaikan dengan struktur Parquet baru yang dihasilkan dlt.

**5. Apa yang akan dilakukan berbeda jika mengulang**
Jika mengulang, saya akan memastikan schema dan sample data dari dlt (di Lakehouse) diperiksa secara manual terlebih dahulu menggunakan DuckDB CLI sebelum langsung menulis model dbt, agar transisi model staging dari format JSON di Postgres ke format flat Parquet dari dlt dapat direncanakan lebih mulus tanpa perlu debug berulang di Airflow logs.
