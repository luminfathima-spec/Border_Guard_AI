import os
import sqlite3
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings
from app.core.logging import logger

Base = declarative_base()

def get_engine():
    """
    Initializes SQLAlchemy database engine.
    Tries PostgreSQL if configured; automatically falls back to SQLite if PostgreSQL is unavailable.
    """
    db_url = settings.DATABASE_URL
    eng = None
    if db_url.startswith("postgresql"):
        try:
            test_engine = create_engine(
                db_url,
                connect_args={"connect_timeout": 1},
                pool_pre_ping=True,
            )
            with test_engine.connect():
                pass
            logger.info("Successfully connected to PostgreSQL database.")
            eng = test_engine
        except Exception as e:
            logger.warning(f"PostgreSQL connection failed ({e}). Falling back to local SQLite database.")
            sqlite_path = settings.get_absolute_path("data/sentinelai.db")
            os.makedirs(sqlite_path.parent, exist_ok=True)
            eng = create_engine(
                f"sqlite:///{sqlite_path}",
                connect_args={"check_same_thread": False},
            )
    elif db_url.startswith("sqlite"):
        eng = create_engine(
            db_url,
            connect_args={"check_same_thread": False},
        )
    else:
        eng = create_engine(db_url)

    # Automatically create tables and seed default users if not yet seeded
    try:
        import app.models.user
        import app.models.camera
        import app.models.video
        import app.models.detection
        import app.models.event
        import app.models.alert
        import app.models.incident
        import app.models.evidence
        import app.models.audit
        from app.db.init_db import init_db

        Base.metadata.create_all(bind=eng)

        # Migrate SQLite columns if missing
        if "sqlite" in str(eng.url):
            try:
                with eng.connect() as conn:
                    # Check columns on videos
                    existing_cols = [row[1] for row in conn.execute(text("PRAGMA table_info(videos)")).fetchall()]
                    for col_name, col_type in [
                        ("processed_path", "VARCHAR(512)"),
                        ("total_detections_count", "INTEGER DEFAULT 0"),
                        ("total_tracked_objects_count", "INTEGER DEFAULT 0"),
                        ("total_incidents_count", "INTEGER DEFAULT 0"),
                    ]:
                        if col_name not in existing_cols:
                            conn.execute(text(f"ALTER TABLE videos ADD COLUMN {col_name} {col_type}"))
                            conn.commit()
            except Exception as mig_err:
                logger.warning(f"SQLite migration check notice: {mig_err}")

        TempSession = sessionmaker(autocommit=False, autoflush=False, bind=eng)
        db = TempSession()
        try:
            init_db(db)
        finally:
            db.close()
    except Exception as err:
        logger.error(f"Auto-migration/seed failed: {err}")

    return eng

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    FastAPI dependency that provides a transactional database session per request.
    Automatically closes session upon completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
