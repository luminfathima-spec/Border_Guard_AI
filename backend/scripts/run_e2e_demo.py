import os
import sys
import requests

BASE_URL = "http://localhost:8000/api/v1"

def test_full_video_demonstration():
    print("--- 1. Testing Login ---", flush=True)
    login_res = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "admin@sentinel.ai",
        "password": "AdminPassword123!"
    })
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("[OK] Login successful, JWT token obtained.", flush=True)

    print("\n--- 2. Testing List Demo Scenarios ---", flush=True)
    demos_res = requests.get(f"{BASE_URL}/videos/demos", headers=headers)
    assert demos_res.status_code == 200, f"Get demos failed: {demos_res.text}"
    demos = demos_res.json()
    assert len(demos) >= 2, "Expected at least 2 demo scenarios"
    print(f"[OK] Found {len(demos)} pre-packaged demo scenarios:", flush=True)
    for d in demos:
        print(f"  - [{d['id']}] {d['title']} ({d['duration_seconds']}s, {d['resolution']})", flush=True)

    print("\n--- 3. Testing Ingest & Process Demo Scenario ---", flush=True)
    ingest_res = requests.post(
        f"{BASE_URL}/videos/demo/ingest",
        data={"demo_id": "incursion", "camera_id": 1},
        headers=headers
    )
    assert ingest_res.status_code == 200, f"Ingest failed: {ingest_res.text}"
    ingest_data = ingest_res.json()
    video_info = ingest_data["video"]
    analytics = ingest_data["analytics"]
    print(f"[OK] Demo Ingestion Result: {ingest_data['message']}", flush=True)
    print(f"  - Video ID: {video_info['id']}", flush=True)
    print(f"  - Status: {video_info['status']}")
    print(f"  - Processed URL: {video_info['processed_url']}", flush=True)
    print(f"  - Total Detections: {analytics['total_detections']}", flush=True)
    print(f"  - Tracked Objects: {analytics['tracked_objects']}", flush=True)
    print(f"  - Generated Events: {analytics['generated_events']}", flush=True)
    print(f"  - Created Incident: {analytics['incident_created']}", flush=True)

    print("\n--- 4. Testing Processed Video Static HTTP Availability ---", flush=True)
    processed_url = f"http://localhost:8000{video_info['processed_url']}"
    media_res = requests.get(processed_url, stream=True)
    assert media_res.status_code == 200, f"Processed video stream unreachable: {media_res.status_code}"
    content_type = media_res.headers.get("Content-Type", "")
    print(f"[OK] Processed Video Stream verified (Status 200 OK, Content-Type: {content_type}, Length: {media_res.headers.get('Content-Length', 'chunked')} bytes)", flush=True)

    print("\n--- 5. Testing Incident Register Integration ---", flush=True)
    incidents_res = requests.get(f"{BASE_URL}/incidents", headers=headers)
    assert incidents_res.status_code == 200, "Failed to get incidents"
    incidents = incidents_res.json()
    print(f"[OK] Active Incidents in DB: {len(incidents)}", flush=True)
    latest_incident = incidents[0]
    print(f"  - Latest Incident Number: {latest_incident['incident_number']}", flush=True)
    print(f"  - Title: {latest_incident['title']}", flush=True)
    print(f"  - Severity: {latest_incident['severity']}", flush=True)
    print(f"  - Status: {latest_incident['status']}", flush=True)

    print("\n--- 6. Testing Security Events Audit Ledger ---", flush=True)
    events_res = requests.get(f"{BASE_URL}/events", headers=headers)
    assert events_res.status_code == 200, "Failed to get events"
    events = events_res.json()
    print(f"[OK] Security Events in Audit Ledger: {len(events)}", flush=True)
    breach_event = next((e for e in events if e.get("event_type") == "RESTRICTED_ZONE_ENTRY"), None)
    if breach_event:
        print(f"  - Verified Breach Event: {breach_event['event_type']} (Severity: {breach_event['severity']}, Confidence: {int(breach_event['confidence']*100)}%)", flush=True)

    print("\n========================================================", flush=True)
    print("ALL REAL VIDEO DEMO PIPELINE TESTS PASSED WITH 100% SUCCESS!", flush=True)
    print("========================================================", flush=True)

if __name__ == "__main__":
    test_full_video_demonstration()
