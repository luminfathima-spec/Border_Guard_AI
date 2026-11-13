import re
import time
import json
import random
from typing import List, Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod

from app.core.config import settings
from app.core.logging import logger
from app.schemas.ai import IncidentAnalysisResponse, ObservedEventItem
from app.services.gemini.prompts import SYSTEM_INSTRUCTION

class BaseGeminiClient(ABC):
    @abstractmethod
    def generate_structured_analysis(
        self,
        prompt: str,
        images: Optional[List[bytes]] = None,
        system_instruction: Optional[str] = None,
    ) -> Tuple[IncidentAnalysisResponse, Dict[str, Any]]:
        """
        Executes structured generation returning an IncidentAnalysisResponse and call metadata.
        """
        pass

    @abstractmethod
    def ping_connectivity(self) -> Dict[str, Any]:
        """
        Verifies client connectivity and responsiveness.
        """
        pass


class RealGeminiClient(BaseGeminiClient):
    """
    Production client utilizing the official Google GenAI SDK (google-genai).
    Implements bounded exponential backoff retries on transient rate limits (429/503),
    timeout boundaries, secret sanitization, and strict Pydantic JSON schema response enforcement.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout_seconds: float = 30.0,
    ):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name or settings.GEMINI_MODEL
        self.timeout_seconds = timeout_seconds
        if not self.api_key or not self.api_key.strip():
            raise ValueError("GEMINI_API_KEY is not configured for RealGeminiClient.")

    def _sanitize_error(self, err_msg: str) -> str:
        """Strips secret API key if present in error message string."""
        if self.api_key and len(self.api_key.strip()) > 5:
            return err_msg.replace(self.api_key.strip(), "[REDACTED_API_KEY]")
        return err_msg

    @staticmethod
    def categorize_error(exc: Exception) -> str:
        """Classifies external Google API errors into semantic operational categories."""
        err_str = str(exc).lower()
        if "api_key_invalid" in err_str or "400" in err_str or "api key not valid" in err_str:
            return "INVALID_API_KEY"
        elif "403" in err_str or "permission" in err_str:
            return "PERMISSION_DENIED"
        elif "404" in err_str or "not found" in err_str:
            return "MODEL_NOT_FOUND"
        elif "429" in err_str or "resource_exhausted" in err_str or "quota" in err_str:
            return "QUOTA_EXCEEDED"
        elif "503" in err_str or "unavailable" in err_str:
            return "SERVICE_UNAVAILABLE"
        elif "timeout" in err_str or "timed out" in err_str:
            return "NETWORK_TIMEOUT"
        return "API_COMMUNICATION_ERROR"

    def ping_connectivity(self) -> Dict[str, Any]:
        """
        Executes a minimal test generation request to verify API key validity,
        network reachability, and model responsiveness.
        Never exposes the secret key in return values.
        """
        from google import genai
        from google.genai import types

        client = genai.Client(
            api_key=self.api_key,
            http_options=types.HttpOptions(timeout=int(self.timeout_seconds * 1000)),
        )
        start_time = time.time()
        try:
            response = client.models.generate_content(
                model=self.model_name,
                contents="Ping: SentinelAI surveillance engine connectivity check. Reply with ok.",
            )
            elapsed_ms = int((time.time() - start_time) * 1000)
            return {
                "status": "SUCCESS",
                "model_name": self.model_name,
                "response_text": (response.text or "").strip()[:50],
                "execution_time_ms": elapsed_ms,
                "is_live_success": True,
            }
        except Exception as e:
            category = self.categorize_error(e)
            sanitized_msg = self._sanitize_error(str(e))
            logger.error(f"Live Gemini connectivity ping failed ({category}): {sanitized_msg}")
            return {
                "status": "FAILED",
                "error_category": category,
                "message": sanitized_msg,
                "model_name": self.model_name,
                "is_live_success": False,
            }

    def generate_structured_analysis(
        self,
        prompt: str,
        images: Optional[List[bytes]] = None,
        system_instruction: Optional[str] = None,
    ) -> Tuple[IncidentAnalysisResponse, Dict[str, Any]]:
        from google import genai
        from google.genai import types

        client = genai.Client(
            api_key=self.api_key,
            http_options=types.HttpOptions(timeout=int(self.timeout_seconds * 1000)),
        )
        sys_inst = system_instruction or SYSTEM_INSTRUCTION

        # Build contents list (multimodal images + text prompt)
        contents: List[Any] = []
        if images:
            for img_bytes in images:
                contents.append(
                    types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg")
                )
        contents.append(prompt)

        config = types.GenerateContentConfig(
            temperature=0.2,
            top_p=0.95,
            max_output_tokens=2048,
            system_instruction=sys_inst,
            response_mime_type="application/json",
            response_schema=IncidentAnalysisResponse,
        )

        max_retries = 3
        backoff_base = 1.0
        start_time = time.time()
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                response = client.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                    config=config,
                )

                elapsed_ms = int((time.time() - start_time) * 1000)
                raw_text = response.text or "{}"

                # Defensively strip markdown JSON code fences if returned by model
                clean_text = raw_text.strip()
                if clean_text.startswith("```"):
                    clean_text = re.sub(r"^```(?:json)?\s*", "", clean_text)
                    clean_text = re.sub(r"\s*```$", "", clean_text)

                parsed_json = json.loads(clean_text)
                structured_obj = IncidentAnalysisResponse.model_validate(parsed_json)

                # Extract token usage if provided by API
                token_count = 0
                if hasattr(response, "usage_metadata") and response.usage_metadata:
                    token_count = getattr(response.usage_metadata, "total_token_count", 0) or 0

                metadata = {
                    "model_name": self.model_name,
                    "token_count": token_count,
                    "execution_time_ms": elapsed_ms,
                    "is_mock": False,
                    "raw_response_text": raw_text,
                }
                return structured_obj, metadata

            except Exception as e:
                last_error = e
                err_str = str(e).lower()
                is_transient = any(code in err_str for code in ["429", "503", "rate", "resource_exhausted", "unavailable"])
                sanitized_err = self._sanitize_error(str(e))
                if is_transient and attempt < max_retries:
                    sleep_sec = (backoff_base * (2 ** (attempt - 1))) + random.uniform(0.1, 0.5)
                    logger.warning(
                        f"Gemini API transient failure (attempt {attempt}/{max_retries}): {sanitized_err}. "
                        f"Retrying in {sleep_sec:.2f}s..."
                    )
                    time.sleep(sleep_sec)
                else:
                    logger.error(f"Gemini API fatal error on attempt {attempt}: {sanitized_err}", exc_info=True)
                    break

        sanitized_last_error = self._sanitize_error(str(last_error))
        raise RuntimeError(f"Google Gemini generation failed after {max_retries} attempts: {sanitized_last_error}")


class MockGeminiClient(BaseGeminiClient):
    """
    Deterministic mock provider for unit tests, local offline development,
    and CI environments where live Google Cloud credentials are not available.
    Extracts telemetry facts from prompt to generate realistic, grounded structured analysis.
    """

    def __init__(self, model_name: str = "mock-gemini-2.5-flash", inject_hallucination: bool = False):
        self.model_name = model_name
        self.inject_hallucination = inject_hallucination

    def ping_connectivity(self) -> Dict[str, Any]:
        """Returns mock operational connectivity status."""
        return {
            "status": "MOCK_ACTIVE",
            "model_name": self.model_name,
            "response_text": "mock-ok",
            "execution_time_ms": 1,
            "is_live_success": False,
            "is_mock": True,
        }

    def generate_structured_analysis(
        self,
        prompt: str,
        images: Optional[List[bytes]] = None,
        system_instruction: Optional[str] = None,
    ) -> Tuple[IncidentAnalysisResponse, Dict[str, Any]]:
        start_time = time.time()

        # Parse telemetry facts if embedded in markdown json block
        facts = {}
        json_match = re.search(r"```json\s*(\{.*?\})\s*```", prompt, re.DOTALL)
        if json_match:
            try:
                facts = json.loads(json_match.group(1))
            except Exception:
                facts = {}

        incident_number = facts.get("incident_number", "INC-TEST-001")
        severity = facts.get("severity", "HIGH")
        camera_id = facts.get("camera_id") or 1
        raw_events = facts.get("events", [])
        evidence_items = facts.get("evidence_items", [])

        # Build referenced lists
        referenced_camera_ids = [camera_id] if camera_id else [1]
        supporting_evidence_ids = [ev.get("id") for ev in evidence_items if isinstance(ev, dict) and "id" in ev]
        if not supporting_evidence_ids and "evidence_items_count" in facts and facts["evidence_items_count"] > 0:
            supporting_evidence_ids = [1]

        # Extract timestamps
        timestamps = [ev.get("timestamp") for ev in raw_events if isinstance(ev, dict) and "timestamp" in ev]
        if not timestamps:
            timestamps = [facts.get("created_at", "2026-08-30T04:33:00Z")]

        # Determine if telemetry is empty
        is_empty = (len(raw_events) == 0 and facts.get("events_count", 0) == 0)

        # Build observed event items
        observed_events = []
        for idx, ev in enumerate(raw_events):
            if isinstance(ev, dict):
                observed_events.append(
                    ObservedEventItem(
                        event_id=ev.get("id", idx + 1),
                        event_type=ev.get("type", "RESTRICTED_ZONE_ENTRY"),
                        timestamp=ev.get("timestamp", timestamps[0]),
                        confidence=float(ev.get("confidence", 0.95)),
                        description=ev.get("description", "Object trajectory confirmed crossing virtual boundary"),
                    )
                )

        if not observed_events and not is_empty:
            observed_events.append(
                ObservedEventItem(
                    event_id=1,
                    event_type="RESTRICTED_ZONE_ENTRY",
                    timestamp=timestamps[0],
                    confidence=0.96,
                    description=f"Automated CV detected perimeter crossing at {timestamps[0]}",
                )
            )

        # Handle injection of hallucination for test verification
        if self.inject_hallucination:
            referenced_camera_ids.append(99999)  # Nonexistent camera ID
            supporting_evidence_ids.append(88888)  # Nonexistent evidence ID

        if is_empty:
            response = IncidentAnalysisResponse(
                summary=f"Incident {incident_number} has insufficient sensor or telemetry data. No deterministic breach events were detected in the provided video segment.",
                observed_events=[],
                referenced_camera_ids=referenced_camera_ids,
                supporting_evidence_ids=[],
                timestamp_references=timestamps,
                uncertainty_and_conflicts=["Zero sensor detections recorded", "Footage interval contains no confirmed tracks"],
                suggested_human_actions=[
                    "Verify physical camera hardware and stream connectivity.",
                    "Review RAW sensor logs for undetected motion.",
                ],
                threat_level="LOW",
                insufficient_evidence=True,
            )
        else:
            response = IncidentAnalysisResponse(
                summary=(
                    f"Surveillance incident {incident_number} represents a confirmed {severity} threat. "
                    f"Computer vision analytics recorded sustained perimeter intrusion by unauthorized target(s). "
                    f"Visual evidence confirms deliberate trajectory across demarcation boundaries."
                ),
                observed_events=observed_events,
                referenced_camera_ids=referenced_camera_ids,
                supporting_evidence_ids=supporting_evidence_ids,
                timestamp_references=timestamps,
                uncertainty_and_conflicts=[
                    "Lighting conditions at 04:33 UTC introduce partial shadow ambiguity.",
                    "Target face partially obscured; biometric facial matching inconclusive."
                ],
                suggested_human_actions=[
                    "Dispatch Quick Reaction Team (QRT) to Sector perimeter coordinates.",
                    "Lock PTZ optics on target coordinate vector to monitor secondary movement.",
                    "Broadcast alert to adjacent border security watchtowers.",
                    "Secure forensic video clip and export tamper-evident hash to incident register."
                ],
                threat_level=severity if severity in ["LOW", "MEDIUM", "HIGH", "CRITICAL"] else "HIGH",
                insufficient_evidence=False,
            )

        elapsed_ms = int((time.time() - start_time) * 1000)
        metadata = {
            "model_name": self.model_name,
            "token_count": 450,
            "execution_time_ms": max(elapsed_ms, 12),
            "is_mock": True,
            "raw_response_text": response.model_dump_json(),
        }
        return response, metadata


def get_gemini_client(
    force_mock: bool = False,
    inject_hallucination: bool = False,
) -> BaseGeminiClient:
    """
    Factory function providing the appropriate Gemini client.
    Returns RealGeminiClient if GEMINI_API_KEY is configured and not force_mock,
    otherwise returns MockGeminiClient.
    """
    has_key = bool(settings.GEMINI_API_KEY and len(settings.GEMINI_API_KEY.strip()) > 5)
    if has_key and not force_mock:
        try:
            return RealGeminiClient()
        except Exception as e:
            logger.warning(f"Failed to instantiate RealGeminiClient ({e}), falling back to MockGeminiClient.")
            return MockGeminiClient(inject_hallucination=inject_hallucination)
    return MockGeminiClient(inject_hallucination=inject_hallucination)
