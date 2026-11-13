import re
import json
from typing import Dict, Any, Optional

PROMPT_VERSION = "2026.04.1"

SYSTEM_INSTRUCTION = (
    "You are the SentinelAI Cognitive Reasoning Officer, an elite military border surveillance "
    "intelligence analysis system. Your operational duty is to analyze deterministic computer-vision "
    "detections, tracking telemetry, and keyframe visual evidence to synthesize a rigorous tactical assessment.\n\n"
    "CRITICAL OPERATIONAL RULES:\n"
    "1. ABSOLUTE GROUNDING: You must cite ONLY the Camera IDs, Evidence IDs, and Security Event IDs "
    "explicitly provided in the input telemetry. Never invent, hallucinate, or extrapolate nonexistent IDs.\n"
    "2. EPISTEMIC ISOLATION: Clearly distinguish between measured physical sensor detections (tripwire crossings, "
    "zone intrusions, track coordinates) and your generative cognitive threat inferences.\n"
    "3. HONEST UNCERTAINTY: If footage is occluded, lighting is poor, or telemetry contains gaps, record these "
    "explicitly in 'uncertainty_and_conflicts'. If visual or sensor evidence is insufficient to verify the threat, "
    "set 'insufficient_evidence': true.\n"
    "4. TACTICAL DIRECTNESS: Provide 3-4 actionable, prioritized SOP recommendations for Quick Reaction Teams (QRT).\n"
    "5. SCHEMA ENFORCEMENT: Your output must strictly conform to the required JSON schema."
)

def sanitize_telemetry(facts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enforces privacy, operational security, and data retention policies by sanitizing
    external LLM payloads:
    - Strips RTSP passwords and database connection strings.
    - Masks potential operator PII or internal IP addresses.
    - Retains only forensic event telemetry, timestamps, and camera identifiers.
    """
    sanitized = json.loads(json.dumps(facts))  # Deep copy

    def clean_strings(obj: Any) -> Any:
        if isinstance(obj, str):
            # Mask RTSP credentials
            obj = re.sub(r"://([^:]+):([^@]+)@", r"://\1:****@", obj)
            # Mask authorization bearer tokens
            obj = re.sub(r"Bearer\s+[A-Za-z0-9_\-\.]+", "Bearer ****", obj)
            # Mask potential passwords or tokens
            obj = re.sub(r"(?i)(password|secret|token)\s*[:=]\s*['\"]?[^\s'\"]+['\"]?", r"\1: ****", obj)
            return obj
        elif isinstance(obj, dict):
            return {k: clean_strings(v) for k, v in obj.items() if not k.lower().endswith(("_hash", "secret", "password"))}
        elif isinstance(obj, list):
            return [clean_strings(item) for item in obj]
        return obj

    return clean_strings(sanitized)


def build_incident_prompt(facts: Dict[str, Any], custom_instructions: Optional[str] = None) -> str:
    """
    Assembles a versioned prompt combining sanitized structured telemetry facts and operator notes.
    """
    sanitized_facts = sanitize_telemetry(facts)
    instructions_str = custom_instructions.strip() if custom_instructions else "Provide rapid perimeter breach tactical assessment."

    prompt = f"""[SENTINEL-AI INCIDENT TELEMETRY DOSSIER - PROMPT_VERSION: {PROMPT_VERSION}]

Below is the verified, immutable surveillance telemetry recorded by local computer-vision and edge sensors:

```json
{json.dumps(sanitized_facts, indent=2)}
```

OPERATOR INSTRUCTIONS:
{instructions_str}

MANDATORY RESPONSE REQUIREMENTS:
1. Synthesize an objective tactical executive summary in 'summary'.
2. List all observed events in 'observed_events' with exact timestamp, type, and description.
3. In 'referenced_camera_ids', include ONLY the integer Camera IDs present in the input telemetry.
4. In 'supporting_evidence_ids', include ONLY the integer Evidence IDs present in the input telemetry.
5. In 'timestamp_references', cite the specific timestamps matching the observed telemetry.
6. In 'uncertainty_and_conflicts', document any occlusions, sensory ambiguities, or missing evidence intervals.
7. In 'suggested_human_actions', provide 3 to 4 prioritized, actionable recommendations.
8. Set 'threat_level' to LOW, MEDIUM, HIGH, or CRITICAL.
9. If data is inconclusive, set 'insufficient_evidence': true.
"""
    return prompt.strip()
