from dbt.adapters.duckdb.plugins import BasePlugin
import os

class Plugin(BasePlugin):
    def configure_connection(self, conn):
        # We attach the DuckLake catalog here so it's available during dbt's compilation and execution
        pg_db = os.getenv('POSTGRES_DB', 'elt_lakehouse')
        pg_user = os.getenv('POSTGRES_USER', 'elt_user')
        pg_pass = os.getenv('POSTGRES_PASSWORD', 'elt_password')
        pg_host = os.getenv('POSTGRES_HOST', 'postgres')
        pg_port = os.getenv('POSTGRES_PORT', '5432')
        
        pg_conn = f"dbname={pg_db} user={pg_user} password={pg_pass} host={pg_host} port={pg_port}"
        
        # Load extensions (should already be loaded, but safe to ensure)
        conn.execute("LOAD ducklake")
        conn.execute("LOAD postgres")
        conn.execute("LOAD httpfs")
        conn.execute("LOAD aws")
        
        # Configure MinIO access (in case it wasn't set globally)
        minio_key = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
        minio_secret = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
        conn.execute("SET s3_endpoint='minio:9000'")
        conn.execute(f"SET s3_access_key_id='{minio_key}'")
        conn.execute(f"SET s3_secret_access_key='{minio_secret}'")
        conn.execute("SET s3_use_ssl=false")
        conn.execute("SET s3_region='us-east-1'")
        conn.execute("SET s3_url_style='path'")

        # Attach DuckLake
        attach_sql = f"ATTACH 'ducklake:postgres:{pg_conn}' AS lakehouse (DATA_PATH 's3://lakehouse/ducklake/', METADATA_SCHEMA 'ducklake_catalog')"
        conn.execute(attach_sql)
