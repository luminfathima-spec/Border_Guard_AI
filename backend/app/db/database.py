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
        import app.models.track
        import app.models.event
        import app.models.alert
        import app.models.incident
        import app.models.evidence
        import app.models.ai_analysis
        import app.models.report
        import app.models.audit
        import app.models.verification
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

                    # Check columns on ai_analyses
                    existing_ai_cols = [row[1] for row in conn.execute(text("PRAGMA table_info(ai_analyses)")).fetchall()]
                    if "prompt_version" not in existing_ai_cols and len(existing_ai_cols) > 0:
                        conn.execute(text("ALTER TABLE ai_analyses ADD COLUMN prompt_version VARCHAR(50) DEFAULT '2026.04.1'"))
                        conn.commit()

                    # Check columns on reports
                    existing_report_cols = [row[1] for row in conn.execute(text("PRAGMA table_info(reports)")).fetchall()]
                    if len(existing_report_cols) > 0:
                        for col_name, col_type in [
                            ("review_status", "VARCHAR(50) DEFAULT 'DRAFT'"),
                            ("approved_by_user_id", "INTEGER"),
                            ("approved_at", "DATETIME"),
                            ("model_name", "VARCHAR(100) DEFAULT 'gemini-2.5-flash'"),
                            ("prompt_version", "VARCHAR(50) DEFAULT '2026.04.1'"),
                            ("sections_json", "JSON DEFAULT '{}'"),
                            ("human_corrections", "JSON DEFAULT '[]'"),
                            ("audit_history", "JSON DEFAULT '[]'"),
                        ]:
                            if col_name not in existing_report_cols:
                                conn.execute(text(f"ALTER TABLE reports ADD COLUMN {col_name} {col_type}"))
                                conn.commit()

                    # Check columns on security_events (Phase 8 Edge Sync)
                    existing_ev_cols = [row[1] for row in conn.execute(text("PRAGMA table_info(security_events)")).fetchall()]
                    if len(existing_ev_cols) > 0:
                        for col_name, col_type in [
                            ("client_event_id", "VARCHAR(100)"),
                            ("sync_status", "VARCHAR(50) DEFAULT 'SYNCED'"),
                            ("synced_at", "DATETIME"),
                            ("edge_node_id", "VARCHAR(100)"),
                        ]:
                            if col_name not in existing_ev_cols:
                                conn.execute(text(f"ALTER TABLE security_events ADD COLUMN {col_name} {col_type}"))
                                conn.commit()

                    # Check columns on evidence (Phase 8 Edge Sync)
                    existing_evidence_cols = [row[1] for row in conn.execute(text("PRAGMA table_info(evidence)")).fetchall()]
                    if len(existing_evidence_cols) > 0:
                        for col_name, col_type in [
                            ("client_evidence_id", "VARCHAR(100)"),
                            ("sync_status", "VARCHAR(50) DEFAULT 'SYNCED'"),
                            ("synced_at", "DATETIME"),
                        ]:
                            if col_name not in existing_evidence_cols:
                                conn.execute(text(f"ALTER TABLE evidence ADD COLUMN {col_name} {col_type}"))
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
