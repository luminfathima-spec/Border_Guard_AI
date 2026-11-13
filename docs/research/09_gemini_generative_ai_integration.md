# Research Document 09: Google Gemini Generative AI Integration & Deterministic Evidence Safeguards

**Author**: Senior Computer-Vision Architect & AI Systems Researcher  
**System**: SentinelAI (GenAI BorderGuard)  
**Date**: September 2026  
**Status**: Implemented & Verified (Phase 5)

---

## 1. Technical Problem Statement

### 1.1 The Epistemic Hazard of Generative AI in Legal Evidentiary Chains
Recent advancements in multimodal Large Language Models (MLLMs), such as Google Gemini, enable unprecedented situational reasoning, natural language summarization, and cross-modal correlation across visual and telemetry streams. However, integrating generative models into national defense, border security, and high-consequence surveillance introduces a catastrophic failure mode: **unconstrained epistemic hallucination**.

In criminal and military jurisprudence, every factual assertion must satisfy a verifiable **Chain of Custody**:
1. If an intelligence summary asserts: *"Camera CAM-04 recorded the suspect breaching Demarcation Tripwire 2 at 04:33:12 UTC, corroborated by thermal snapshot EV-109"*, each referenced entity (`CAM-04`, `Demarcation Tripwire 2`, `EV-109`, and timestamp $t_0$) must exist as an immutable physical detection record.
2. Standard generative systems operate probabilistically. Without deterministic validation, an MLLM frequently hallucinates plausible-sounding but fictitious camera IDs, fabricates non-existent corroborating evidence numbers, or transposes chronological timestamps. If such hallucinated claims penetrate an official incident dossier, the evidentiary integrity of the entire prosecution is legally invalidated.

### 1.2 Bandwidth, Privacy, and Operational Security Constraints
Surveillance installations along remote border demarcations operate under strict bandwidth, latency, and security limitations:
1. **Continuous Video Streaming Bottleneck**: Streaming 24/7 uncompressed 1080p/4K CCTV feeds across satellite or cellular uplinks to cloud APIs is bandwidth-prohibitive, cost-inefficient, and introduces significant latency.
2. **Operational Privacy & PII Exposure**: Transmitting unvetted video streams risks leaking sensitive operator biometrics, encryption tokens, or internal network credentials.
3. **Transient Network Fragility**: Remote edge connectivity is inherently lossy. AI integration must withstand transient network drops, rate limits ($429$), and service unavailability ($503$) without dropping surveillance alerts.

---

## 2. Official Google AI Specifications & Architectural Trade-offs

### 2.1 Supported Model Family & Capabilities

| Parameter | Gemini 2.5 Flash (`gemini-2.5-flash`) | Gemini 2.5 Pro (`gemini-2.5-pro`) | Legacy (`gemini-1.5-flash`) |
| :--- | :--- | :--- | :--- |
| **Primary Use Case** | **Real-time Tactical Triage (Default)** | Multi-camera Forensic Investigation | Legacy Edge Deployments |
| **Context Window** | 1,048,576 tokens (~1 hour multimodal) | 2,097,152 tokens | 1,048,576 tokens |
| **Structured Output** | Native Pydantic JSON schema (`response_schema`) | Native Pydantic JSON schema | Partial JSON mode |
| **Inference Latency** | **Sub-second (400ms – 900ms)** | 2.5s – 5.0s | 800ms – 1.8s |
| **Rate Limits (Free)** | 15 RPM / 1M TPM / 1,500 RPD | 2 RPM / 32k TPM / 50 RPD | 15 RPM / 1M TPM |
| **Cost (Pay-as-you-go)**| ~$0.075 / 1M input, ~$0.30 / 1M output | ~$1.25 / 1M input, ~$5.00 / 1M output | ~$0.075 / 1M input |

**Architectural Decision**: SentinelAI utilizes `gemini-2.5-flash` as its primary operational intelligence model configured dynamically via `settings.GEMINI_MODEL`. It delivers the optimal balance of millisecond response latency, multimodal keyframe reasoning, and cost-effective structured output enforcement.

### 2.2 Multimodal Input Strategy: Event-Triggered Keyframes
Rather than transmitting continuous video streams, SentinelAI implements **Event-Triggered Keyframe Selection**:
$$\text{Video Stream } \mathcal{V} \xrightarrow{\text{YOLOv8 + Ray-Casting}} \text{Confirmed Breach at } t_{\text{breach}} \xrightarrow{\text{FrameSelector}} \{ \mathcal{F}_{t - 1.5\text{s}}, \mathcal{F}_{t_{\text{breach}}}, \mathcal{F}_{t + 1.5\text{s}} \}$$
* When computer-vision tracking confirms a perimeter tripwire breach or restricted zone entry, the system isolates a 3-frame sequence capturing pre-intrusion trajectory, the exact demarcation crossing event, and post-intrusion vector.
* Frames are downscaled to a maximum dimension of $1024 \times 1024$ and compressed to JPEG ($85\%$ quality), reducing network payload size from $>50\text{ MB}$ (raw video) to $<350\text{ KB}$ while preserving full forensic fidelity.

---

## 3. Epistemic Isolation & The Deterministic Cross-Examiner

To reconcile generative reasoning with the legal chain of custody, SentinelAI enforces a strict mathematical and operational separation between **Measured Physical Detections** and **Generative Cognitive Inferences**.

```
                   ┌─────────────────────────────────────────┐
                   │    PostgreSQL Immutable Sensor Ledger   │
                   │ (Cameras, Detections, Events, Evidence) │
                   └────────────────────┬────────────────────┘
                                        │ (Sanitized Telemetry Facts)
                                        ▼
                             ┌───────────────────────┐
                             │ Google Gemini 2.5     │
                             │ (Multimodal MLLM)     │
                             └──────────┬────────────┘
                                        │ (Probabilistic JSON Schema)
                                        ▼
                       ┌─────────────────────────────────┐
                       │  DETERMINISTIC CROSS-EXAMINER   │
                       │  - Verify Camera IDs in DB      │
                       │  - Verify Evidence IDs in DB    │
                       │  - Verify Event IDs in DB       │
                       │  - Validate Timestamp Windows   │
                       └────────┬───────────────┬────────┘
                   [No Hallucinations]      [Hallucinations Detected]
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐     ┌──────────────────┐
                       │ Status: SUCCESS │     │ Status: FLAGGED  │
                       │ Grounding = 1.0 │     │ Quarantine IDs   │
                       │ Persist Record  │     │ Attach Warning   │
                       └─────────────────┘     └──────────────────┘
```

### 3.1 Mathematical Grounding Formulation
Let $\mathcal{C}_{\text{cited}} = \{c_1, c_2, \dots, c_m\}$ be the set of integer camera identifiers cited in the generative model output, and $\mathcal{E}_{\text{cited}} = \{e_1, e_2, \dots, e_k\}$ be the set of cited evidence identifiers.

Let $\mathcal{D}_{\text{cam}}$ and $\mathcal{D}_{\text{ev}}$ denote the ground-truth set of primary keys in the database tables `cameras` and `evidence`:
$$\mathcal{C}_{\text{verified}} = \mathcal{C}_{\text{cited}} \cap \mathcal{D}_{\text{cam}}, \quad \mathcal{C}_{\text{ungrounded}} = \mathcal{C}_{\text{cited}} \setminus \mathcal{D}_{\text{cam}}$$
$$\mathcal{E}_{\text{verified}} = \mathcal{E}_{\text{cited}} \cap \mathcal{D}_{\text{ev}}, \quad \mathcal{E}_{\text{ungrounded}} = \mathcal{E}_{\text{cited}} \setminus \mathcal{D}_{\text{ev}}$$

The **Grounding Verification Score** $S_{\text{ground}} \in [0.0, 1.0]$ is strictly defined as:
$$S_{\text{ground}} = \begin{cases}
1.0 & \text{if } |\mathcal{C}_{\text{cited}}| + |\mathcal{E}_{\text{cited}}| = 0 \\
\frac{|\mathcal{C}_{\text{verified}}| + |\mathcal{E}_{\text{verified}}|}{|\mathcal{C}_{\text{cited}}| + |\mathcal{E}_{\text{cited}}|} & \text{otherwise}
\end{cases}$$

### 3.2 Automated Quarantine & Evidentiary Warning Protocol
If $|\mathcal{C}_{\text{ungrounded}}| + |\mathcal{E}_{\text{ungrounded}}| > 0$:
1. The analysis status is immediately set to `AnalysisStatus.FLAGGED`.
2. All ungrounded identifiers are stripped from the active output object to prevent downstream automated SOP systems from acting on non-existent targets.
3. An explicit evidentiary caution banner is appended to the tactical summary:
   `> [!CAUTION] CROSS-EXAMINER GROUNDING SAFEGUARD WARNING: Generative AI cited ungrounded entities not found in verified sensor records...`
4. The exact audit discrepancy is permanently recorded in `AIAnalysis.grounded_citations`.

---

## 4. Privacy, Operational Security & Data Retention

To comply with defense operational security standards:
1. **Payload Sanitization (`sanitize_telemetry`)**:
   - RTSP passwords, credentials, and query strings are stripped using regular expression tokenizers prior to prompt compilation (`rtsp://user:pass@host` $\to$ `rtsp://user:****@host`).
   - Operator JWT bearer tokens and session secrets are excised.
2. **Bounded Exponential Backoff with Jitter**:
   - On encountering HTTP $429$ (Rate Limit Exceeded) or HTTP $503$ (Service Unavailable), client calls execute up to 3 retry attempts with exponential backoff:
     $$t_{\text{wait}} = t_{\text{base}} \times 2^{\text{attempt} - 1} + \mathcal{U}(0.1, 0.5)$$
3. **Deterministic Mock Fallback (`MockGeminiClient`)**:
   - In offline field environments, air-gapped watchtowers, or test suites, the system falls back to `MockGeminiClient`. The mock inspects input telemetry, generates schema-valid responses, and explicitly declares `is_mock: true`.

---

## 5. Testable Hypotheses

* **Hypothesis $H_{2,1}$ (Grounding Verification & Hallucination Elimination)**:  
  Enforcing post-generation cross-examination against PostgreSQL entity tables guarantees $100\%$ detection and quarantine of hallucinated camera, evidence, and event identifiers, ensuring zero ungrounded entity references enter verified surveillance records ($S_{\text{ground}} = 1.0$ for all accepted records).

* **Hypothesis $H_{2,2}$ (Structured Tactical Triage Acceleration)**:  
  Constraining multimodal generative outputs to rigid JSON Pydantic schemas reduces security analyst incident triage verification latency by $>60\%$ compared to unstructured natural language narrative reports.
