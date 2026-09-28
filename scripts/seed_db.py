import sys
import datetime
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.db.database import SessionLocal, engine, Base
from app.models import (
    User, UserRole,
    Camera, CameraStatus,
    SecurityEvent, EventType, SeverityLevel,
    Alert, AlertStatus,
    Incident, IncidentStatus,
    AuditLog
)
from app.core.security import get_password_hash

def seed():
    print("Seeding SentinelAI database with baseline operational data...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Seed Users
        existing_admin = db.query(User).filter(User.email == "admin@sentinel.ai").first()
        if not existing_admin:
            admin_user = User(
                name="Commander R. Sharma",
                email="admin@sentinel.ai",
                password_hash=get_password_hash("AdminPassword123!"),
                role=UserRole.ADMIN.value,
                is_active=True,
            )
            analyst_user = User(
                name="Officer A. Verma",
                email="analyst@sentinel.ai",
                password_hash=get_password_hash("AnalystPassword123!"),
                role=UserRole.SECURITY_ANALYST.value,
                is_active=True,
            )
            operator_user = User(
                name="Field Operator K. Singh",
                email="operator@sentinel.ai",
                password_hash=get_password_hash("OperatorPassword123!"),
                role=UserRole.OPERATOR.value,
                is_active=True,
            )
            db.add_all([admin_user, analyst_user, operator_user])
            db.commit()
            print("  [+] Seeded 3 Operational Users (Admin, Analyst, Operator)")
        else:
            print("  [*] Users already exist. Skipping user seed.")

        # 2. Seed Border Surveillance Cameras
        cam_count = db.query(Camera).count()
        if cam_count == 0:
            cam1 = Camera(
                name="Northern Perimeter - Gate A",
                camera_identifier="CAM-NP-01",
                location="Sector 4 Border Outpost North",
                latitude=32.7266,
                longitude=74.8570,
                status=CameraStatus.ONLINE.value,
                zone="Sector 4 (North Perimeter)",
                restricted_zones=[
                    {
                        "id": "zone-np-01",
                        "name": "High Security Buffer Strip",
                        "polygon": [
                            {"x": 0.15, "y": 0.20},
                            {"x": 0.85, "y": 0.20},
                            {"x": 0.90, "y": 0.80},
                            {"x": 0.10, "y": 0.80},
                        ],
                        "alert_severity": "HIGH",
                    }
                ],
                virtual_lines=[
                    {
                        "id": "line-np-01",
                        "name": "Perimeter Demarcation Line",
                        "p1": {"x": 0.10, "y": 0.50},
                        "p2": {"x": 0.90, "y": 0.50},
                        "direction": "BOTH",
                        "alert_severity": "CRITICAL",
                    }
                ],
            )

            cam2 = Camera(
                name="Eastern Buffer Zone - Checkpoint Beta",
                camera_identifier="CAM-EB-02",
                location="Sector 7 Forward Recon Point",
                latitude=32.7150,
                longitude=74.8720,
                status=CameraStatus.ONLINE.value,
                zone="Sector 7 (East Buffer)",
                restricted_zones=[
                    {
                        "id": "zone-eb-01",
                        "name": "Zero-Tolerance Exclusion Zone",
                        "polygon": [
                            {"x": 0.25, "y": 0.35},
                            {"x": 0.75, "y": 0.35},
                            {"x": 0.80, "y": 0.90},
                            {"x": 0.20, "y": 0.90},
                        ],
                        "alert_severity": "CRITICAL",
                    }
                ],
                virtual_lines=[],
            )

            cam3 = Camera(
                name="River Basin Watchtower",
                camera_identifier="CAM-RB-03",
                location="Sector 9 Riverine Terrain",
                latitude=32.6980,
                longitude=74.8410,
                status=CameraStatus.ONLINE.value,
                zone="Sector 9 (River Basin)",
                restricted_zones=[],
                virtual_lines=[],
            )

            cam4 = Camera(
                name="South Valley Convoy Gate",
                camera_identifier="CAM-SV-04",
                location="Sector 2 Logistics Route",
                latitude=32.6820,
                longitude=74.8300,
                status=CameraStatus.DEGRADED.value,
                zone="Sector 2 (South Valley)",
                restricted_zones=[],
                virtual_lines=[],
            )

            db.add_all([cam1, cam2, cam3, cam4])
            db.commit()
            print("  [+] Seeded 4 Border Surveillance Cameras")

            # 3. Seed Sample Incident, Events, and Alerts
            inc1 = Incident(
                incident_number="INC-2026-0001",
                title="Multiple Person Intrusion detected along Sector 4 Buffer Strip",
                description="Automated computer vision triggered restricted zone intrusion and tripwire breach along Sector 4 North Perimeter. Two unidentified targets detected in buffer zone.",
                severity="CRITICAL",
                status=IncidentStatus.OPEN.value,
                ai_summary="Automated Threat Assessment: Two coordinated individuals breached the Sector 4 High Security Buffer Strip at 21:40 hrs moving southward across the perimeter demarcation line. Rapid entry speed and trajectory suggest intentional bypass of primary fence gate. Immediate tactical dispatch to Sector 4 Outpost recommended.",
                ai_recommendations=[
                    "Dispatch Quick Reaction Team (QRT) to Sector 4 Outpost immediately.",
                    "Verify secondary infrared feed on Sector 4 Watchtower.",
                    "Lock down Convoy Gate Beta access route.",
                ],
                ai_last_generated_at=datetime.datetime.now(datetime.timezone.utc),
                analyst_notes="QRT Alpha alerted. Drone surveillance requested for Sector 4 perimeter sweep.",
            )
            db.add(inc1)
            db.commit()
            db.refresh(inc1)

            event1 = SecurityEvent(
                event_type=EventType.RESTRICTED_ZONE_ENTRY.value,
                severity=SeverityLevel.CRITICAL.value,
                camera_id=cam1.id,
                incident_id=inc1.id,
                description="Target entered restricted buffer zone at [0.42, 0.58]",
                confidence=0.94,
                status="ACTIVE",
                metadata_json={
                    "tracking_id": 101,
                    "object_type": "person",
                    "zone_name": "High Security Buffer Strip",
                    "dwell_time_seconds": 18.4,
                },
            )
            event2 = SecurityEvent(
                event_type=EventType.LINE_CROSSING.value,
                severity=SeverityLevel.CRITICAL.value,
                camera_id=cam1.id,
                incident_id=inc1.id,
                description="Target crossed Perimeter Demarcation Line towards South",
                confidence=0.91,
                status="ACTIVE",
                metadata_json={
                    "tracking_id": 101,
                    "object_type": "person",
                    "line_name": "Perimeter Demarcation Line",
                    "direction": "NORTH_TO_SOUTH",
                },
            )
            db.add_all([event1, event2])
            db.commit()
            db.refresh(event1)
            db.refresh(event2)

            alert1 = Alert(
                event_id=event1.id,
                camera_id=cam1.id,
                incident_id=inc1.id,
                severity=SeverityLevel.CRITICAL.value,
                title="CRITICAL: Restricted Zone Intrusion",
                message="Target ID #101 penetrated High Security Buffer Strip (CAM-NP-01).",
                status=AlertStatus.NEW.value,
            )
            alert2 = Alert(
                event_id=event2.id,
                camera_id=cam1.id,
                incident_id=inc1.id,
                severity=SeverityLevel.CRITICAL.value,
                title="CRITICAL: Virtual Tripwire Breach",
                message="Demarcation Line breached in Sector 4 North (CAM-NP-01).",
                status=AlertStatus.NEW.value,
            )
            db.add_all([alert1, alert2])

            # Seed initial audit log
            audit = AuditLog(
                user_email="system@sentinel.ai",
                action="SYSTEM_INIT",
                resource_type="System",
                resource_id="1",
                details={"status": "Initialized baseline surveillance models and database schema"},
                ip_address="127.0.0.1",
            )
            db.add(audit)
            db.commit()
            print("  [+] Seeded Baseline Security Incident, Events, Alerts, and Audit Log")
        else:
            print("  [*] Cameras already seeded. Skipping camera seed.")

        print("Database seeding completed successfully!")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
