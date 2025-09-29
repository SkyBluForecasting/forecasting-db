## Table of Contents

- [Quick Start](#quick-start)
- [Project Overview](#project-overview)
- [Project Structure](#project-structure)
- [Local Development Setup](#local-development-setup)
- [Database Schema](#database-schema)
- [Database Migrations](#database-migrations)
- [Development Workflow](#development-workflow)
- [Pre-Commit Hooks](#pre-commit-hooks)

## Quick Start

```bash
# Clone and setup
git clone <repository-url>
cd forecasting-db
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Create a .env file with your database URL for running locally
echo "SQLALCHEMY_URL=postgresql+psycopg2://postgres:localpass@localhost:5432/appdb" > .env

# Start database
docker compose up -d

# Run migrations
alembic upgrade head
```

## Project Overview

This project provides a Python package for managing forecast data in TimescaleDB, a PostgreSQL extension optimized for time-series data. The package includes:

- **SQLAlchemy Models**: Type-safe database models for forecast data
- **Alembic Migrations**: Version-controlled database schema management
- **Docker Environment**: Containerized TimescaleDB with Adminer for database administration
- **Testing Framework**: Comprehensive test suite with migration testing

## Project Structure

```
forecasting-db/
├── forecasting_db/      # Python package
│   └── models.py       # SQLAlchemy models
├── alembic_migrations/  # Alembic database migrations
│   ├── versions/        # Migration files
│   ├── env.py           # Alembic environment configuration
│   └── script.py.mako   # Migration template
├── tests/               # Tests
├── alembic.ini          # Alembic configuration
├── docker-compose.yml   # Docker services configuration
├── requirements.txt     # Python dependencies
└── setup.py            # Package setup configuration
```

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

### 4. Create an env file

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

`docker compose exec timescaledb psql -U postgres`

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

### 1. Database Changes

1. Make changes to your SQLAlchemy models
2. Generate migration: `alembic revision --autogenerate -m "your changes"`
3. Review the generated migration file
4. Apply migration: `alembic upgrade head`

### 2. Testing

To run tests:

```bash
python -m pytest tests/
```

To run tests and also check coverage:

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
