import csv
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from forecasting_db.models import Constraints, ForecastRuns, Forecasts, Measurements

# Config
DB_CONFIG = {
    "host": "localhost",
    "port": 15432,
    "dbname": "appdb",
    "user": "postgres",
    "password": "skyblu55!",
}

DATABASE_URL = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

MODEL_MAP = {
    "Forecasts": Forecasts,
    "ForecastRuns": ForecastRuns,
    "Constraints": Constraints,
    "Measurements": Measurements,
}


def load_csv_to_test_table(csv_file, model, batch_size=500):
    # Step 1: load CSV
    with open(csv_file, "r") as f:
        reader = csv.DictReader(f)
        rows = [model(**row) for row in reader]

    session = Session()
    try:
        # Step 2: optional connection test
        try:
            conn = engine.connect()
            print("✅ DB connection successful")
            conn.close()
        except Exception as e:
            print(f"❌ DB connection failed: {e}")
            return

        # Step 3: insert in batches
        for i in range(0, len(rows), batch_size):
            batch = rows[i : i + batch_size]
            session.add_all(batch)
            session.commit()
            print(f"Inserted rows {i+1} to {i+len(batch)} into {model.__tablename__}")

    except Exception as e:
        session.rollback()
        print(f"Error inserting rows: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    print("Starting script")
    if len(sys.argv) != 3:
        print("Usage: python load_test_data.py <csv_file> <ModelName>")
        sys.exit(1)

    csv_file = sys.argv[1]
    model = MODEL_MAP[sys.argv[2]]

    load_csv_to_test_table(csv_file, model)
