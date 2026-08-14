from soda.scan import Scan
import duckdb
import os
import logging

def run_soda_duckdb(check_file: str, data_source: str = "duckdb"):
    scan = Scan()
    scan.set_data_source_name(data_source)
    
    # Configure duckdb
    con = duckdb.connect(database=":memory:")
    con.execute("INSTALL httpfs;")
    con.execute("LOAD httpfs;")
    con.execute("INSTALL aws;")
    con.execute("LOAD aws;")
    con.execute("INSTALL postgres;")
    con.execute("LOAD postgres;")
    
    # Attach PostgreSQL catalog
    pg_conn = f"dbname={os.getenv('POSTGRES_DB')} user={os.getenv('POSTGRES_USER')} password={os.getenv('POSTGRES_PASSWORD')} host={os.getenv('POSTGRES_HOST')} port=5432"
    
    s3_key = os.getenv('MINIO_ACCESS_KEY')
    s3_secret = os.getenv('MINIO_SECRET_KEY')
    
    con.execute(f"""
        CREATE SECRET (
            TYPE S3,
            KEY_ID '{s3_key}',
            SECRET '{s3_secret}',
            REGION 'us-east-1',
            ENDPOINT 'minio:9000',
            URL_STYLE 'path',
            USE_SSL false
        );
    """)
    # We do not use TYPE DUCKLAKE, DuckLake is just a concept name.
    # Postgres is already attached or we use it for duckdb catalog if any?
    # In profiles.yml, it attaches pg as TYPE POSTGRES
    con.execute(f"ATTACH '{pg_conn}' AS pg (TYPE POSTGRES);")
    
    # Create views over the MinIO parquet files so Soda can check them
    con.execute("CREATE VIEW pull_requests AS SELECT * FROM read_parquet('s3://lakehouse/raw/github_data/pull_requests/*.parquet');")
    # For issues, handle the case where it might be empty
    try:
        con.execute("CREATE VIEW issues AS SELECT * FROM read_parquet('s3://lakehouse/raw/github_data/issues/*.parquet');")
    except Exception:
        # If no issues data exists yet, create empty view with same schema or just let it fail later
        pass
    
    scan.add_duckdb_connection(con, data_source_name=data_source)
    scan.add_sodacl_yaml_file(check_file)
    scan.execute()
    con.close()
    
    if scan.has_error_logs():
        raise Exception(f"Soda Scan has error logs: {scan.get_error_logs_text()}")
    
    if scan.has_check_fails():
        raise Exception(f"Soda checks failed: {scan.get_checks_fail_text()}")
    
    logging.info("Soda DuckDB scan successful")
    return scan.get_checks_fail_text()

def run_soda_postgres(check_file: str, data_source: str = "postgres_mart"):
    scan = Scan()
    scan.set_data_source_name(data_source)
    scan.add_configuration_yaml_file("/opt/airflow/data_quality/configuration.yml")
    scan.add_sodacl_yaml_file(check_file)
    scan.execute()
    
    if scan.has_error_logs():
        raise Exception(f"Soda Scan has error logs: {scan.get_error_logs_text()}")
    
    if scan.has_check_fails():
        raise Exception(f"Soda checks failed: {scan.get_checks_fail_text()}")
    
    logging.info("Soda Postgres scan successful")
    return scan.get_checks_fail_text()
