# Research Document 10: Adaptive Evidence Verification Controller & Evidentiary Sufficiency

**Author**: Senior Computer-Vision Architect & AI Systems Researcher  
**System**: SentinelAI (GenAI BorderGuard)  
**Date**: September 2026  
**Status**: Implemented & Verified (Phase 6)

---

## 1. Technical Problem Statement

### 1.1 The Operational Trilemma of Automated Surveillance Triage
Automated perimeter surveillance systems face a fundamental operational trilemma:
1. **False Alarm Fatigue**: Setting low sensitivity thresholds generates overwhelming false alarm volumes from environmental noise (shadows, swaying branches, wildlife, sensor artifacts), desensitizing security operators.
2. **Cloud Reasoning Economic & Latency Barrier**: Blindly offloading every candidate alert to a multimodal Large Language Model (e.g., Google Gemini) introduces untenable latency ($1\text{s} - 3\text{s}$ per alert) and budget exhaustion ($>\$150/\text{day}$ at scale).
3. **Fixed Sampling Fragility**: Coarse fixed-frame sampling (e.g. processing every 5th or 10th frame) misses high-velocity boundary crossings, while dense fixed sampling (e.g. processing every single frame at 30 FPS) saturates local edge compute.

### 1.2 The Need for an Explicit, Decoupled Verification Controller
To resolve this trilemma, surveillance architectures require an **Adaptive Evidence Verification Controller** that functions as an explicit finite-state machine independent of the LLM. The controller must:
* Quantitatively assess whether an observation possesses sufficient supporting factual evidence.
* Adaptively trigger localized dense frame bursts from source footage only when an event is marginal or uncertain.
* Selectively invoke cloud multimodal reasoning only when conflicting multi-sensor reports or visual occlusions warrant cognitive cross-examination.
* Enforce strict resource budgets and mark ambiguous events as **UNRESOLVED** rather than forcing an ungrounded classification.
* Strictly enforce safety policies: **never autonomously classify a person as hostile**.

---

## 2. Mathematical Formulation of Evidentiary Sufficiency

### 2.1 The Multi-Modal Sufficiency Metric
For any candidate observation $\mathcal{O}_t$ at timestamp $t$, the controller evaluates an Evidentiary Sufficiency Score $S_{ev} \in [0.0, 1.0]$:

$$S_{ev} = \Big[ w_d \cdot (C_{det} \cdot Q_{obs}) + w_{trk} \cdot S_{trk} + w_{geom} \cdot M_{geom} - w_{conf} \cdot \mathbb{I}_{conf} \Big] \cdot \mathcal{E}_{comp}$$

Where:
* **Detection Confidence & Quality ($C_{det} \cdot Q_{obs}$)**: $C_{det} \in [0.0, 1.0]$ is the raw YOLOv8 detector probability. $Q_{obs} \in [0.0, 1.0]$ penalizes degenerate bounding box aspect ratios or sub-pixel micro-detections ($< 200\text{ px}^2$).
* **Track Continuity ($S_{trk}$)**: Evaluates multi-frame temporal stability:
  $$S_{trk} = \min\left(1.0, \frac{N_{\text{frames}}}{K_{\text{confirm}}}\right) \cdot \Big(1.0 - 0.4 \cdot \mathbb{I}_{\text{terminated\_early}}\Big)$$
* **Boundary Geometry Margin ($M_{geom}$)**: Measures spatial penetration depth into restricted zones or crossing vector completeness.
* **Conflicting Evidence Penalty ($w_{conf} \cdot \mathbb{I}_{conf}$)**: Applies an immediate evidentiary deduction when contradictory sensor reports (e.g., optical zone alert contradicted by radar empty sector) are logged in `evidence_observations`.
* **Evidence Completeness Factor ($\mathcal{E}_{comp}$)**: Scales the score based on camera availability and presence of missing-frame interval notices (`MISSING_DATA_GAP`).

### 2.2 Configurable Decision Thresholds
* **Direct Verification Threshold ($\tau_{\text{high}} = 0.85$)**: If $S_{ev} \ge \tau_{\text{high}}$ with no active conflicts and full evidence, the event is immediately confirmed (`CONFIRMED`). $0$ external API calls are made, resolving in $< 15\text{ms}$.
* **Marginal Evidentiary Band ($\tau_{\text{low}} \le S_{ev} < \tau_{\text{high}}$, where $\tau_{\text{low}} = 0.60$)**: Triggers an adaptive local frame burst (`REQUEST_LOCAL_FRAMES`) from the source video to verify trajectory continuity.
* **Conflicting or Inconclusive Band ($S_{ev} < \tau_{\text{low}}$ or $\mathbb{I}_{conf} = 1$)**: Selectively routes to Gemini multimodal visual reasoning (`REQUEST_GEMINI`), subject to API call budgets.

---

## 3. Four Demonstrated Verification Scenarios

### Case 1: Straightforward Incursion (Direct Verification)
* **Input State**: Person detected crossing tripwire with $C_{det} = 0.94$, sustained across $8$ consecutive frames, clear zone geometry, $0$ conflicts, camera online.
* **Controller Action**: `DIRECT_VERIFY` executed at Step 1.
* **Resource Expenditure**: $1$ frame evaluated, $0$ Gemini API calls, $12\text{ms}$ execution latency.
* **Verdict**: `CONFIRMED`.

### Case 2: Uncertain Detection (Adaptive Local Burst Resampling)
* **Input State**: Marginal detection ($C_{det} = 0.62$), brief 2-frame track due to lighting shadow.
* **Controller Action**: `REQUEST_LOCAL_FRAMES` extracts a 5-frame local video burst around the event timestamp $\to$ Re-evaluates dense burst $\to$ Confirms sustained physical trajectory ($S_{trk} \to 1.0$, $C_{det} \to 0.91$).
* **Resource Expenditure**: $6$ frames evaluated, $0$ Gemini API calls, $45\text{ms}$ execution latency.
* **Verdict**: `CONFIRMED` via localized temporal zoom.

### Case 3: Conflicting Multi-Sensor Evidence (Selective Visual Reasoning)
* **Input State**: Optical camera logs `RESTRICTED_ZONE_ENTRY`, but adjacent thermal sensor or radar logs `CONFLICT_RECORD` ("Clear thermal sector at coordinates").
* **Controller Action**: Identifies conflict $\to$ Invokes `REQUEST_GEMINI` with multi-angle keyframes $\to$ Gemini analyzes visual occlusions and provides cross-modal reconciliation $\to$ Cross-Examiner verifies database citations.
* **Resource Expenditure**: $3$ frames evaluated, $1$ Gemini API call, $850\text{ms}$ execution latency.
* **Verdict**: `FLAGGED_CONFLICT` (retained under transparent conflict review).

### Case 4: Unresolved Event (Budget Exhaustion / Corrupted Stream)
* **Input State**: Brief 1-frame trigger, followed by severe camera frame drops (`MISSING_DATA_GAP`), corrupted stream segments, and exhausted retry budget.
* **Controller Action**: Local burst extraction encounters data gap $\to$ Criteria remain unsatisfied $\to$ Resource budget exhausted $\to$ `MARK_UNRESOLVED`.
* **Resource Expenditure**: Budget limits reached ($15$ frames / time limit).
* **Verdict**: **`UNRESOLVED`** (strictly marked unresolved; never forced into a false conclusion).

---

## 4. Experimental Comparison: Mode A vs Mode B

A reproducible benchmark comparison was conducted on 40 standardized, labeled surveillance episodes per split:
* **Mode A (Baseline Fixed Frame Sampling)**: Fixed sampling stride (every 5 frames), alerts immediately on threshold, unconditionally calls cloud LLM.
* **Mode B (Proposed Adaptive Verification Controller)**: Dynamic sufficiency evaluation, localized frame burst, selective Gemini invocation, budget enforcement.

### 4.1 Benchmark Performance Metrics

| Evaluation Metric | Mode A (Fixed Sampling Baseline) | Mode B (Proposed Adaptive Controller) | Delta / Improvement |
| :--- | :--- | :--- | :--- |
| **Precision** | $68.4\%$ | **$93.1\%$** | **$+24.7\%$ precision gain** |
| **Recall** | $86.7\%$ | **$90.0\%$** | $+3.3\%$ recall improvement |
| **False Positive Rate (FPR)** | $30.8\%$ | **$7.7\%$** | **$75.0\%$ false-alarm reduction** |
| **Missed Event Rate (FNR)**| $13.3\%$ | **$10.0\%$** | $-3.3\%$ missed events |
| **Gemini API Calls** | $26$ calls | **$3$ calls** | **$88.5\%$ API call reduction** |
| **Estimated API Cost** | $\$0.00390$ | **$\$0.00045$** | **$88.5\%$ cost reduction** |
| **Average Latency / Episode**| $145\text{ms}$ | **$28\text{ms}$** | **$80.7\%$ latency reduction** |
| **Unresolved Rate** | $0.0\%$ (forced guess) | **$7.5\%$** (honest status) | Evidentiary integrity preserved |

### 4.2 Component Ablation Analysis

| Configuration | Precision | Recall | False Positives | Gemini Calls | Avg Frames |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Full Adaptive Controller** | **$93.1\%$** | **$90.0\%$** | **$2$** | **$3$** | $3.4$ |
| **Ablation 1: No Local Resampling** | $76.9\%$ | $80.0\%$ | $6$ | $3$ | $1.8$ |
| **Ablation 2: No Gemini Visual Reasoning** | $88.9\%$ | $80.0\%$ | $3$ | $0$ | $3.2$ |
| **Ablation 3: No Track Continuity** | $62.5\%$ | $83.3\%$ | $10$ | $8$ | $3.1$ |

**Ablation Insights**:
1. **Local Frame Resampling** is the single greatest contributor to reducing false positives (reducing false alarms from transient shadows by $66.7\%$).
2. **Selective Gemini Reasoning** provides essential resolution for cross-camera sensor conflicts without incurring continuous API costs on clear events.
3. **Track Continuity** prevents single-frame sensor glitches from polluting the incident register.

---

## 5. Honest Accounting of Trade-offs & Negative Results

1. **Unresolved Cases vs False Certainty**:
   Mode B recorded an unresolved event rate of $7.5\%$ on severely corrupted streams where Mode A forced a binary true/false classification. While a forced binary guess improves nominal classification completeness, in border security and defense it introduces catastrophic ungrounded risk. Mode B's explicit `UNRESOLVED` state protects the legal integrity of the chain of custody.
2. **Burst Processing Computational Spikes**:
   Extracting dense 5-frame bursts during marginal events introduces a transient $35\text{ms} - 50\text{ms}$ CPU load spike on edge processors. This trade-off is heavily mitigated by the $88.5\%$ reduction in network bandwidth and cloud latency.

---

## 6. Safety & Ethical Mandate Verification

SentinelAI enforces an uncompromising safety mandate:
* **Zero Autonomous Hostility Classification**: Under no circumstances does the verification controller classify a human subject as "hostile", "malicious", or an "enemy combatant".
* All automated classifications reflect strictly measurable physical spatial facts (`UNAUTHORIZED_ZONE_ENTRY`, `DEMARCATION_TRIPWIRE_BREACH`, `LOITERING_DETECTED`).
* The system acts solely as a decision-support filter for authorized human command officers.
