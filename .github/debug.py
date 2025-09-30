import os

from sqlalchemy import create_engine

url = os.environ.get("SQLALCHEMY_URL", "").replace("skyblu55!", "skyblu55X")
try:
    create_engine(url)
    print("SQLAlchemy URL parsed successfully!")
except Exception as e:
    print("Parsing failed:", e)
