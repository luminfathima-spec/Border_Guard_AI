import requests

BASE_URL = "http://localhost:8000/api/v1"

def view_evidence():
    login_res = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "admin@sentinel.ai",
        "password": "AdminPassword123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = requests.get(f"{BASE_URL}/evidence", headers=headers)
    print("EVIDENCE API STATUS:", res.status_code)
    evs = res.json()
    print(f"Total Evidence Vault Items: {len(evs)}")
    for e in evs:
        print(f"  - [Evidence #{e['id']}] Type: {e['evidence_type']:<10} | Size: {e['file_size_bytes']:>6} bytes | SHA256: {e['checksum_sha256']}")
        print(f"    File: {e['file_path']}")
        print(f"    Metadata: {e.get('metadata_json', {})}")
        print(f"    Incident ID: {e.get('incident_id')} | Event ID: {e.get('event_id')}")
        print()

if __name__ == "__main__":
    view_evidence()
