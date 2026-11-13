# GenAI BorderGuard — Innovation Comparison Matrix

**Document Identifier:** DOC-RES-04  
**Category:** Comparative Technical & Architectural Analysis  
**Status:** Approved Research Baseline  

---

## 1. Overview & Comparative Framing

This document provides a comparative analysis of the four core architectural mechanisms proposed for **GenAI BorderGuard (SentinelAI)** against prevailing industry conventions and state-of-the-art (SOTA) academic baselines.

Each mechanism is evaluated across seven rigorous technical dimensions:
1. **Mathematical / Algorithmic Formulation**: Formal definition of data structures, state machines, and algorithms.
2. **Conventional / SOTA Approach**: How standard commercial VMS or academic pipelines solve the problem today.
3. **Proposed Architecture**: The specific design implemented in SentinelAI.
4. **Hypothesized Technical Advantage**: Measurable operational or computational improvements.
5. **Known Failure Modes & Boundary Limitations**: Edge cases where the mechanism degrades or fails.
6. **Computational & Storage Overhead**: Resource consumption profile (Edge CPU/GPU vs. Cloud/Hub).
7. **Prior Art Overlap Risk & Differentiation Boundary**: Intellectual property clearance status and defensive boundaries.

---

## 2. Comprehensive Comparison Matrix

### 2.1 Mechanism 1: Evidence-Linked Spatio-Temporal Event Graphs (EL-STEG)

| Dimension | Specification |
| :--- | :--- |
| **Mathematical / Data-Structure Formulation** | Directed Acyclic Graph $\mathcal{G} = (\mathcal{V}, \mathcal{E}, \mathcal{H})$:<br>• $\mathcal{V} = \{v_i\}$ where $v_i = (\text{track\_id}, \text{camera\_id}, t_i, (x, y, w, h)_{\text{norm}}, \text{event\_type}, \vec{v}_i)$<br>• $\mathcal{E} = \{e_{ij} = (v_i, v_j, \Delta t, \Delta \vec{x}, P_{\text{assoc}})\}$ capturing spatial transition & handover probability<br>• $\mathcal{H}: \mathcal{V} \to \{0, 1\}^{256}$ where $\mathcal{H}(v_i) = \text{SHA256}(\text{Telemetry}(v_i) \parallel \text{Hash}(\text{Keyframe}_i) \parallel \text{Hash}(\text{Clip}_i) \parallel \mathcal{H}(v_{i-1}))$ |
| **Conventional / SOTA Approach** | Flat relational tables in SQL (e.g., `detections` table, `events` table) or timeseries indices (Elasticsearch/InfluxDB). Video media stored in disparate directory structures; no internal cryptographic chaining across temporal state changes. |
| **Proposed SentinelAI Architecture** | Multi-camera graph engine maintaining an in-memory active DAG persisted to PostgreSQL 17 JSONB / recursive CTEs. Every state transition (zone entry, loiter inflection, cross-camera handover) creates an immutable, cryptographically chained node bound to raw media hashes. |
| **Hypothesized Technical Advantage** | • **Zero-gap forensic timeline**: Instant multi-camera path traversal with $O(\log |\mathcal{V}|)$ query complexity.<br>• **Legal Chain of Custody**: Cryptographic mathematical proof that video frames and event telemetry have not been tampered with or retroactively forged. |
| **Known Failure Modes & Limitations** | • High ID switch rates in crowded scenes lead to fragmented or chimeric graphs.<br>• Clock drift across unsynchronized edge camera NTP servers can produce backward-pointing or cyclical edges.<br>• Large storage footprint if dense frame-by-frame nodes are maintained without pruning. |
| **Overhead (Edge vs. Hub)** | • **Edge**: Negligible compute ($< 2\text{ms}$ per event node insertion, SHA-256 computed on FFmpeg extract).<br>• **Hub**: Moderate memory for active graphs ($\sim 1.5\text{MB}$ per active incident graph); database storage $\approx 250\text{ bytes}$ per graph node. |
| **Prior Art Overlap Risk** | **MEDIUM**: Scene graphs and video event graphs are well-studied in academic literature (e.g., CVPR video scene graph benchmarks).<br>**Differentiation Boundary**: The coupling of *spatio-temporal tracking graph topology* directly with *microsecond cryptographic hash chains* bound to isolated FFmpeg video slices for legally admissible chain-of-custody. |

---

### 2.2 Mechanism 2: Adaptive Two-Tier Multimodal Verification Architecture

| Dimension | Specification |
| :--- | :--- |
| **Mathematical / Data-Structure Formulation** | Tiered decision function with dynamic threat scoring:<br>• **Tier 1 (Edge)**: $\forall \text{frame } f_t, \quad \mathcal{D}(f_t) \to \{(b_k, c_k, p_k)\}$; Spatial logic computes instant threat index $\Theta(t) = w_1 \cdot \text{ZoneWeight} + w_2 \cdot \text{Speed}(t) + w_3 \cdot \text{Dwell}(t) + w_4 \cdot (1 - p_{\text{animal}})$<br>• **Dispatch Gate**: Trigger Tier 2 if $\Theta(t) \ge \tau_{\text{threat}}$ AND $\text{Bandwidth}_{\text{avail}} \ge \beta_{\min}$<br>• **Tier 2 (Cloud / Gemini)**: Multimodal verification $M(\text{Telemetry}(t), \text{Keyframe}_t) \to (\text{Veracity} \in \{\text{TRUE}, \text{FALSE}\}, \text{Confidence}, \text{ThreatAssessment})$ |
| **Conventional / SOTA Approach** | • *Paradigm A*: Pure edge CV running YOLO/SSD with static confidence thresholds (high false alarm rate due to weather, animals, shadows).<br>• *Paradigm B*: Streaming raw RTSP video to cloud VLM APIs (catastrophically bandwidth-prohibitive, expensive, and latency-intolerant over satellite). |
| **Proposed SentinelAI Architecture** | Continuous edge inference handles 100% of frames locally (YOLOv8 + ByteTrack). Only when an ambiguous, high-salience threat boundary is crossed does the edge node formulate a compact JSON telemetry packet and extract a high-contrast keyframe slice to dispatch to Google Gemini 2.5 Flash / Pro. |
| **Hypothesized Technical Advantage** | • $> 90\%$ reduction in non-actionable false alarms (filtering deer, blowing tarps, lens spiders).<br>• $> 98\%$ reduction in cloud API and satellite bandwidth costs compared to continuous streaming.<br>• Average verification latency $< 3.5\text{s}$ over low-bandwidth uplinks. |
| **Known Failure Modes & Limitations** | • If Tier 1 suffers a False Negative (missed detection due to heavy camouflage or sensor glare), Tier 2 is never triggered.<br>• Latency spikes (3–10s) if satellite uplink experiences high jitter or packet loss.<br>• Edge throttle saturation during coordinated multi-point perimeter breaches. |
| **Overhead (Edge vs. Hub)** | • **Edge**: High local GPU utilization ($15\text{–}30\text{ FPS}$ on embedded hardware); uplink bandwidth $< 100\text{ kbps}$ average (only telemetry + occasional 150KB JPEG dispatched).<br>• **Cloud/Hub**: Pay-per-token API invocation only during genuine breach events. |
| **Prior Art Overlap Risk** | **MEDIUM-HIGH**: Cascaded edge-cloud video systems are known (e.g., Microsoft *Rocket*, Stanford *NoScope*, MIT *Focus*).<br>**Differentiation Boundary**: Dynamic threat score $\Theta(t)$ driven specifically by perimeter spatial geometry and loitering vectors, combined with *structured-telemetry-conditioned multimodal LLM verification* rather than simple deep CNN classifiers. |

---

### 2.3 Mechanism 3: Formally Constrained Evidence-Grounded Reporting

| Dimension | Specification |
| :--- | :--- |
| **Mathematical / Data-Structure Formulation** | Constrained Generative Decoder with Grounding Verification:<br>• **Input Fact Tuple**: $\mathcal{F} = \langle \text{EventID}, \text{Timestamp}, \text{CameraID}, \text{Class}, \text{Zone}, \text{BBox}_{\text{norm}}, \text{Velocity}, \text{SHA256} \rangle$<br>• **Strict Pydantic Generation Schema**: Output must validate against $\mathcal{S}_{\text{TacticalReport}}$ requiring field-level citations: $A_k = (\text{AssertionText}, \text{CitedEventIDs} \subseteq \{\text{EventID}_i\})$<br>• **Automated Cross-Examiner Verification**: $\forall e \in \text{CitedEventIDs}, \quad \text{ExistsInDB}(e) \equiv \text{TRUE}$; If any cited coordinate, timestamp, or entity has no supporting fact $\mathcal{F}$, raise `GROUNDING_VIOLATION_EXCEPTION`. |
| **Conventional / SOTA Approach** | Free-form natural language prompting (e.g., *"Summarize the threat from this video"*). LLMs produce eloquent but unverifiable prose, frequently inventing details (e.g., claiming a suspect is "carrying a rifle" when the camera only resolved a blurry walking stick, or hallucinating vehicle license numbers). |
| **Proposed SentinelAI Architecture** | Gemini 2.5 is strictly barred from "detecting" raw physical phenomena. Physical phenomena are supplied as immutable JSON facts. Gemini's role is restricted to cognitive reasoning, intent synthesis, and SOP formulation. The generated response is parsed against the database before display. |
| **Hypothesized Technical Advantage** | • **Zero Hallucination of Physical Facts**: 100% of reported targets, times, and perimeter breaches are mathematically anchored in verified database records.<br>• **Audit-Ready Compliance**: Incident briefings can be directly submitted to military command or legal courts with zero manual factual correction. |
| **Known Failure Modes & Limitations** | • If edge telemetry contains erroneous classifications (e.g., a wolf classified as a `dog`), the LLM will reason based on that erroneous fact.<br>• Schema adherence rejects summaries with minor formatting errors, requiring retry or fallback to raw tabular telemetry. |
| **Overhead (Edge vs. Hub)** | • **Edge**: Zero overhead (handled on Hub/Cloud).<br>• **Hub**: Minimal CPU overhead for JSON validation and cross-referencing regex parsing ($< 15\text{ms}$). |
| **Prior Art Overlap Risk** | **LOW-MEDIUM**: General RAG (Retrieval-Augmented Generation) and JSON-schema constrained decoding (e.g., Instructor, Outlines) are known.<br>**Differentiation Boundary**: The application of a *deterministic CV telemetry cross-examiner* that rejects multimodal LLM security incident dossiers if claims diverge from physical spatial tracking vectors. |

---

### 2.4 Mechanism 4: Deterministic Offline Event Graph Reconciliation

| Dimension | Specification |
| :--- | :--- |
| **Mathematical / Data-Structure Formulation** | Distributed Causal Synchronization with Conflict-Free Semantics:<br>• **Edge Vector Clock**: $\vec{C}_{\text{edge}} = \langle c_1, c_2, \dots, c_n \rangle$ advancing monotonically with each local event.<br>• **Local Append-Only WAL**: Local storage logs operations $\mathcal{O}_k = (\text{OpID}, \vec{C}_k, \text{NodeData}, \text{SHA256}_{\text{local}})$.<br>• **Reconciliation Operator**: Upon connection restoration, Central Cluster executes: $\mathcal{G}_{\text{central}} \leftarrow \mathcal{G}_{\text{central}} \sqcup \text{TopologicalSort}(\{\mathcal{O}_{\text{edge}}\})$; Track stitching function $\mathcal{M}(\text{Track}_A, \text{Track}_B) \to [0, 1]$ merges split trajectories where $\Delta t \le t_{\text{handover}}$ and $\text{Cosine}(\vec{v}_A, \vec{v}_B) \ge \tau_{\text{trajectory}}$. |
| **Conventional / SOTA Approach** | • Naive FIFO queue replay: Edge alerts are dumped sequentially into the central server, often flooding the database and creating duplicate incident tickets.<br>• Disconnected video is simply written to local SD cards or NVR disks; operators must physically travel to outposts to retrieve hard drives for investigation. |
| **Proposed SentinelAI Architecture** | Edge nodes maintain an embedded transactional write-ahead log (WAL). When the WAN link is severed, local operations continue seamlessly. Upon reconnection, an asynchronous, idempotency-keyed reconciliation handshake replays and topologically stitches events into the central event graph without duplicate alerts. |
| **Hypothesized Technical Advantage** | • Complete operational autonomy during prolonged (72+ hour) network blackouts.<br>• Zero duplicate alerts generated at Central SOC upon reconnect.<br>• Automated track healing: Unifies disjointed tracks recorded across edge cameras during network severance. |
| **Known Failure Modes & Limitations** | • Local storage exhaustion on edge nodes during multi-week network outages requiring FIFO ring-buffer eviction of raw video.<br>• Clock skew on disconnected edge nodes can disrupt topological sort if NTP servers are unreachable (requires hardware RTC or GPS time sync). |
| **Overhead (Edge vs. Hub)** | • **Edge**: Low storage overhead for local WAL ($\sim 50\text{MB}$ per 24 hours of event metadata); low CPU during queue flush.<br>• **Hub**: Moderate transactional I/O spike during multi-node reconciliation flush; mitigated by batch UPSERTs and connection throttling. |
| **Prior Art Overlap Risk** | **MEDIUM**: Distributed database replication (CRDTs, Git-like causal DAGs) is standard in distributed computing.<br>**Differentiation Boundary**: Application of *causal vector clocks and spatio-temporal track stitching* to resolve interrupted multi-camera perimeter tracking graphs without human intervention. |

---

## 3. Consolidated Technical Trade-off Matrix

| Metric / Attribute | EL-STEG (Mechanism 1) | Adaptive Verification (Mechanism 2) | Grounded Reporting (Mechanism 3) | Offline Reconciliation (Mechanism 4) |
| :--- | :--- | :--- | :--- | :--- |
| **Latency Impact** | $+2\text{ms}$ (Edge write) | $+1.5\text{ to } 3.5\text{s}$ (Tier 2 Cloud) | $+20\text{ms}$ (Hub validation) | Asynchronous (Background batch) |
| **Bandwidth Consumption** | Local only | $\sim 150\text{KB}$ per high-threat trigger | $\sim 5\text{KB}$ per incident report | Burst sync ($\sim 2\text{MB}$ / hr of outage) |
| **False Positive Impact** | Neutral (Structuring only) | **High Reduction** ($> 90\%$ drop) | High (Prevents hallucinated alarms)| Neutral (Preserves true events) |
| **Forensic Integrity** | **Cryptographic Proof** | Verifiable decision logs | Auditable field citations | Deterministic hash preservation |
| **Edge Hardware Demand** | Low (Hash + Node insert) | High (Continuous YOLOv8) | Zero (Runs on Hub/Cloud) | Low (Local disk WAL) |
