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

- **Database Schema**: SQLAlchemy models defining the forecast data structure
- **Alembic Migrations**: Version-controlled database schema changes
- **Docker Environment**: Local TimescaleDB instance for development and testing
- **Migration Testing**: Automated tests to ensure migrations work correctly

This is primarily a database schema repository, not a Python package for import by other applications.


## Project Structure

```
forecasting-db/
├── forecasting_db/      # SQLAlchemy models for schema definition
│   └── models.py       # Database table models
├── alembic_migrations/  # Database migration files
│   ├── versions/        # Migration scripts
│   ├── env.py           # Alembic environment setup
│   └── script.py.mako   # Migration template
├── tests/               # Migration and schema tests
├── alembic.ini          # Alembic configuration
├── docker-compose.yml   # Local database setup
└── requirements.txt     # Development dependencies
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
