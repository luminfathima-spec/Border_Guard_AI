import datetime
from sqlalchemy.orm import Session
from app.core.logging import logger
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.camera import Camera, CameraStatus
from app.models.event import SecurityEvent, EventType, SeverityLevel
from app.models.alert import Alert, AlertStatus
from app.models.incident import Incident, IncidentStatus

def init_db(db: Session) -> None:
    """
    Ensures default administrative, analyst, and operator accounts are seeded with verified password hashes.
    Also initializes default border cameras and sample threat dossiers if table is empty.
    """
    # 1. Seed Users
    default_users = [
        {
            "name": "General Commander A. Sharma",
            "email": "admin@sentinel.ai",
            "password": "AdminPassword123!",
            "role": UserRole.ADMIN.value,
        },
        {
            "name": "Senior Analyst Priya Verma",
            "email": "analyst@sentinel.ai",
            "password": "AnalystPassword123!",
            "role": UserRole.SECURITY_ANALYST.value,
        },
        {
            "name": "Field Operator R. Singh",
            "email": "operator@sentinel.ai",
            "password": "OperatorPassword123!",
            "role": UserRole.OPERATOR.value,
        },
    ]

    for user_info in default_users:
        existing_user = db.query(User).filter(User.email == user_info["email"]).first()
        if not existing_user:
            user = User(
                name=user_info["name"],
                email=user_info["email"],
                password_hash=get_password_hash(user_info["password"]),
                role=user_info["role"],
                is_active=True,
            )
            db.add(user)
            logger.info(f"Seeded user: {user_info['email']} ({user_info['role']})")
        else:
            # Refresh password hash to ensure credentials match
            existing_user.password_hash = get_password_hash(user_info["password"])
            existing_user.is_active = True
            db.add(existing_user)

    db.commit()

    # 2. Seed Default Border Surveillance Cameras if empty
    camera_count = db.query(Camera).count()
    if camera_count == 0:
        default_cameras = [
            Camera(
                name="North Watchtower Post A-1",
                camera_identifier="CAM-NP-01",
                location="Sector 07 Northern Perimeter",
                zone="Sector 07 North",
                status=CameraStatus.ONLINE.value,
                latitude=34.1254,
                longitude=74.8321,
                restricted_zones=[
                    {
                        "id": "zone-1",
                        "name": "Primary Buffer Strip",
                        "polygon": [{"x": 10, "y": 20}, {"x": 80, "y": 20}, {"x": 80, "y": 70}, {"x": 10, "y": 70}],
                        "alert_severity": "CRITICAL",
                    }
                ],
                virtual_lines=[
                    {
                        "id": "line-1",
                        "name": "Demarcation Tripwire 01",
                        "p1": {"x": 15, "y": 40},
                        "p2": {"x": 75, "y": 40},
                        "direction": "BOTH",
                        "alert_severity": "HIGH",
                    }
                ],
            ),
            Camera(
                name="East Checkpoint Forward PTZ",
                camera_identifier="CAM-EB-02",
                location="Sector 04 Eastern Gate Outpost",
                zone="Sector 04 East",
                status=CameraStatus.ONLINE.value,
                latitude=34.1290,
                longitude=74.8410,
                restricted_zones=[],
                virtual_lines=[],
            ),
            Camera(
                name="Riverbed Crossing Thermal IR",
                camera_identifier="CAM-RB-03",
                location="Sector 09 Riverine Demarcation",
                zone="Sector 09 River",
                status=CameraStatus.ONLINE.value,
                latitude=34.1180,
                longitude=74.8210,
                restricted_zones=[],
                virtual_lines=[],
            ),
            Camera(
                name="South Valley Panoramic Sensor",
                camera_identifier="CAM-SV-04",
                location="Sector 07 South Ridge Outpost",
                zone="Sector 07 South",
                status=CameraStatus.ONLINE.value,
                latitude=34.1105,
                longitude=74.8150,
                restricted_zones=[],
                virtual_lines=[],
            ),
        ]
        for cam in default_cameras:
            db.add(cam)
        db.commit()
        logger.info("Seeded 4 default border surveillance camera nodes.")

    # 3. Seed Sample Incidents & Events if empty
    incident_count = db.query(Incident).count()
    if incident_count == 0:
        cam1 = db.query(Camera).filter(Camera.camera_identifier == "CAM-NP-01").first()
        cam_id = cam1.id if cam1 else 1

        inc1 = Incident(
            incident_number="INC-2026-0801",
            title="Restricted Buffer Zone Breach — Sector 07 Northern Perimeter",
            description="Computer Vision YOLOv8 engine detected unauthorized person crossing demarcation line into 150m restricted exclusion zone at 04:33 UTC.",
            severity=SeverityLevel.CRITICAL.value,
            status=IncidentStatus.OPEN.value,
            ai_summary="Target penetrated the 150m buffer zone at coordinates 34.1254N, 74.8321E with a deliberate westward trajectory. Threat velocity suggests coordinated border infiltration attempt. Quick Reaction Team (QRT) dispatched.",
            ai_recommendations=[
                "Deploy Quick Reaction Team patrol unit Alpha to Sector 07 North Ridge.",
                "Activate PTZ tracking zoom on CAM-NP-01 to maintain continuous visual vector.",
                "Notify border guard command outpost of active incursion status.",
            ],
            analyst_notes="Field patrol unit 4 confirmed intercept vector. Thermal drone dispatched to support visual tracking.",
        )
        db.add(inc1)
        db.commit()

        # Add sample event
        ev1 = SecurityEvent(
            event_type=EventType.RESTRICTED_ZONE_ENTRY.value,
            severity=SeverityLevel.CRITICAL.value,
            camera_id=cam_id,
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            description="Person target detected inside Sector 07 restricted buffer zone",
            confidence=0.96,
            incident_id=inc1.id,
        )
        db.add(ev1)

        # Add sample alert
        al1 = Alert(
            event_id=ev1.id,
            camera_id=cam_id,
            severity=SeverityLevel.CRITICAL.value,
            title="CRITICAL: Sector 07 Zone Incursion",
            message="Target crossed Tripwire 01-A into Northern Buffer Strip.",
            status=AlertStatus.NEW.value,
        )
        db.add(al1)
        db.commit()
        logger.info("Seeded initial incident dossier and security alerts.")
