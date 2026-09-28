import os
from app.db.database import SessionLocal
from app.models.video import Video
from app.services.analytics_pipeline import AnalyticsPipelineService
from app.api.routes.videos import ingest_demo_video
from app.models.user import User

db = SessionLocal()
admin_user = db.query(User).filter(User.email == "admin@sentinel.ai").first()

print("Triggering demo surveillance ingestion...")
res = ingest_demo_video(demo_id="incursion", camera_id=1, db=db, current_user=admin_user)
print("DEMO INGESTION RESULT:", res["message"])
print("ANALYTICS:", res["analytics"])
print("PROCESSED VIDEO PATH:", res["video"].processed_path)
print("PROCESSED VIDEO EXISTS:", os.path.exists(res["video"].processed_path))

db.close()
