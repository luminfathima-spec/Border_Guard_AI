# GenAI BorderGuard — Measurable Research Hypotheses & Experimental Protocols

**Document Identifier:** DOC-RES-05  
**Category:** Empirical Validation & Experimental Design  
**Status:** Approved Research Baseline  

---

## 1. Scientific Protocol & Hypothesis Formulation

To evaluate the engineering validity and practical efficacy of the **GenAI BorderGuard (SentinelAI)** architecture without making unsubstantiated claims of novelty or commercial superiority, this document defines four **measurable, falsifiable research hypotheses**.

Every hypothesis is framed under classical null-hypothesis significance testing (NHST), specifying:
- **Null Hypothesis ($H_0$)**: The default position that the proposed architectural mechanism exhibits no measurable performance advantage over established baselines.
- **Alternative Hypothesis ($H_1$)**: The specific, quantified performance improvement hypothesized by SentinelAI.
- **Independent & Dependent Variables**: Precise physical and computational metrics.
- **Experimental Testbed & Benchmark Datasets**: Controlled environments and video corpora.
- **Statistical Acceptance Thresholds**: Rejection criteria ($p$-values, effect sizes, and confidence intervals).

> [!NOTE]
> Testing these hypotheses does not assume novelty or patentability. Validation indicates whether the proposed architectural trade-offs achieve superior engineering characteristics (e.g., lower false alarm rates, zero hallucination, lower bandwidth, or deterministic recovery) under realistic border surveillance constraints.

---

## 2. Research Hypothesis 1: False Alarm Reduction via Adaptive Two-Tier Verification

### 2.1 Formal Formulation
* **Null Hypothesis ($H_{0,1}$)**: Cascaded Tier 1 edge computer vision (YOLOv8 + spatial geometry) coupled with on-demand Tier 2 multimodal verification (Google Gemini 2.5) yields no statistically significant reduction in False Alarm Rate (FAR) compared to a tuned baseline YOLOv8 detector ($p \ge 0.01$), or degrades the True Positive Rate (TPR) by more than $2.0\%$.
* **Alternative Hypothesis ($H_{1,1}$)**: The adaptive two-tier verification pipeline reduces the False Alarm Rate by $\ge 85.0\%$ ($p < 0.001$) under severe environmental noise (wind, rain, shadows, wildlife) while maintaining a True Positive Rate (TPR) $\ge 98.0\%$ of verified human intrusions, with a cloud bandwidth expenditure $\le 5.0\%$ of continuous video streaming.

### 2.2 Variables & Mathematical Metrics
* **Independent Variables**:
  - Verification Architecture: Baseline (YOLOv8x tuned threshold) vs. Proposed (YOLOv8n/s + Dynamic Threat Scorer $\Theta(t)$ + Google Gemini Tier 2).
  - Environmental Condition: Clear Day, Dawn/Dusk Glare, Nighttime IR, Moderate Fog, High Wind / Swaying Foliage.
* **Dependent Variables**:
  - False Alarm Rate:
    $$\text{FAR} = \frac{\text{False Positives (FP)}}{\text{Total Surveillance Hours (Camera-Hours)}} \quad [\text{alarms/camera-hour}]$$
  - True Positive Rate:
    $$\text{TPR} = \frac{\text{True Positives (TP)}}{\text{TP} + \text{False Negatives (FN)}} \times 100\%$$
  - Uplink Bandwidth Consumption: Mean kilobits per second ($\text{kbps}$) per camera stream.
  - End-to-End Alert Latency: Time $\Delta t$ from physical tripwire breach to final verified alert generation on the SOC console.

### 2.3 Experimental Protocol & Benchmark Corpora
* **Dataset**: 500 hours of continuous perimeter video containing:
  - 250 staged, ground-truth perimeter breaches (single person crawling, multi-person rush, vehicle approach, camouflaged crossing).
  - 250 hours of unbreached, high-noise ambient footage (wildlife herds, stray dogs, blowing trees, torrential rain, headlights).
* **Target Hardware**: Edge node: NVIDIA Jetson Orin AGX (32GB) / discrete RTX 4060; Cloud Hub: Google Gemini 2.5 Flash API via synthetic 512 kbps throttled uplink.
* **Acceptance Criteria**:
  - $\text{FAR}_{\text{proposed}} \le 0.15 \times \text{FAR}_{\text{baseline}}$
  - $\text{TPR}_{\text{proposed}} \ge 98.0\%$
  - Mean uplink bandwidth $\le 100\text{ kbps}$ per channel.
  - End-to-end latency for Tier 2 verified alert $\le 3.5\text{ seconds}$.

---

## 3. Research Hypothesis 2: Zero Hallucination via Constrained Telemetry Injection

### 3.1 Formal Formulation
* **Null Hypothesis ($H_{0,2}$)**: Conditioning Google Gemini on structured JSON telemetry facts and enforcing Pydantic output schema validation yields no statistically significant reduction in factual hallucination rate compared to standard multimodal visual question answering (VQA) prompting ($p \ge 0.01$).
* **Alternative Hypothesis ($H_{1,2}$)**: Structured telemetry injection coupled with an automated deterministic cross-examiner reduces the Factual Hallucination Rate for physical breach parameters (target count, breach timestamp, zone identifier, velocity) to strictly $0.0\%$ across 1,000 incident briefings, with $100\%$ of narrative factual assertions mapped directly to verified database telemetry nodes.

### 3.2 Variables & Mathematical Metrics
* **Independent Variables**:
  - Prompting Modality: Standard Multimodal Prompting (video clip + free-form prompt) vs. SentinelAI Grounded Telemetry Engine (structured facts JSON + keyframe + Pydantic schema + cross-examiner).
* **Dependent Variables**:
  - Factual Hallucination Rate (FHR):
    $$\text{FHR} = \frac{\sum_{k=1}^N \mathbb{I}(\exists \text{ factual claim in briefing } k \text{ not grounded in telemetry})}{\text{Total Briefings } N} \times 100\%$$
  - Grounding Citation Density: Proportion of generated assertions citing a valid, existing `EventID`:
    $$\text{GCD} = \frac{\sum \text{Validly Cited Assertions}}{\sum \text{Total Assertions}} \times 100\%$$
  - Analyst Triage Verification Time: Human review time (seconds) required to certify an incident report for command escalation.

### 3.3 Experimental Protocol
* **Test Corpus**: 1,000 simulated and real perimeter breach events across 10 distinct cameras with ground-truth structured database logs.
* **Evaluation Protocol**:
  - Automated regex and entity extraction parsing each output narrative for entity counts, camera IDs, timestamps, and action claims.
  - Double-blind human review by 3 security analysts evaluating 100 randomly sampled briefings for narrative accuracy and factual grounding.
* **Acceptance Criteria**:
  - $\text{FHR} \equiv 0.0\%$ (zero tolerated physical hallucinations in audited sample).
  - $\text{GCD} \ge 99.5\%$.
  - Human review time reduced by $\ge 60\%$ compared to reviewing raw unedited video.

---

## 4. Research Hypothesis 3: Tamper Detection & Forensic Integrity of EL-STEG

### 4.1 Formal Formulation
* **Null Hypothesis ($H_{0,3}$)**: Organizing multi-camera detection telemetry into an Evidence-Linked Spatio-Temporal Event Graph (EL-STEG) with SHA-256 hash chaining yields no difference in tamper detection sensitivity or forensic query latency compared to standard indexed relational SQL database logs.
* **Alternative Hypothesis ($H_{1,3}$)**: EL-STEG achieves $100.0\%$ detection of unauthorized frame substitutions, timestamp alterations, or coordinate modifications in forensic evidence packages, while reducing multi-camera breach trajectory reconstruction latency by $\ge 75.0\%$ ($> 4\times$ speedup) compared to relational multi-table SQL joins.

### 4.2 Variables & Mathematical Metrics
* **Independent Variables**:
  - Data Storage Paradigm: Relational Tables (PostgreSQL `detections` + `events` with foreign keys) vs. EL-STEG (PostgreSQL 17 recursive graph CTEs + SHA-256 hash chaining).
  - Tamper Injections: Single-pixel video keyframe modification, 1-second timestamp offset, trajectory coordinate alteration, or event deletion.
* **Dependent Variables**:
  - Tamper Detection Accuracy ($TDA$): Percentage of synthetic tampering attempts correctly identified by the integrity verifier.
  - Trajectory Traversal Latency: Wall-clock time ($\text{ms}$) to trace an individual target's complete path across 5 consecutive cameras over a 30-minute span.
  - Storage Overhead: Kilobytes per 1,000 recorded surveillance events.

### 4.3 Experimental Protocol
* **Test Dataset**: Synthetic 10-camera network generating 100,000 detection nodes and 5,000 multi-camera handover edges.
* **Adversarial Injections**: 500 controlled tamper attempts injected at random into the database:
  - 125 bit-flips in stored JPEG snapshots.
  - 125 modifications of bounding box telemetry in database rows.
  - 125 deletions of intermediate trajectory nodes.
  - 125 timestamp manipulations simulating backdated entries.
* **Acceptance Criteria**:
  - $TDA \equiv 100.0\%$ (zero undetected tamper instances).
  - Graph traversal query latency $\le 50\text{ms}$ for a 5-camera, 30-minute trajectory (vs. $\ge 200\text{ms}$ for baseline SQL joins).
  - Storage overhead $\le 300\text{ bytes}$ per graph node.

---

## 5. Research Hypothesis 4: Deterministic Convergence of Disconnected Event Graphs

### 5.1 Formal Formulation
* **Null Hypothesis ($H_{0,4}$)**: Reconciling edge event graphs after network outages using causal vector clocks and topological sorting yields an identical rate of duplicate alert generation and chronological state inversion as standard sequential FIFO HTTP message re-queuing ($p \ge 0.01$).
* **Alternative Hypothesis ($H_{1,4}$)**: Causal topological sort reconciliation achieves exactly $0\%$ event loss, $0$ duplicate incident alerts, and $0$ chronological inversions across simulated WAN blackouts ranging from 15 minutes to 72 hours, with full state convergence achieved within $< 30\text{ seconds}$ of network restoration over a 512 kbps uplink.

### 5.2 Variables & Mathematical Metrics
* **Independent Variables**:
  - Reconciliation Mechanism: Naive FIFO HTTP Queue Replay vs. SentinelAI Causal Topological Reconciler (Vector Clocks + Idempotent UPSERT).
  - Network Blackout Duration: $t_{\text{outage}} \in \{15\text{ min}, 1\text{ hour}, 6\text{ hours}, 24\text{ hours}, 72\text{ hours}\}$.
  - Uplink Restoration Bandwidth: Throttled at $256\text{ kbps}$, $512\text{ kbps}$, and $2\text{ Mbps}$.
* **Dependent Variables**:
  - Duplicate Alert Rate ($DAR$): Number of redundant alerts created for a single ongoing breach event upon reconnect.
  - Chronological Inversion Count ($CIC$): Number of events logged where child event timestamp precedes parent event timestamp.
  - Reconciliation Convergence Latency ($T_{\text{conv}}$): Total duration (seconds) until edge buffer is flushed and central database achieves full consistency.

### 5.3 Experimental Protocol
* **Testbed**: Edge node disconnected from network during active surveillance with continuous simulated intrusions (average 10 breaches/hour).
* **Fault Injection**: Random network dropouts with simulated packet loss ($5\%\text{–}20\%$) and latency jitter ($200\text{–}1500\text{ms}$).
* **Acceptance Criteria**:
  - $DAR \equiv 0$ duplicate alerts generated at central SOC.
  - $CIC \equiv 0$ causal inversions in the central event graph.
  - Data loss $\equiv 0.0\%$ (all edge WAL records successfully committed to PostgreSQL 17).
  - Convergence time $T_{\text{conv}} \le 30\text{ seconds}$ per 1,000 buffered events over $512\text{ kbps}$.

---

## 6. Summary: Research Hypotheses Overview Table

| Hypothesis | Mechanism | Target Metric | Baseline Comparison | Acceptance Threshold |
| :--- | :--- | :--- | :--- | :--- |
| **$H_1$** | Adaptive Two-Tier Verification | False Alarm Rate (FAR) | Single-tier YOLOv8x | $\ge 85\%$ FAR reduction; $\ge 98\%$ TPR; $< 100\text{ kbps}$ uplink |
| **$H_2$** | Constrained Grounding Engine | Factual Hallucination (FHR) | Zero-shot Multimodal VLM | $0.0\%$ physical hallucinations; $100\%$ fact citation |
| **$H_3$** | Evidence-Linked Event Graph | Tamper Detection & Query Speed | Relational SQL Indices | $100\%$ tamper detection; $\ge 4\times$ faster multi-camera traversal |
| **$H_4$** | Offline Graph Reconciliation | State Inversion & Duplicate Alerts | Sequential FIFO Replay | $0$ duplicates; $0$ inversions; $100\%$ zero-loss recovery |
