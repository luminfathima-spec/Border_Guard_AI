import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_ai_incident_summarization_and_chat():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Login
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": "admin@sentinel.ai",
            "password": "AdminPassword123!"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Get existing seeded incident
        incidents_res = await ac.get("/api/v1/incidents", headers=headers)
        assert incidents_res.status_code == 200
        incidents = incidents_res.json()
        assert len(incidents) >= 1
        target_incident_id = incidents[0]["id"]

        # 3. Request AI Summary
        summary_res = await ac.post(
            f"/api/v1/ai/incidents/{target_incident_id}/summarize",
            json={"custom_instructions": "Focus on high-threat sector 4 perimeter response."},
            headers=headers
        )
        assert summary_res.status_code == 200
        sum_data = summary_res.json()
        assert "ai_summary" in sum_data
        assert len(sum_data["ai_recommendations"]) >= 1
        assert "model_used" in sum_data

        # 4. Chat with AI Assistant
        chat_res = await ac.post(
            "/api/v1/ai/assistant/chat",
            json={
                "message": "Which cameras currently require immediate attention?",
                "conversation_history": []
            },
            headers=headers
        )
        assert chat_res.status_code == 200
        chat_data = chat_res.json()
        assert "response" in chat_data
        assert "suggested_actions" in chat_data

        # 5. Generate Incident Report Markdown
        report_res = await ac.post(
            f"/api/v1/ai/incidents/{target_incident_id}/report",
            headers=headers
        )
        assert report_res.status_code == 200
        report_data = report_res.json()
        assert "SENTINEL-AI SURVEILLANCE INCIDENT DOSSIER" in report_data["markdown_content"]
