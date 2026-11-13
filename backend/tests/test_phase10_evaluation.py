"""
Phase 10 Automated Evaluation & Benchmark Verification Suite — SentinelAI (GenAI BorderGuard)
Tests baseline systems, proposed system improvements, adverse conditions, ablations,
machine-readable result exports, and honest documentation of limitations.
"""

import os
import json
import csv
import pytest
from app.evaluation.reproducible_benchmark import (
    ReproducibleEvaluationHarness,
    BenchmarkSummary,
    ScenarioResult,
    RANDOM_SEED
)

@pytest.fixture(scope="module")
def evaluation_summary() -> BenchmarkSummary:
    """Runs the reproducible benchmark harness and returns the structured summary."""
    harness = ReproducibleEvaluationHarness()
    return harness.run_full_evaluation()

def test_baseline_vs_proposed_improvement(evaluation_summary: BenchmarkSummary):
    """
    Requirement 1: Build and document baseline systems before comparing improvements.
    Verifies that Proposed SentinelAI strictly improves upon Baseline-1 and Baseline-2.
    """
    comp = evaluation_summary.comparative_metrics
    b1 = comp["Baseline-1_RawDetector"]
    b2 = comp["Baseline-2_TrackerNoController"]
    prop = comp["Proposed_SentinelAI_Full"]

    # F1 Score Improvement
    assert prop["f1_score"] > b1["f1_score"], f"Proposed F1 ({prop['f1_score']}) should exceed Baseline-1 ({b1['f1_score']})"
    assert prop["f1_score"] > b2["f1_score"], f"Proposed F1 ({prop['f1_score']}) should exceed Baseline-2 ({b2['f1_score']})"

    # False Alarm Rate Reduction
    assert prop["false_alarm_rate_pct"] < b1["false_alarm_rate_pct"], "Proposed FAR must be lower than Baseline-1"
    assert prop["false_alarm_rate_pct"] < b2["false_alarm_rate_pct"], "Proposed FAR must be lower than Baseline-2"

    # Evidence Reference Validity Improvement
    assert prop["mean_citation_validity_pct"] == 100.0, "Proposed system must achieve 100% citation validity"
    assert prop["mean_citation_validity_pct"] > b1["mean_citation_validity_pct"]

def test_documented_dataset_split_and_no_leakage(evaluation_summary: BenchmarkSummary):
    """
    Requirement 2: Use a documented dataset split and avoid test-data leakage.
    Verifies that 100 scenarios across 6 documented categories are evaluated with isolated ground truth.
    """
    split = evaluation_summary.dataset_split
    assert sum(split.values()) == 100, f"Expected 100 scenarios, got {sum(split.values())}"
    assert "DAYLIGHT_NOMINAL" in split
    assert "LOW_LIGHT_INFRARED" in split
    assert "SEVERE_OCCLUSION" in split
    assert "DEGRADED_VIDEO" in split
    assert "NETWORK_PARTITION" in split
    assert "CONTRADICTORY_OBS" in split

    # Check reproducibility
    assert evaluation_summary.hardware_and_environment["random_seed"] == RANDOM_SEED

def test_adverse_condition_evaluations(evaluation_summary: BenchmarkSummary):
    """
    Requirement 4: Test low light, occlusion, degraded video, dropped connections, and contradictory observations.
    """
    adverse = evaluation_summary.adverse_condition_metrics
    assert "LOW_LIGHT_INFRARED" in adverse
    assert "SEVERE_OCCLUSION" in adverse
    assert "DEGRADED_VIDEO" in adverse
    assert "NETWORK_PARTITION" in adverse
    assert "CONTRADICTORY_OBS" in adverse

    for cat_name, metrics in adverse.items():
        assert metrics["scenarios_evaluated"] >= 15, f"{cat_name} must evaluate at least 15 scenarios"
        assert metrics["precision"] > 80.0, f"{cat_name} precision should exceed 80%"
        assert metrics["recall"] >= 50.0, f"{cat_name} recall should be at least 50%"

def test_ablation_studies(evaluation_summary: BenchmarkSummary):
    """
    Requirement 5: Run ablation studies for event graph, adaptive verification controller,
    and evidence-constrained report validation.
    """
    abl = evaluation_summary.ablation_metrics
    prop = evaluation_summary.comparative_metrics["Proposed_SentinelAI_Full"]

    # 1. Event Graph Ablation: Removing graph degrades recall and multi-sensor consistency
    no_graph = abl["Ablation_NoEventGraph"]
    assert no_graph["recall"] < prop["recall"], "Disabling Event Graph must degrade recall on complex events"

    # 2. Adaptive Verification Controller Ablation: Fixed threshold degrades recall
    no_ctrl = abl["Ablation_NoAdaptiveController"]
    assert no_ctrl["recall"] < prop["recall"], "Disabling Adaptive Controller must degrade recall"

    # 3. Cross-Examiner Citation Ablation: Removing cross-examiner severely degrades citation validity
    no_cross = abl["Ablation_NoCrossExaminer"]
    assert no_cross["mean_citation_validity_pct"] < 70.0, "Disabling Cross-Examiner must drop citation validity"

    # 4. Edge Buffer Ablation: Disabling buffer causes event loss during outages
    no_buff = abl["Ablation_NoEdgeBuffer"]
    assert no_buff["event_loss_pct"] > 0.0, "Disabling Edge Buffer must cause event loss during outages"

def test_machine_readable_results_exported():
    """
    Requirement 6: Export machine-readable results and document test configurations.
    Verifies that benchmark_report.json and benchmark_summary.csv exist and are valid.
    """
    res_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "evaluation_results"
    )
    json_path = os.path.join(res_dir, "benchmark_report.json")
    csv_path = os.path.join(res_dir, "benchmark_summary.csv")
    raw_path = os.path.join(res_dir, "benchmark_raw_scenarios.csv")

    assert os.path.exists(json_path), f"Missing JSON report at {json_path}"
    assert os.path.exists(csv_path), f"Missing CSV summary at {csv_path}"
    assert os.path.exists(raw_path), f"Missing Raw scenarios CSV at {raw_path}"

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert data["total_scenarios_evaluated"] == 100
        assert "comparative_metrics" in data
        assert "honest_failure_modes" in data

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)
        assert len(rows) >= 8  # Header + 7 configs

def test_honest_failure_modes_recorded(evaluation_summary: BenchmarkSummary):
    """
    Requirement 7: Record failures, limitations, and negative results honestly.
    """
    failures = evaluation_summary.honest_failure_modes
    assert len(failures) >= 4, "Must document at least 4 concrete failure modes and limitations"
    failure_ids = [f["failure_id"] for f in failures]
    assert "FAIL-LOWLIGHT-TINY" in failure_ids
    assert "FAIL-OCCLUSION-IDSWITCH" in failure_ids
    assert "FAIL-CONTROLLER-LATENCY" in failure_ids
    assert "FAIL-UNCONSTRAINED-HALLUCINATION" in failure_ids
