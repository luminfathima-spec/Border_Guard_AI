import os
import shutil
import datetime
from pathlib import Path
from typing import Dict, Any, List
from app.core.config import settings
from app.core.logging import logger
from app.services.edge.edge_buffer import EdgeEventBuffer

class EdgeStorageManager:
    """
    Monitors edge local disk capacity, manages snapshot storage,
    and enforces priority-based retention limits.
    """

    @classmethod
    def get_disk_metrics(cls) -> Dict[str, Any]:
        """Returns physical disk capacity and edge buffer directory space utilization."""
        data_dir = settings.get_absolute_path(settings.DATA_DIR)
        os.makedirs(data_dir, exist_ok=True)

        usage = shutil.disk_usage(str(data_dir))
        total_bytes = usage.total
        free_bytes = usage.free
        used_bytes = usage.used
        used_pct = round((used_bytes / max(total_bytes, 1)) * 100.0, 2)

        # Measure size of snapshots and edge buffer
        buffer_bytes = 0
        snapshots_dir = settings.get_absolute_path(settings.SNAPSHOTS_DIR)
        if os.path.exists(snapshots_dir):
            for f in os.scandir(snapshots_dir):
                if f.is_file():
                    buffer_bytes += f.stat().st_size

        db_path = EdgeEventBuffer.get_db_path()
        if os.path.exists(db_path):
            buffer_bytes += os.path.getsize(db_path)

        buffer_mb = round(buffer_bytes / (1024 * 1024), 2)
        max_quota_mb = float(settings.EDGE_BUFFER_MAX_DISK_MB)
        quota_utilization_pct = round((buffer_mb / max(max_quota_mb, 1.0)) * 100.0, 2)

        is_warning = (used_pct >= 90.0) or (buffer_mb >= max_quota_mb * 0.9)
        is_quota_breached = buffer_mb >= max_quota_mb

        return {
            "total_bytes": total_bytes,
            "free_bytes": free_bytes,
            "used_bytes": used_bytes,
            "used_percent": used_pct,
            "buffer_size_bytes": buffer_bytes,
            "buffer_size_mb": buffer_mb,
            "max_quota_mb": max_quota_mb,
            "quota_utilization_percent": quota_utilization_pct,
            "is_warning": is_warning,
            "is_quota_breached": is_quota_breached,
        }

    @classmethod
    def enforce_retention(cls) -> Dict[str, Any]:
        """
        Enforces local retention policy:
        1. Prunes already SYNCED evidence older than retention threshold.
        2. If quota is exceeded, performs priority-aware pruning:
           - Deletes lowest priority (LOW, MEDIUM) raw snapshot files first (FIFO by age).
           - Preserves HIGH and CRITICAL perimeter breach snapshots.
           - Preserves metadata in SQLite audit table even when media file is purged.
        """
        metrics = cls.get_disk_metrics()
        conn = EdgeEventBuffer.get_connection()
        files_deleted = 0
        bytes_freed = 0

        retention_days = settings.EDGE_BUFFER_RETENTION_DAYS
        cutoff_date = (
            datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=retention_days)
        ).isoformat()

        # Step 1: Purge synced snapshots older than retention days
        cursor = conn.execute(
            """
            SELECT client_event_id, snapshot_path FROM buffered_events
            WHERE status = 'SYNCED' AND detected_at < ? AND snapshot_path IS NOT NULL;
            """,
            (cutoff_date,),
        )
        old_synced = cursor.fetchall()
        for row in old_synced:
            sp = row["snapshot_path"]
            if sp:
                abs_sp = settings.get_absolute_path(sp)
                if os.path.exists(abs_sp):
                    sz = os.path.getsize(abs_sp)
                    try:
                        os.remove(abs_sp)
                        files_deleted += 1
                        bytes_freed += sz
                    except Exception as err:
                        logger.warning(f"Could not purge old snapshot {abs_sp}: {err}")

        # Step 2: If quota is breached or disk usage > 90%, prune LOW/MEDIUM snapshots
        current_buffer_mb = (metrics["buffer_size_bytes"] - bytes_freed) / (1024 * 1024)
        if current_buffer_mb >= settings.EDGE_BUFFER_MAX_DISK_MB or metrics["used_percent"] >= 90.0:
            logger.warning(f"Edge storage quota exceeded ({current_buffer_mb:.1f} MB >= {settings.EDGE_BUFFER_MAX_DISK_MB} MB). Pruning low-priority media.")
            cursor = conn.execute(
                """
                SELECT client_event_id, snapshot_path, severity FROM buffered_events
                WHERE severity IN ('LOW', 'MEDIUM') AND snapshot_path IS NOT NULL
                ORDER BY detected_at ASC;
                """
            )
            low_priority = cursor.fetchall()
            for row in low_priority:
                sp = row["snapshot_path"]
                if sp:
                    abs_sp = settings.get_absolute_path(sp)
                    if os.path.exists(abs_sp):
                        sz = os.path.getsize(abs_sp)
                        try:
                            os.remove(abs_sp)
                            files_deleted += 1
                            bytes_freed += sz
                        except Exception as err:
                            logger.warning(f"Notice pruning file {abs_sp}: {err}")

                # Check if buffer is now within safe threshold (80% of quota)
                if ((metrics["buffer_size_bytes"] - bytes_freed) / (1024 * 1024)) < (settings.EDGE_BUFFER_MAX_DISK_MB * 0.8):
                    break

        return {
            "files_deleted": files_deleted,
            "bytes_freed": bytes_freed,
            "bytes_freed_mb": round(bytes_freed / (1024 * 1024), 2),
            "remaining_buffer_mb": round((metrics["buffer_size_bytes"] - bytes_freed) / (1024 * 1024), 2),
            "status": "QUOTA_COMPLIANT" if (metrics["buffer_size_bytes"] - bytes_freed) / (1024 * 1024) < settings.EDGE_BUFFER_MAX_DISK_MB else "QUOTA_PRESSURE",
        }
