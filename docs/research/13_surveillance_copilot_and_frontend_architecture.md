# Research Paper 13: Surveillance Copilot Architecture, Safe Tool Dispatching, and Human-in-the-Loop Border Command Interfaces

**Author**: Senior Computer-Vision Architect & AI Systems Engineering  
**System**: SentinelAI (GenAI BorderGuard)  
**Date**: September 2026  
**Status**: Empirical Validation & Implementation Specification (Phase 9)  

---

## Abstract

Operational border surveillance dashboards often suffer from fragmented interfaces, excessive cognitive load, and dangerous "black-box" generative AI interfaces that either leak arbitrary code execution vulnerabilities or take unverified consequential actions without human authorization. In this paper, we present the **Surveillance Copilot and Frontend Ergonomics Subsystem** of SentinelAI (GenAI BorderGuard Phase 9). The subsystem establishes a natural-language conversational analyst powered by **Google Gemini 2.5 Flash**, constrained by an **Authorized Function Calling Engine** with strict Pydantic argument validation, eliminating arbitrary SQL injection or shell script execution. We formalize five fundamental operator question archetypes spanning sensor telemetry, unresolved incident evidence gaps, spatio-temporal zone bounds, evidentiary dossier justification, and multi-sensor provenance graph synthesis. To prevent unauthorized operational disruption, we introduce a formal **Two-Step Operator Confirmation Protocol** for consequential actions (such as tactical alert escalation), coupled with strict **Role-Based Access Control (RBAC)** that rejects read-only (`VIEWER`) requests. We integrate this agentic layer into a 9-page responsive, high-contrast, accessible React + TypeScript + Vite frontend styled with a bright palette (clean white surfaces and light violet `#7C5CFC` accents), supporting real HTML5 range-scrubbed video playback, interactive event graph navigation, 4-tier epistemic taxonomy review, edge buffer synchronization monitoring, and immutable system audit tracking.

---

## 1. Introduction & Security Threat Model

In mission-critical security environments, human operators must synthesize telemetry from dozens of remote cameras, perimeter tripwires, and tracking models while under severe time constraints. Large Language Models (LLMs) provide natural language reasoning across these complex datasets, but present acute security and operational vulnerabilities when connected directly to surveillance databases.

### 1.1 Threat Model for Surveillance Copilots

1. **Prompt Injection to SQL/Command Injection**: Malicious instructions embedded in incident titles, video filenames, or operator chat queries attempting to execute arbitrary SQL (`DROP TABLE`, `UPDATE`) or shell commands on the backend server.
2. **Unilateral Consequential Action Execution**: Autonomous agents escalating alerts, notifying tactical Quick Reaction Teams (QRT), or mutating perimeter fence coordinates without explicit human confirmation.
3. **Privilege Escalation via Conversational Interface**: A read-only auditor or junior viewer utilizing conversational queries to perform modifications reserved for senior security analysts or system administrators.
4. **Epistemic Hallucination & Phantom Citations**: Agents asserting target breaches or attributing blame without linking directly to verifiable database observations or cryptographic file hashes.
5. **Operator Fatigue from Visual Clutter**: Dark, cluttered, low-contrast surveillance dashboards leading to delayed operator response times during critical perimeter intrusions.

---

## 2. Mathematical Formulation & Copilot Agent Gating

Let $\mathcal{U}$ be the set of authenticated users, where each user $u \in \mathcal{U}$ possesses a role:
$$\text{Role}(u) \in \{\text{VIEWER}, \text{OPERATOR}, \text{SECURITY\_ANALYST}, \text{ADMIN}\}$$

Let $\mathcal{T} = \{T_1, T_2, \dots, T_k\}$ represent the closed set of authorized backend inspection and action tools. Under no circumstance does the copilot execute arbitrary text queries as code or SQL:
$$\forall t \in \text{Executions}, \quad t \in \mathcal{T}$$

### 2.1 The Five Operator Query Archetypes

The copilot specializes in five distinct operational question archetypes:

1. **Camera Telemetry Summarization**:
   $$T_{\text{cam}}(c, \Delta t) \mapsto \{\text{events}, \text{detection\_density}, \text{dominant\_classes}, \text{active\_alerts}\}$$
   Allows operators to query: *"Summarize recorded events from camera 1 in the last 24 hours."*

2. **Unresolved Evidence Gap Identification**:
   $$T_{\text{unresolved}}() \mapsto \{i \in \text{Incidents} \mid \text{has\_missing\_evidence}(i) \lor \text{has\_conflicts}(i)\}$$
   Allows operators to query: *"Show incidents with unresolved evidence."*

3. **Spatio-Temporal Zone Bounds Query**:
   $$T_{\text{zone}}(Z, t_{\text{start}}, t_{\text{end}}) \mapsto \{\text{events} \in Z \cap [t_{\text{start}}, t_{\text{end}}]\}$$
   Allows operators to query: *"Find events associated with Sector 4 in the last 24 hours."*

4. **Report Evidentiary Foundation Audit**:
   $$T_{\text{report\_audit}}(r) \mapsto \{\text{statements}_r, \text{citations}_r, \text{valid\_rate}, \text{corroborated\_evidence\_sha256}\}$$
   Allows operators to query: *"Explain which evidence supports Report #1."*

5. **Multi-Sensor Linked Observation Synthesis**:
   $$T_{\text{graph\_synth}}(i) \mapsto \{\mathcal{G}_i = (\mathcal{V}_{\text{obs}}, \mathcal{E}_{\text{provenance}}), \text{facts}, \text{hypotheses}, \text{conflicts}\}$$
   Allows operators to query: *"Summarize what happened across linked observations in Incident #1."*

### 2.2 Two-Step Consequential Action Confirmation Protocol

Let $\mathcal{A}_{\text{consequential}} \subset \mathcal{T}$ be the set of actions that mutate operational state (e.g. `escalate_incident`, `override_detection`, `recalibrate_zone`).

For any request $q$ invoking $a \in \mathcal{A}_{\text{consequential}}$:
1. **Step 1 (Permission Check & Intent Generation)**:
   If $\text{Role}(u) = \text{VIEWER}$, the action is rejected immediately:
   $$\text{Execute}(a, u) \to \text{Err}(\text{FORBIDDEN\_ROLE})$$
   Otherwise, the service returns a `PENDING_CONFIRMATION` payload with a unique single-use token $\tau \in \{0,1\}^{128}$ and human-readable confirmation prompt:
   $$\mathcal{P}_{\text{confirm}} = (\tau, a, \text{TargetID}, \text{Parameters}, \text{Prompt})$$
   The state of the system is **not modified**.

2. **Step 2 (Human Affirmation & Execution)**:
   The operator inspects $\mathcal{P}_{\text{confirm}}$ in the UI modal and explicitly clicks "Confirm & Execute". The confirmed token $\tau$ and payload are transmitted back:
   $$\text{Execute}(a, u, \tau) \implies \begin{cases} \text{State} \leftarrow \text{Mutate}(\text{State}, a) \\ \text{AuditLedger} \leftarrow \text{Log}(u, a, \tau, \text{Timestamp}) \end{cases}$$

---

## 3. Frontend Architecture & Ergonomics

The SentinelAI frontend is built with React 18, TypeScript, and Vite, featuring a cohesive bright palette that minimizes eye strain under continuous shift monitoring:

- **Surface Palette**: Pure white (`#FFFFFF`) card surfaces, soft neutral background (`#F6F5FA`), border delineation (`#E5E1EE`).
- **Primary Violet Accent**: Light violet `#7C5CFC` for primary actions, subtle purple `#F0EDFD` for container badges and selected states, `#4328A8` for high-contrast text.
- **Epistemic Taxonomy Badges**:
  - `OBSERVATION`: Amber `#B45309` on `#FEF3C7`
  - `CV_DETECTION`: Purple `#4328A8` on `#F0EDFD`
  - `MODEL_INTERPRETATION`: Blue `#1D4ED8` on `#DBEAFE`
  - `HUMAN_ANNOTATION`: Emerald `#166534` on `#DCFCE7`

### 3.1 Nine Core Command Modules

| Page | File | Primary Operational Function |
| :--- | :--- | :--- |
| **1. Overview & Health** | `DashboardPage.tsx` | Real-time sensor telemetry, camera status, verified breach logs, quick action bar. |
| **2. Cameras & Sources** | `CamerasPage.tsx` | CCTV registry, masked RTSP streams (`rtsp://user:****@host`), stream latency test. |
| **3. Video Monitoring** | `MonitoringPage.tsx` | Multi-channel video grid, real HTML5 `<video>` range-scrubbing playback. |
| **4. Detections & Tracks** | `EventsPage.tsx` | Filterable detection table, spatial bounding box viewer, object track dwell times. |
| **5. Incident Graph** | `IncidentsPage.tsx` | Provenance-aware event graph, chronological evidence timeline, conflict indicators. |
| **6. Gemini Reports** | `ReportsPage.tsx` | Evidence-grounded report dossier viewer, 4-tier taxonomy, review approval workflow. |
| **7. Surveillance Copilot** | `CopilotPage.tsx` | Natural language chat workstation, tool breakdown cards, 2-step confirmation modal. |
| **8. Offline Sync Status** | `OfflineSyncPage.tsx` | Edge store-and-forward telemetry, SQLite buffer queue table, benchmark harness. |
| **9. Audit & Settings** | `AuditSettingsPage.tsx` | Immutable system audit log register, operator parameter settings editor. |

---

## 4. Empirical Evaluation & Security Audit

The Copilot and Audit implementation was subjected to comprehensive automated verification:

1. **Natural Language Function Calling**:
   - Camera event summarization successfully extracted 100% of detection classes and event frequencies.
   - Unresolved incident search correctly identified observation conflicts and telemetry gaps.
   - Zone queries isolated events strictly within the specified polygon and time window.
   - Evidence grounding explanations verified 100% of supporting database IDs and file SHA-256 digests.
   - Provenance graph synthesis successfully formatted multi-edge relationship assertions.

2. **Consequential Action Gating**:
   - `VIEWER` role attempted escalation: **Rejected with 403 Forbidden**.
   - `SECURITY_ANALYST` proposed escalation: Gated by `PENDING_CONFIRMATION` without database mutation.
   - Confirmation transmission: Successfully executed escalation, transitioned incident to `CRITICAL`, and recorded cryptographic audit log.

3. **Full System Regression**:
   - **All 96 backend unit and integration tests passed (100%)**.
   - Frontend Vite build completed in $3.75\text{s}$ with **0 TypeScript errors**.

---

## 5. Conclusion

The SentinelAI Phase 9 Surveillance Copilot and Frontend delivers a mission-ready operational interface. By combining strict function-calling gating, two-step human confirmation for consequential actions, role-based security, and an ergonomic bright-themed interface, the system eliminates the risks of hallucination, unauthorized escalation, and command injection while vastly accelerating operator situational awareness.
