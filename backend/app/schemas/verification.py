import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class VerificationVerdict(str, Enum):
    CONFIRMED = "CONFIRMED"
    REJECTED_NOISE = "REJECTED_NOISE"
    UNRESOLVED = "UNRESOLVED"
    FLAGGED_CONFLICT = "FLAGGED_CONFLICT"

class VerificationAction(str, Enum):
    DIRECT_VERIFY = "DIRECT_VERIFY"
    REQUEST_LOCAL_FRAMES = "REQUEST_LOCAL_FRAMES"
    REQUEST_GEMINI = "REQUEST_GEMINI"
    FLAG_CONFLICT = "FLAG_CONFLICT"
    MARK_UNRESOLVED = "MARK_UNRESOLVED"
    REJECT_NOISE = "REJECT_NOISE"

class VerificationConfig(BaseModel):
    high_confidence_threshold: float = Field(0.85, ge=0.0, le=1.0)
    marginal_threshold: float = Field(0.60, ge=0.0, le=1.0)
    min_track_frames: int = Field(3, ge=1)
    local_burst_frames: int = Field(5, ge=1)
    max_time_budget_ms: int = Field(2500, ge=100)
    max_gemini_calls_budget: int = Field(1, ge=0)
    max_frame_eval_budget: int = Field(15, ge=1)
    weight_detection_confidence: float = Field(0.40, ge=0.0, le=1.0)
    weight_track_continuity: float = Field(0.30, ge=0.0, le=1.0)
    weight_boundary_geometry: float = Field(0.20, ge=0.0, le=1.0)
    weight_conflict_penalty: float = Field(0.10, ge=0.0, le=1.0)

class DecisionLedgerEntry(BaseModel):
    step: int
    timestamp: datetime.datetime
    action: VerificationAction
    inputs: Dict[str, Any]
    reason: str
    evidence_gathered: List[str] = []
    outcome: str

class VerificationEvaluationResult(BaseModel):
    event_id: Optional[int] = None
    incident_id: Optional[int] = None
    verdict: VerificationVerdict
    confidence: float
    is_unresolved: bool
    is_conflict: bool
    frames_examined: int
    gemini_calls_made: int
    estimated_cost_usd: float
    total_time_ms: float
    decision_ledger: List[DecisionLedgerEntry]
    summary_explanation: str

class EvaluateEventRequest(BaseModel):
    event_id: int
    config: Optional[VerificationConfig] = None
    force_mock_gemini: bool = False

class BenchmarkRunRequest(BaseModel):
    dataset_name: str = "border_surveillance_benchmark_v1"
    fixed_sampling_interval: int = 5
    num_episodes: int = 20
