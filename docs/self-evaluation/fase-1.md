# Self-Evaluation: Fase 1 (Batch ELT Baseline)

**1. Apa keputusan desain yang paling sulit di fase ini, dan kenapa?**
Keputusan untuk tidak menggunakan dlt sejak awal dan membuat script Python custom untuk ekstraksi data GitHub. Hal ini ditujukan untuk menunjukkan pemahaman nyata tentang apa yang diabstraksikan oleh tools modern seperti dlt (misalnya: *pagination*, *exponential backoff*, dan *incremental loading*).

**2. Kalau harus jelaskan arsitektur ini ke orang lain dalam 2 menit tanpa membuka kode, apa yang akan disampaikan?**
Pipeline ini mengekstrak data JSON Pull Requests dan Issues dari GitHub API menggunakan Python script yang dijalankan oleh Airflow. Data tersebut kemudian disimpan secara mentah (*raw*) ke dalam database PostgreSQL. Selanjutnya, tool bernama dbt mengubah JSON mentah tersebut menjadi bentuk Star Schema (fakta dan dimensi) agar siap divisualisasikan oleh Metabase.

**3. Trade-off apa yang disadari sudah diambil, dan alternatif apa yang tidak dipilih?**
Menggunakan `LocalExecutor` di Airflow dan menjalankan semuanya dalam satu mesin menggunakan Docker Compose, ketimbang menggunakan Kubernetes atau cloud services. Ini adalah trade-off agar portfolio mudah dijalankan oleh reviewer di lokal mesin mereka (portabilitas diutamakan daripada skalabilitas masif).

**4. Bug atau masalah teknis apa yang ditemui selama pengerjaan, dan bagaimana penyelesaiannya?**
Integrasi `dbt-postgres` dengan Airflow BashOperator. Terkadang path `.dbt` default menyebabkan Airflow tidak mengenali direktori profiles. Penyelesaiannya adalah dengan selalu melakukan mount folder `dbt/` ke dalam container dan mengeksekusi `dbt run --profiles-dir .` di dalam folder tersebut.

**5. Jika mengulang fase ini dari awal, apa yang akan dilakukan berbeda?**
Mungkin membuat skrip *schema auto-detection* sederhana di Python, meski pada akhirnya akan lebih mudah dan terstruktur saat dimigrasi menggunakan `dlt` di Fase 2.
