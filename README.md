# Forecasting Database

PostgreSQL TimescaleDB for storing forecasts, historical data, and training data.


## Project Structure

```
forecasting-db/
├── alembic/           # Alembic database migrations
│   ├── versions/        # Migration files
│   ├── env.py          # Alembic environment configuration
│   └── script.py.mako  # Migration template
├── tests/              # Test files
├── alembic.ini         # Alembic configuration
├── docker-compose.yml  # Docker services configuration
├── requirements.txt    # Python dependencies
└── README.md          # This file
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

### 4. Start Database Services

```bash
docker compose up -d
```

This starts:
- **TimescaleDB**: PostgreSQL with time-series extensions
- **Adminer**: Web-based database administration tool

### 4. Database Connection Details

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

```bash
# Run tests
python -m pytest tests/
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

## Pre-Commit

Pre-commit hooks are set-up for this repo. To run them locally:
```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

## Configuration

### Environment Variables

The project uses the following default configuration in `alembic.ini`:

```
sqlalchemy.url = postgresql+psycopg2://postgres:localpass@localhost:5432/appdb
```

To use different database credentials, update the connection string in `alembic.ini` or set environment variables.
