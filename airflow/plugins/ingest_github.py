import os
import json
import time
import logging
import psycopg2
import requests

logger = logging.getLogger(__name__)

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "postgres"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "elt_lakehouse"),
        user=os.getenv("POSTGRES_USER", "elt_user"),
        password=os.getenv("POSTGRES_PASSWORD", "elt_password")
    )

def create_raw_tables_if_not_exist(cursor):
    """Create raw tables if they don't exist yet."""
    # Pull requests table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS raw.pull_requests (
            id BIGINT PRIMARY KEY,
            number INT,
            title TEXT,
            state TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            raw_data JSONB
        );
    """)
    # Issues table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS raw.issues (
            id BIGINT PRIMARY KEY,
            number INT,
            title TEXT,
            state TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            raw_data JSONB
        );
    """)

def get_last_updated_at(cursor, table_name):
    """Get the maximum updated_at for incremental loading."""
    cursor.execute(f"SELECT MAX(updated_at) FROM raw.{table_name}")
    result = cursor.fetchone()
    if result and result[0]:
        # Return in ISO 8601 format for GitHub API
        return result[0].strftime("%Y-%m-%dT%H:%M:%SZ")
    return None

def fetch_github_data(endpoint, repo="dbt-labs/dbt-core", since=None):
    """Fetch data from GitHub API with pagination and exponential backoff."""
    demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
    if demo_mode:
        logger.info(f"DEMO_MODE is ON. Loading seed data for {endpoint}.")
        seed_file = f"/opt/airflow/data/seed/{endpoint}.json"
        try:
            with open(seed_file, "r") as f:
                data = json.load(f)
                # If 'since' is provided, simulate filtering
                if since:
                    data = [item for item in data if item.get("updated_at") > since]
                return data
        except FileNotFoundError:
            logger.warning(f"Seed file not found: {seed_file}")
            return []

    token = os.getenv("GITHUB_API_TOKEN")
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "ELT-Lakehouse-Pipeline"
    }
    if token:
        headers["Authorization"] = f"token {token}"

    base_url = f"https://api.github.com/repos/{repo}/{endpoint}"
    params = {"per_page": 100, "state": "all"}
    if since:
        params["since"] = since

    all_data = []
    url = base_url

    while url:
        logger.info(f"Fetching {url}")
        
        # Exponential backoff loop
        max_retries = 3
        for attempt in range(max_retries):
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                break
            elif response.status_code in (403, 429):
                # Rate limit hit
                reset_time = int(response.headers.get("X-RateLimit-Reset", time.time() + 60))
                sleep_time = max(reset_time - int(time.time()), 5)
                logger.warning(f"Rate limit hit. Sleeping for {sleep_time} seconds. Attempt {attempt + 1}/{max_retries}")
                time.sleep(sleep_time)
            else:
                response.raise_for_status()
        
        data = response.json()
        if not data:
            break
            
        all_data.extend(data)
        
        # Pagination
        if "next" in response.links:
            url = response.links["next"]["url"]
            params = {} # params are included in the 'next' URL
        else:
            url = None

    return all_data

def ingest_to_db(data, table_name, cursor):
    """Insert or update data in the raw schema (idempotent)."""
    if not data:
        logger.info(f"No new data to ingest into {table_name}.")
        return

    insert_query = f"""
        INSERT INTO raw.{table_name} (id, number, title, state, created_at, updated_at, raw_data)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            number = EXCLUDED.number,
            title = EXCLUDED.title,
            state = EXCLUDED.state,
            created_at = EXCLUDED.created_at,
            updated_at = EXCLUDED.updated_at,
            raw_data = EXCLUDED.raw_data;
    """

    for item in data:
        # Convert string dates to None if empty
        created_at = item.get("created_at")
        updated_at = item.get("updated_at")
        
        cursor.execute(insert_query, (
            item.get("id"),
            item.get("number"),
            item.get("title"),
            item.get("state"),
            created_at,
            updated_at,
            json.dumps(item)
        ))
        
    logger.info(f"Successfully ingested {len(data)} records into raw.{table_name}.")

def run_ingestion(endpoint, table_name):
    """Main callable for Airflow tasks."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            create_raw_tables_if_not_exist(cursor)
            conn.commit()
            
            # Incremental load: find max updated_at
            since = get_last_updated_at(cursor, table_name)
            if since:
                logger.info(f"Incremental load from {since} for {table_name}")
            else:
                logger.info(f"Full load for {table_name}")
                
            data = fetch_github_data(endpoint=endpoint, since=since)
            
            ingest_to_db(data, table_name, cursor)
            conn.commit()
    finally:
        conn.close()

def ingest_pull_requests(**kwargs):
    run_ingestion("pulls", "pull_requests")

def ingest_issues(**kwargs):
    run_ingestion("issues", "issues")
