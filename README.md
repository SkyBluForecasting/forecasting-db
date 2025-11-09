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
- **Database Schema**: SQLAlchemy models defining the forecast data structure
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

**TimescaleDB Connection:**
- Host: `localhost`
- Port: `5432`
- User: `postgres`
- Password: `localpass`
- Database: `appdb`

**Adminer Access:**
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
5. Commit the migration file to version control

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

### Option 2: Use Adminer (if you want a GUI)

1. Make sure Adminer is running on the EC2 instance

- Run `docker ps`.
- If no container named adminer is running, start it: `docker run -d -p 8080:8080 --name adminer adminer`

2. Forward Adminer to your local machine. This maps your local port 8080 to EC2’s 8080, where Adminer is running.

```bash
ssh -i /path/to/your/key.pem -L 8080:localhost:8080 ec2-user@<EC2-PUBLIC-IP>
```

3. Open Adminer in your browser:

- Go to localhost:8080
- Login with your RDS credentials
    - Server: RDS Endpoint
    - Username: postgres
    - Password:
    - Database: appdb


### Option 3: Use SSH tunnel from local machine

1. Forward a local port to the EC2 instance, then connect to RDS through it. This makes localhost:5432 act as if its the RDS.E.g.,

`ssh -i ../engine-key.pem -L 15432:<RDS_ENDPOINT>:5432 ec2-user@<EC2 IP> -N &`

2. Then if you're running scripts, use `"host": "localhost"`
