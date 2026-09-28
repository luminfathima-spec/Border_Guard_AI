import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.db.database import engine, Base
import app.models  # Ensure all models are registered with Base

def init_db():
    print("Connecting to PostgreSQL and creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully:")
    for table_name in Base.metadata.tables.keys():
        print(f"  - {table_name}")

if __name__ == "__main__":
    init_db()
