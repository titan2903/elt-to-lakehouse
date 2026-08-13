# ELT to Lakehouse — Workspace Rules

Rules ini berlaku untuk SEMUA interaksi agent di workspace ini. Baca sebelum mengerjakan task apapun.

## Referensi Wajib

Dokumen desain utama: `rancangan-project-data-engineering.md` di root repository.
Semua keputusan teknis sudah LOCKED di dokumen tersebut. Jangan menyimpang.

## Fase Workflow

Sebelum menulis kode, SELALU identifikasi fase mana yang sedang dikerjakan:

- **Fase 1 (branch: `fase-1/baseline`)**: Batch ELT → PostgreSQL → dbt-postgres → Metabase
- **Fase 2 (branch: `fase-2/lakehouse`)**: dlt → MinIO → DuckLake/DuckDB → dbt-duckdb → PostgreSQL mart → Metabase
- **Fase 3 (branch: `fase-3/data-quality`)**: + Soda Core + n8n → Telegram

Jangan menulis kode Fase 2 di branch Fase 1. Jangan menambahkan service Fase 3 ke docker-compose base.

## PostgreSQL Schema Map

Satu instance PostgreSQL, 5 schema terpisah:

| Schema | Isi | Dipakai Sejak |
|---|---|---|
| `airflow_meta` | Airflow metadata (connections, DAG runs, task instances) | Fase 1 |
| `raw` | Data mentah dari GitHub API (INSERT oleh ingestion script/dlt) | Fase 1 |
| `staging` | dbt staging models (cleaned, renamed, casted) | Fase 1 |
| `mart` | dbt mart models (star schema: fact + dimension tables) — serving layer untuk Metabase | Fase 1 |
| `ducklake_catalog` | DuckLake catalog metadata (table registry, ACID log) | Fase 2 |

Jangan membuat schema baru selain yang tercantum di atas tanpa mendiskusikan dengan user terlebih dahulu.

## Git Convention

- Branch per fase: `fase-1/baseline`, `fase-2/lakehouse`, `fase-3/data-quality`
- Merge ke `main` hanya setelah fase selesai dan SEMUA test lolos
- Tag release: `v1.0-baseline`, `v2.0-lakehouse`, `v3.0-data-quality`
- Conventional commits wajib:
  - `feat:` fitur baru
  - `fix:` perbaikan bug
  - `docs:` dokumentasi
  - `test:` test baru atau perbaikan test
  - `chore:` maintenance (dependency update, config)

## Dokumentasi Wajib Per Fase

Setiap fase HARUS menghasilkan:

1. **Architecture diagram** di `docs/architecture-v{1,2,3}.md` (format Mermaid)
2. **README section** yang menjelaskan arsitektur, keputusan desain, dan trade-off
3. **Self-evaluation** di `docs/self-evaluation/` — jawab 5 pertanyaan:
   - Keputusan desain paling sulit dan kenapa
   - Penjelasan arsitektur 2 menit tanpa kode
   - Trade-off yang diambil vs alternatif yang tidak dipilih
   - Bug/masalah teknis yang ditemui dan solusinya
   - Apa yang akan dilakukan berbeda jika mengulang

## Konvensi Bahasa

- Dokumentasi (README, docs/, komentar penjelasan): **Bahasa Indonesia**
- Kode (variabel, fungsi, class, SQL alias, dbt model names): **English**
- Commit messages: **English** (conventional commits)

## File yang HARUS masuk `.gitignore`

```
.env
dlt/.dlt/secrets.toml
*.duckdb
*.duckdb.wal
__pycache__/
.pytest_cache/
dbt/target/
dbt/dbt_packages/
dbt/logs/
```
