# SentinelAI Research Document: Provenance-Aware Event Graph (EL-STEG)

**Document Identifier:** DOC-RES-08  
**Category:** Knowledge Representation & Forensic Provenance  
**Status:** Approved Research Specification  

---

## 1. Technical Problem Definition

Surveillance operations in high-stakes environments (such as national borders, critical infrastructure, and defense perimeters) suffer from a critical vulnerability known as **epistemic opacity**:

1. **Undifferentiated Epistemic Status**: Current Video Management Systems (VMS) and AI pipelines store alerts in flat, disconnected relational tables. When an alert arrives in a SOC console (or is consumed by a multimodal LLM), the system cannot distinguish between:
   - **Direct physical sensor observations**: e.g., "Bounding box $[x_1, y_1, x_2, y_2]$ detected at frame 142 ($t = 12.4\text{s}$) by Camera 04 with YOLO confidence 0.88".
   - **Inferred algorithmic associations**: e.g., "Track 104 on Camera 01 is hypothesized to be the same individual as Track 32 on Camera 02 based on visual re-identification heuristics".
   - **Analyst assertions**: e.g., "Operator tagged object as non-hostile maintenance personnel".
   - **AI synthetic summaries**: e.g., "Gemini hypothesized diversionary perimeter breach".

2. **Evidentiary Destruction via Silent Overwriting**: Traditional database schemas update incident or event rows in-place (e.g., updating `status = 'RESOLVED'` or overwriting `classification`). This destroys the historical audit trail and invalidates the legal chain of custody required for prosecution or official inquiry.

3. **Inability to Represent Negative and Conflicting Evidence**: Standard alert tables assume all recorded events are positive facts. In real border surveillance, critical insights come from **conflicting observations** (e.g., Radar detected movement at coordinate $C$, but thermal camera at $C$ observed zero heat signatures) and **missing evidence gaps** (e.g., 3-second RTSP frame drop during a suspected crossing). Current systems cannot formally represent or query these conditions.

4. **Dangling Evidence & Hallucination Propagation**: In downstream GenAI summarization, language models generate fluent tactical narratives that cite fictitious video frames or link unrelated persons. Without strict foreign-key verified graph topology, hallucinated citations cannot be deterministically refuted.

---

## 2. Design Alternatives & Trade-Off Analysis

| Dimension | Alternative A: Flat SQL Foreign Keys | Alternative B: Dedicated Graph Database (Neo4j / Neptune) | Alternative C (Selected): Relational Labeled Property Graph (LPG) in PostgreSQL |
| :--- | :--- | :--- | :--- |
| **Data Model** | Standard relational tables (`events`, `detections`, `videos`) | Property graph nodes and edges stored in native graph engine | Relational LPG using explicit edge table (`event_links`) & observation table (`evidence_observations`) |
| **Edge Metadata** | None (pure 1:N foreign keys) | High (arbitrary edge properties) | High (typed relationships, provenance mode, timestamps, confidence, creation reason, conflict flags) |
| **Multi-Hop Traversal** | Expensive multi-table joins | Native Cypher / graph traversal | PostgreSQL Recursive CTEs ($< 15\text{ms}$ over incident trees) |
| **Infrastructure Overhead** | Zero additional infrastructure | High (separate JVM/cluster, operational maintenance, backup divergence) | Zero additional infrastructure (uses existing PostgreSQL instance) |
| **Transactional Integrity** | Strong ACID | Weak across SQL-Graph boundary (dual-write sync vulnerabilities) | Strong ACID: unified transaction across video metadata, detections, events, and graph edges |
| **Referential Integrity** | Enforced by foreign keys | Application-managed or weak constraints | Strictly enforced via PostgreSQL foreign keys, check constraints, and service-level verification |
| **Suitability for Edge Nodes** | Suitable | Unsuitable for low-power edge nodes (Jetson, field servers) | Ideal: single SQLite/PostgreSQL binary |

**Decision**: Alternative C provides the expressive power of property graphs while maintaining strict ACID transactional consistency, microsecond query performance, and zero operational footprint expansion.

---

## 3. Prior Art Investigation & Defensive Boundary

To maintain defensive intellectual property boundaries and ensure non-infringement, prevailing standards and prior art were investigated:

### 3.1 Relevant Prior Art
1. **W3C PROV Data Model (PROV-DM / PROV-O)**:
   - Standardizes representation of provenance graphs (`Entity`, `Activity`, `Agent`, `wasDerivedFrom`, `wasAttributedTo`).
   - *SentinelAI differentiation*: PROV-O is designed for static documents and web resources. SentinelAI adapts provenance concepts specifically to **frame-level spatio-temporal video surveillance** with sub-second timestamps, camera geometry, and SHA-256 cryptographic media binding.
2. **MPEG-7 Multimedia Description Interface (ISO/IEC 15938)**:
   - Provides XML schemas for describing multimedia content, segment decomposition, and high-level visual features.
   - *SentinelAI differentiation*: MPEG-7 is a descriptive metadata container without causal reasoning, conflict resolution, or non-overwriting supersession logic.
3. **Video Scene Graphs (VSG) & Spatio-Temporal Action Graphs**:
   - Academic frameworks (e.g., Johnson et al., Action Genome) modeling objects and spatial predicates (`person-riding-bicycle`) per frame.
   - *SentinelAI differentiation*: VSGs model perceptual visual relations within a frame. SentinelAI models **forensic chain-of-custody and multi-modal causal inference** across cameras, physical sensors, human operators, and LLM reasoning engines.
4. **OpenLineage / Data Lineage**:
   - Data pipeline observability tracking datasets and job runs.
   - *SentinelAI differentiation*: Focuses on batch ETL jobs rather than real-time tactical edge security observations.

### 3.2 Defensive Boundary Statement
SentinelAI's provenance graph is not claimed as a novel fundamental graph theory. Rather, it represents an engineering realization of an **ACID-compliant, evidence-grounded provenance network** tailored for multi-sensor perimeter defense that eliminates epistemic opacity and prevents generative AI hallucination.

---

## 4. Measurable Research Hypotheses

### Hypothesis $H_{1,3}$: Forensic Chain-of-Custody Verification
* **Null Hypothesis ($H_{0,3}$)**: Tracking evidence provenance via an explicit event-link graph provides no measurable improvement in detecting manipulated, out-of-order, or fabricated video observations compared to standard relational event logs ($p \ge 0.01$).
* **Alternative Hypothesis ($H_{1,3}$)**: The provenance-aware event graph achieves **$100.0\%$ detection** of dangling evidence references, out-of-order timestamps, and duplicate claims, while resolving multi-tier evidence chains in $< 25\text{ms}$.

### Hypothesis $H_{1,5}$: Disputed & Negative Observation Representation
* **Null Hypothesis ($H_{0,5}$)**: Representing negative evidence (sensor gaps) and conflicting observations explicitly provides no reduction in operator triage confusion compared to standard binary alert streams.
* **Alternative Hypothesis ($H_{1,5}$)**: Explicit conflict modeling reduces contradictory dispatch decisions by $\ge 80\%$ by surfacing divergent sensor reports at the exact point of operator triage.
