.PHONY: setup up down test test-dbt test-dag seed lint help

help:
	@echo "Available commands:"
	@echo "  make setup     - Set up the project (copy .env, init DB, etc.)"
	@echo "  make up        - Start the Docker Compose environment"
	@echo "  make down      - Stop the Docker Compose environment"
	@echo "  make test      - Run all tests (pytest + dbt test)"
	@echo "  make test-dbt  - Run dbt tests"
	@echo "  make test-dag  - Run Airflow DAG integrity tests"
	@echo "  make seed      - Load seed data (DEMO_MODE)"
	@echo "  make lint      - Run code linters (ruff, sqlfluff)"

setup:
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env from .env.example"; fi
	@echo "Setup complete. Please verify .env settings."

up:
	docker compose -f docker-compose.yml -f docker-compose.fase2.yml up -d
	@echo "Waiting for services to be healthy..."
	@sleep 10
	@echo "Airflow UI: http://localhost:8080 (admin/admin)"
	@echo "Metabase UI: http://localhost:3000"

down:
	docker compose -f docker-compose.yml -f docker-compose.fase2.yml down -v
	@echo "Containers stopped and volumes removed."

test: test-dag test-dbt
	AIRFLOW__CORE__LOAD_EXAMPLES=false airflow db migrate && PYTHONPATH=$(PWD)/airflow pytest tests/

test-dag:
	AIRFLOW__CORE__LOAD_EXAMPLES=false airflow db migrate && PYTHONPATH=$(PWD)/airflow pytest tests/test_dag_integrity.py

test-dbt:
	cd dbt && PYTHONPATH=$(PWD)/dbt POSTGRES_HOST=localhost dbt test --profiles-dir .

seed:
	@echo "Triggering seed data initialization (handled via DAG / DEMO_MODE)"

lint:
	ruff check .
	sqlfluff lint dbt/models
