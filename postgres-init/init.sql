-- Create schemas required for the project
CREATE SCHEMA IF NOT EXISTS airflow_meta;
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS mart;
CREATE SCHEMA IF NOT EXISTS ducklake_catalog;

-- Set permissions (assuming standard elt_user)
-- We will use the user defined in POSTGRES_USER environment variable,
-- but typically initdb runs as superuser and the DB/user are created by docker-entrypoint.
-- The schemas will be owned by the POSTGRES_USER.
