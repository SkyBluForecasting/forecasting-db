## Table of Contents

- [Project Overview](#project-overview)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Local Development Setup](#local-development-setup)
- [Database Schema](#database-schema)
- [Database Migrations](#database-migrations)
- [Development Workflow](#development-workflow)
- [Pre-Commit Hooks](#pre-commit-hooks)


## Project Overview

This project manages the database schema and migrations for the forecasting application.  It provides:

- **Python Package**: An installable package via AWS Code Artifact to access SQLAlchemy models and database utilities directly from other applications.
- **Database Schema**: SQLAlchemy models defining the data structure
- **Alembic Migrations**: Version-controlled database schema changes
- **Docker Environment**: Local TimescaleDB instance for development and testing
- **Migration Testing**: Automated tests to ensure migrations work correctly

This repository serves both as a database schema/migrations manager and a shared Python package for other parts of the forecasting application.


## Local Development Setup

### 1. Clone and Setup Environment

```bash
# Clone the repository
git clone <repository-url>
cd forecasting-db

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Install the package in editable mode (so imports work if running things locally)

```bash
pip install -e .
```

### 4. Create an env file to specify database URL to test with.

```bash
echo "SQLALCHEMY_URL=postgresql+psycopg2://postgres:localpass@localhost:5432/appdb" > .env
```

### 5. Start Database Services

```bash
docker compose up -d
```

This starts:
- **TimescaleDB**: PostgreSQL with time-series extensions
- **Adminer**: Web-based database administration tool

### 6. Database Connection Details

To access the database with psql, run:

`docker compose exec timescaledb psql -U postgres -d appdb`

To access the database in a GUI with adminer:

- URL: http://localhost:8080
- System: `PostgreSQL`
- Server: `timescaledb`
- User: `postgres`
- Password: `localpass`
- Database: `appdb`

## Database Migrations

### Running Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Create a new migration
alembic revision --autogenerate -m "name of migration"

# Downgrade to previous version
alembic downgrade -1

# Show current migration status
alembic current

# Show migration history
alembic history
```

## Development Workflow

### 1. Schema Changes

1. Modify the SQLAlchemy models in `forecasting_db/models.py`
2. Generate migration: `alembic revision --autogenerate -m "description of schema change"`
3. Review the generated migration file in `alembic_migrations/versions/`
4. Test the migration: `alembic upgrade head`

### 2. Testing Migrations

To test that migrations work correctly:

```bash
python -m pytest tests/
```

To run tests with coverage:

```bash
coverage run -m pytest tests/ && coverage report -m
```

### 3. Stopping Services

```bash
# Stop and remove containers
docker compose down

# Stop and remove containers with volumes (⚠️ removes data)
docker compose down -v

# Restart services
docker compose up -d

# Remove local PostgreSQL data
rm -rf pgdata/
```

## Pre-Commit Hooks

Pre-commit hooks are configured for this repository. To run them locally:
```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

## How to Connect to RDS Postgres

These are the steps to connect to a staging or production version of the RDS database.
The RDS instance is not publicly accessible, so you need to go through the EC2 instance in the same VPC.

### Option 1: Use psql (cli)

1. SSH into the forecasting-db EC2 instance: `ssh -i /path/to/your/key.pem ec2-user@<EC2-PUBLIC-IP>`

2. Once on the EC2 instance, connect to RDS: `psql -h <RDS-ENDPOINT> -U postgres -d appdb -p 5432`

### Option 2: Use the rds_tunnel.sh script to use Adminer and use a SSH tunnel from local machine
