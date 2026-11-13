import os
import json
import sqlite3
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.core.logging import logger

class EdgeEventBuffer:
    """
    Dedicated local SQLite WAL-backed event buffer for forward-deployed edge nodes.
    Preserves unique client event IDs, original detection timestamps,
    and associated evidence media references across power losses or network blackouts.
    """
    _connection: Optional[sqlite3.Connection] = None
    _db_path: Optional[Path] = None

    @classmethod
    def get_db_path(cls) -> Path:
        if cls._db_path is None:
            raw_path = settings.get_absolute_path(settings.EDGE_BUFFER_DB_PATH)
            cls._db_path = Path(raw_path)
            cls._db_path.parent.mkdir(parents=True, exist_ok=True)
        return cls._db_path

    @classmethod
    def set_db_path(cls, custom_path: Path) -> None:
        """Sets custom database path (useful for isolated unit tests)."""
        cls.close()
        cls._db_path = custom_path
        cls._db_path.parent.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_connection(cls) -> sqlite3.Connection:
        if cls._connection is None:
            db_path = cls.get_db_path()
            cls._connection = sqlite3.connect(str(db_path), check_same_thread=False)
            cls._connection.row_factory = sqlite3.Row
            # Enable WAL mode for crash-safety and concurrent read/write
            cls._connection.execute("PRAGMA journal_mode=WAL;")
            cls._connection.execute("PRAGMA synchronous=NORMAL;")
            cls._init_schema(cls._connection)
        return cls._connection

    @classmethod
    def close(cls) -> None:
        """Explicitly closes database connection (simulates process shutdown or restart)."""
        if cls._connection is not None:
            try:
                cls._connection.close()
            except Exception as e:
                logger.warning(f"Notice closing edge buffer connection: {e}")
            finally:
                cls._connection = None

    @classmethod
    def restart(cls) -> None:
        """Simulates edge process crash and reboot."""
        cls.close()
        cls.get_connection()

    @classmethod
    def _init_schema(cls, conn: sqlite3.Connection) -> None:
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS buffered_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_event_id TEXT UNIQUE NOT NULL,
                    event_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    camera_id INTEGER,
                    video_id INTEGER,
                    detected_at TEXT NOT NULL,
                    description TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    metadata_json TEXT DEFAULT '{}',
                    snapshot_path TEXT,
                    clip_path TEXT,
                    edge_node_id TEXT,
                    status TEXT DEFAULT 'PENDING',
                    retry_count INTEGER DEFAULT 0,
                    next_retry_at TEXT,
                    last_error TEXT,
                    created_at TEXT NOT NULL
                );
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS ix_buffered_events_status_detected 
                ON buffered_events (status, detected_at);
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS buffered_evidence (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_evidence_id TEXT UNIQUE NOT NULL,
                    client_event_id TEXT NOT NULL,
                    evidence_type TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size_bytes INTEGER,
                    checksum_sha256 TEXT NOT NULL,
                    detected_at TEXT NOT NULL,
                    metadata_json TEXT DEFAULT '{}',
                    status TEXT DEFAULT 'PENDING',
                    created_at TEXT NOT NULL
                );
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS ix_buffered_evidence_event_id 
                ON buffered_evidence (client_event_id);
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS buffered_tracks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tracking_id INTEGER NOT NULL,
                    video_id INTEGER,
                    camera_id INTEGER,
                    object_type TEXT NOT NULL,
                    first_seen_frame INTEGER NOT NULL,
                    last_seen_frame INTEGER NOT NULL,
                    first_seen_timestamp REAL NOT NULL,
                    last_seen_timestamp REAL NOT NULL,
                    dwell_time_seconds REAL NOT NULL,
                    max_confidence REAL NOT NULL,
                    trajectory_json TEXT DEFAULT '[]',
                    status TEXT DEFAULT 'PENDING',
                    created_at TEXT NOT NULL
                );
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS sync_audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    events_synced INTEGER DEFAULT 0,
                    evidence_synced INTEGER DEFAULT 0,
                    duplicates_prevented INTEGER DEFAULT 0,
                    conflicts_resolved INTEGER DEFAULT 0,
                    bytes_transferred INTEGER DEFAULT 0,
                    duration_ms INTEGER DEFAULT 0,
                    status TEXT NOT NULL
                );
            """)

    @classmethod
    def buffer_event(
        cls,
        client_event_id: str,
        event_type: str,
        severity: str,
        camera_id: Optional[int],
        video_id: Optional[int],
        detected_at: datetime.datetime,
        description: str,
        confidence: float,
        metadata_json: Optional[Dict[str, Any]] = None,
        snapshot_path: Optional[str] = None,
        clip_path: Optional[str] = None,
        edge_node_id: Optional[str] = None,
    ) -> int:
        """
        Stores an event locally during an outage or in edge mode.
        Guarantees that original client_event_id and detected_at timestamp are preserved.
        """
        conn = cls.get_connection()
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        detected_iso = detected_at.isoformat()
        node_id = edge_node_id or settings.EDGE_NODE_ID
        meta_str = json.dumps(metadata_json or {})

        with conn:
            cursor = conn.execute(
                """
                INSERT INTO buffered_events (
                    client_event_id, event_type, severity, camera_id, video_id,
                    detected_at, description, confidence, metadata_json,
                    snapshot_path, clip_path, edge_node_id, status, retry_count, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING', 0, ?)
                ON CONFLICT(client_event_id) DO NOTHING;
                """,
                (
                    client_event_id, event_type, severity, camera_id, video_id,
                    detected_iso, description, confidence, meta_str,
                    snapshot_path, clip_path, node_id, now_iso
                ),
            )
            return cursor.lastrowid or 0

    @classmethod
    def buffer_evidence(
        cls,
        client_evidence_id: str,
        client_event_id: str,
        evidence_type: str,
        file_path: str,
        checksum_sha256: str,
        detected_at: datetime.datetime,
        file_size_bytes: Optional[int] = None,
        metadata_json: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Stores evidence file reference locally associated with a buffered event."""
        conn = cls.get_connection()
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        detected_iso = detected_at.isoformat()
        meta_str = json.dumps(metadata_json or {})

        with conn:
            cursor = conn.execute(
                """
                INSERT INTO buffered_evidence (
                    client_evidence_id, client_event_id, evidence_type, file_path,
                    file_size_bytes, checksum_sha256, detected_at, metadata_json, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'PENDING', ?)
                ON CONFLICT(client_evidence_id) DO NOTHING;
                """,
                (
                    client_evidence_id, client_event_id, evidence_type, file_path,
                    file_size_bytes, checksum_sha256, detected_iso, meta_str, now_iso
                ),
            )
            return cursor.lastrowid or 0

    @classmethod
    def buffer_track(
        cls,
        tracking_id: int,
        video_id: Optional[int],
        camera_id: Optional[int],
        object_type: str,
        first_seen_frame: int,
        last_seen_frame: int,
        first_seen_timestamp: float,
        last_seen_timestamp: float,
        dwell_time_seconds: float,
        max_confidence: float,
        trajectory_json: Optional[List[Dict[str, Any]]] = None,
    ) -> int:
        conn = cls.get_connection()
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        traj_str = json.dumps(trajectory_json or [])

        with conn:
            cursor = conn.execute(
                """
                INSERT INTO buffered_tracks (
                    tracking_id, video_id, camera_id, object_type,
                    first_seen_frame, last_seen_frame, first_seen_timestamp, last_seen_timestamp,
                    dwell_time_seconds, max_confidence, trajectory_json, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING', ?);
                """,
                (
                    tracking_id, video_id, camera_id, object_type,
                    first_seen_frame, last_seen_frame, first_seen_timestamp, last_seen_timestamp,
                    dwell_time_seconds, max_confidence, traj_str, now_iso
                ),
            )
            return cursor.lastrowid or 0

    @classmethod
    def get_pending_events(cls, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Retrieves pending buffered events in chronological order (detected_at ASC).
        Skips items whose next_retry_at is in the future.
        """
        conn = cls.get_connection()
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        cursor = conn.execute(
            """
            SELECT * FROM buffered_events
            WHERE status = 'PENDING'
              AND (next_retry_at IS NULL OR next_retry_at <= ?)
            ORDER BY detected_at ASC
            LIMIT ?;
            """,
            (now_iso, limit),
        )
        rows = cursor.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["metadata_json"] = json.loads(d["metadata_json"] or "{}")
            result.append(d)
        return result

    @classmethod
    def get_pending_evidence_for_event(cls, client_event_id: str) -> List[Dict[str, Any]]:
        conn = cls.get_connection()
        cursor = conn.execute(
            """
            SELECT * FROM buffered_evidence
            WHERE client_event_id = ?
            ORDER BY detected_at ASC;
            """,
            (client_event_id,),
        )
        rows = cursor.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["metadata_json"] = json.loads(d["metadata_json"] or "{}")
            result.append(d)
        return result

    @classmethod
    def mark_event_synced(cls, client_event_id: str) -> None:
        conn = cls.get_connection()
        with conn:
            conn.execute(
                """
                UPDATE buffered_events
                SET status = 'SYNCED'
                WHERE client_event_id = ?;
                """,
                (client_event_id,),
            )
            conn.execute(
                """
                UPDATE buffered_evidence
                SET status = 'SYNCED'
                WHERE client_event_id = ?;
                """,
                (client_event_id,),
            )

    @classmethod
    def mark_event_failed(cls, client_event_id: str, error_message: str, backoff_seconds: float) -> None:
        conn = cls.get_connection()
        next_retry = (
            datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=backoff_seconds)
        ).isoformat()

        with conn:
            # Check current retry count
            cursor = conn.execute(
                "SELECT retry_count FROM buffered_events WHERE client_event_id = ?;",
                (client_event_id,),
            )
            row = cursor.fetchone()
            current_retries = (row["retry_count"] if row else 0) + 1
            new_status = "QUARANTINED" if current_retries >= settings.EDGE_MAX_RETRIES else "PENDING"

            conn.execute(
                """
                UPDATE buffered_events
                SET status = ?,
                    retry_count = ?,
                    next_retry_at = ?,
                    last_error = ?
                WHERE client_event_id = ?;
                """,
                (new_status, current_retries, next_retry, error_message, client_event_id),
            )

    @classmethod
    def record_sync_session(
        cls,
        session_id: str,
        started_at: datetime.datetime,
        completed_at: datetime.datetime,
        events_synced: int,
        evidence_synced: int,
        duplicates_prevented: int,
        conflicts_resolved: int,
        bytes_transferred: int,
        duration_ms: int,
        status: str,
    ) -> None:
        conn = cls.get_connection()
        with conn:
            conn.execute(
                """
                INSERT INTO sync_audit_log (
                    session_id, started_at, completed_at, events_synced,
                    evidence_synced, duplicates_prevented, conflicts_resolved,
                    bytes_transferred, duration_ms, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    session_id, started_at.isoformat(), completed_at.isoformat(),
                    events_synced, evidence_synced, duplicates_prevented,
                    conflicts_resolved, bytes_transferred, duration_ms, status
                ),
            )

    @classmethod
    def get_buffer_stats(cls) -> Dict[str, Any]:
        conn = cls.get_connection()
        cursor = conn.execute(
            """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'PENDING' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status = 'SYNCED' THEN 1 ELSE 0 END) as synced,
                SUM(CASE WHEN status = 'QUARANTINED' THEN 1 ELSE 0 END) as quarantined,
                MIN(CASE WHEN status = 'PENDING' THEN detected_at ELSE NULL END) as oldest_pending
            FROM buffered_events;
            """
        )
        row = cursor.fetchone()
        evidence_cursor = conn.execute("SELECT COUNT(*) as ev_total FROM buffered_evidence WHERE status = 'PENDING';")
        ev_row = evidence_cursor.fetchone()

        db_path = cls.get_db_path()
        db_size_bytes = os.path.getsize(db_path) if db_path.exists() else 0

        return {
            "total_buffered_events": row["total"] or 0,
            "pending_sync_count": row["pending"] or 0,
            "synced_count": row["synced"] or 0,
            "quarantined_count": row["quarantined"] or 0,
            "pending_evidence_count": ev_row["ev_total"] or 0,
            "oldest_pending_timestamp": row["oldest_pending"],
            "db_file_size_bytes": db_size_bytes,
        }

    @classmethod
    def clear_all(cls) -> None:
        """Clears all buffered tables (for test environment resets)."""
        conn = cls.get_connection()
        with conn:
            conn.execute("DELETE FROM buffered_events;")
            conn.execute("DELETE FROM buffered_evidence;")
            conn.execute("DELETE FROM buffered_tracks;")
            conn.execute("DELETE FROM sync_audit_log;")
