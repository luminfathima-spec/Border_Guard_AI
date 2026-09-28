import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    user_email = Column(String(255), nullable=True)
    action = Column(String(100), nullable=False, index=True) # e.g. LOGIN, ACK_ALERT, UPDATE_INCIDENT, RUN_AI_SUMMARY
    resource_type = Column(String(50), nullable=True, index=True) # e.g. Alert, Incident, Camera
    resource_id = Column(String(50), nullable=True)
    details = Column(JSON, default=dict, nullable=False)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False, index=True)

    user = relationship("User", back_populates="audit_logs")
