# GenAI BorderGuard — Technical Problem Definition & User Personas

**Document Identifier:** DOC-RES-01  
**Category:** Problem Space & Operational Requirements  
**Status:** Approved Research Baseline  

---

## 1. Technical Problem Statement

National border perimeters, international maritime boundaries, and remote military installations present some of the most unforgiving operational environments for automated video surveillance. Modern border security agencies oversee thousands of kilometers of perimeter line instrumented with heterogeneous closed-circuit television (CCTV) cameras, long-range electro-optical/infrared (EO/IR) sensors, and legacy analog cameras retrofitted with IP encoders. 

Despite substantial capital investment in surveillance hardware, current operational deployments suffer from severe systemic failures:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                         CORE OPERATIONAL DILEMMA AT THE BORDER                         │
├───────────────────────────────────────┬────────────────────────────────────────────────┤
│       TRADITIONAL VIDEO ANALYTICS     │             NAIVE GENERATIVE AI (LLMs)         │
├───────────────────────────────────────┼────────────────────────────────────────────────┤
│ • High False Alarm Rate (FAR > 85%)   │ • Unviable Bandwidth (Gigabytes/hr cloud feed) │
│ • Severe Operator Alarm Fatigue       │ • High Inference Latency (2–10s per frame)     │
│ • Zero Contextual Intent Reasoning    │ • Risk of Hallucination in Critical Breaches   │
│ • Disconnected Spatial Tracks         │ • Complete Failure During Network Blackouts    │
│ • Fragile Legal Chain of Custody      │ • Extreme Cloud Token & Inference Costs        │
└───────────────────────────────────────┴────────────────────────────────────────────────┘
```

The fundamental technical challenge is to build a unified system architecture that delivers **deterministic, millisecond-latency edge detection** with **provable cryptographic chain of custody**, while simultaneously leveraging **multimodal generative reasoning** for context, intent, and reporting—without introducing hallucinations, unsustainable bandwidth requirements, or operational fragility during network severance.

---

## 2. In-Depth Operational & Environmental Dimensions

### 2.1 Environmental & Optical Hostility
Border perimeters span arid deserts, dense riverine forests, mountain passes, and coastal salt plains:
1. **Severe Atmospheric Attenuation**: Dust storms (haboobs), dense fog, advection marine fog, falling snow, torrential rain, and atmospheric heat shimmer (mirage effect causing target pixel jitter).
2. **Extreme Dynamic Range & Illumination Shifts**: Direct solar glare into lenses at dawn/dusk, backlighting, deep shadow occlusions, headlight sweep artifacts, and near-zero-lux conditions requiring active/passive infrared (IR) illumination (causing loss of chrominance and retro-reflective eye-shine from wildlife).
3. **Dynamic Environmental Noise**: Wind-induced swaying of perimeter vegetation (tall grasses, trees), fence micro-vibrations, tumbleweeds, flying insects settling on camera dome covers, and lens condensation/droplets.

### 2.2 Infrastructure Heterogeneity & Sensor Fragmentation
Border systems are rarely greenfield installations; they are layered brownfield ecosystems:
1. **Legacy Encoding Protocols**: Interfacing with RTSP/RTP over UDP/TCP, legacy analog composite feeds converted via NTSC/PAL video servers, ONVIF Profile S/G/T compliance discrepancies, and proprietary proprietary PTZ telemetry protocols (Pelco-D, Pelco-P).
2. **Variable Resolution and Frame-rates**: Sensor feeds vary wildly from legacy 480p analog up to modern 4K optical sensors, operating at asynchronous frame-rates ranging from 5 FPS (to save solar battery) to 30 FPS.
3. **Non-Uniform Field of View (FoV)**: Overlapping fields of view between adjacent fixed focal cameras and roaming pan-tilt-zoom (PTZ) cameras create severe perspective transformation shifts and scale distortion for distant targets (e.g., target height < 15 pixels at 400m).

### 2.3 Network Fragility & Bandwidth Bottlenecks
Remote border outposts frequently operate off-grid:
1. **Severely Constrained Backhaul**: Uplink connections rely on tactical SATCOM (e.g., Starlink, BGAN), long-range point-to-point microwave relays, or intermittent 3G/4G/5G cellular modems. Bandwidth budgets often cap available outbound transfer to 256 kbps – 2 Mbps per outpost.
2. **High Latency and Packet Jitter**: Network round-trip times (RTT) vary from 80ms to over 1,500ms over satellite hops, making real-time cloud-based video inference impossible.
3. **Periodic Network Severance**: Hostile weather, fiber cuts, electronic jamming, or tactical power outages cause frequent WAN blackouts lasting minutes to several days. The system must operate fully autonomously at the edge and cleanly reconcile state upon link restoration.

### 2.4 Computational & Power Constraints at the Tactical Edge
Edge surveillance compute nodes operate in remote huts, solar-powered masts, or armored field shelters:
1. **Thermal & Environmental Constraints**: Edge hardware is passively cooled, sealed (IP66/IP67) against dust and moisture, and operates in ambient temperatures from -25°C to +55°C.
2. **Compute Budgets**: Systems cannot assume data-center-grade clusters of multi-GPU nodes. Typical edge hardware consists of embedded SoCs (e.g., NVIDIA Jetson Orin AGX/Nano, Intel Core i7 with integrated iGPU, or commercial mini-PCs with entry-level discrete GPUs).
3. **Power Budget**: Edge nodes often run on solar panels backed by lithium iron phosphate (LiFePO4) battery banks, requiring power consumption to remain within 35W – 150W peak.

### 2.5 The Semantic Gap & Operator Cognitive Exhaustion
In a typical 100-camera border sector:
1. **Alarm Fatigue**: Commodity video analytics trigger between 1,500 and 5,000 motion or tripwire events per 24-hour cycle. Over 92% are non-actionable false alarms caused by animals, birds, tree limbs, or sensor noise.
2. **Attention Degradation**: Human physiological studies show that operator target detection efficiency falls by over 70% after only 20 minutes of continuous screen monitoring.
3. **Forensic Disconnection**: When a genuine breach occurs, field security teams receive fragmented, unlinked alerts (e.g., "Camera 04 Line Crossing" followed 3 minutes later by "Camera 07 Loitering"). Reconstructing the breach path across cameras requires tedious manual review of multiple video timelines, losing critical response minutes.
4. **Evidentiary Compromise**: In subsequent legal prosecutions or international border disputes, video recordings are frequently challenged over chain-of-custody lapses, absence of cryptographic hashing at capture time, or unverified manual editing.

---

## 3. Stakeholder & Intended User Personas

To ensure functional relevance and UX efficacy, SentinelAI is architected around four distinct operational personas across the military and paramilitary border command structure:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               OPERATIONAL COMMAND MATRIX                               │
├─────────────────────┬──────────────────────┬────────────────────┬──────────────────────┤
│ 1. Outpost Operator │ 2. Tactical Dispatch │ 3. Forensic / Legal│ 4. Systems Engineer  │
├─────────────────────┼──────────────────────┼────────────────────┼──────────────────────┤
│ • Tier 1 Triage     │ • Field Command      │ • Evidentiary Court│ • Edge Hardware/VMS  │
│ • <1s Reaction      │ • Sector SOP Action  │ • Audit & Chain    │ • Container Health   │
│ • Low Cognitive Load│ • Multi-Camera Synop.│ • Tamper Analysis  │ • Zero-Loss Storage  │
└─────────────────────┴──────────────────────┴────────────────────┴──────────────────────┘
```

### Persona 1: Tactical Outpost Sentry (Tier 1 Operator)
- **Role & Profile**: Enlisted soldier or border guard stationed at a remote Border Outpost (BOP) or forward watchtower.
- **Operating Environment**: High-stress, dimly lit watch room; operating 8-to-12-hour shifts; intermittent radio communications with field patrols.
- **Technical Literacy**: Moderate to basic; accustomed to hardware buttons, joysticks, and simplified surveillance monitor grids.
- **Key Objectives**:
  - Receive unambiguous, immediate (<1 second) acoustic and visual alerts for high-salience perimeter breaches.
  - Instantly distinguish between false alarms (e.g., deer herd at perimeter fence) and human tactical breach attempts (e.g., individual cutting wire under camouflage).
  - One-click confirmation to dispatch Quick Reaction Teams (QRT).
- **Critical Friction Points**: Overwhelming false alert volume; complex multi-screen interfaces that require manual typing; sluggish video scrubbing.

### Persona 2: Sector Command Watch Officer (Tier 2 Tactical Dispatcher)
- **Role & Profile**: Commissioned officer (e.g., Captain / Major) in the Sector Headquarters Security Operations Center (SOC).
- **Operating Environment**: Multi-monitor command center coordinating 10–50 outposts across a 150 km sector.
- **Technical Literacy**: Advanced tactical command training; proficient with Common Operating Picture (COP) GIS maps and VMS systems.
- **Key Objectives**:
  - Understand the holistic tactical picture: direction of movement, target speed, vehicle support, and anticipated breach corridors.
  - Review AI-synthesized tactical summaries generated by Google Gemini to approve standard operating procedure (SOP) escalations.
  - Coordinate inter-agency asset deployments (e.g., UAV launch, mobile patrol intercept).
- **Critical Friction Points**: Disjointed point-alerts from individual cameras that lack unified trajectory tracking; lack of executive briefing automation during fast-moving incidents.

### Persona 3: Forensic Investigator & Legal Officer (Tier 3 Intelligence)
- **Role & Profile**: Military legal officer, intelligence analyst, or border magistrate handling post-incident prosecution, international treaty violations, or counter-smuggling cartels.
- **Operating Environment**: Formal office environment conducting deep post-hoc evidentiary reviews weeks or months after an event.
- **Technical Literacy**: High legal and investigative competence; stringent evidentiary standards.
- **Key Objectives**:
  - Reconstruct the exact chronological timeline of a breach across multiple sensors with zero evidentiary gaps.
  - Export self-verifying, cryptographically sealed forensic evidence dossiers with verifiable SHA-256 hashes for judicial presentation.
  - Verify that AI-generated summaries are strictly grounded in deterministic telemetry without post-facto hallucinations.
- **Critical Friction Points**: Defense challenges asserting video footage was selectively clipped or modified; inability to trace who acknowledged or modified alert records in the VMS.

### Persona 4: Field Edge CV & Communications Engineer (Tier 4 Administrator)
- **Role & Profile**: Technical warrant officer or civilian systems integrator responsible for maintaining outpost edge servers, cameras, and network links.
- **Operating Environment**: Field maintenance vans, server enclosures at remote outposts, and centralized IT management dashboards.
- **Technical Literacy**: Expert in Linux, Docker containerization, networking (RTSP, ONVIF, VPNs), and edge computer vision deployment.
- **Key Objectives**:
  - Monitor edge inference frame rates, GPU/VPU memory utilization, model latency, and camera stream health (frame drops, signal loss).
  - Guarantee zero data loss during WAN outages via local write-ahead logging (WAL) and automatic conflict-free graph reconciliation upon reconnection.
  - Manage secure over-the-air (OTA) model and configuration updates across dozens of distributed edge nodes.
- **Critical Friction Points**: Fragile edge software that crashes during network loss; silent database synchronization failures; difficulty debugging remote edge nodes with limited uplink bandwidth.

---

## 4. Persona Requirements Matrix

| Parameter | Persona 1: Outpost Sentry | Persona 2: Watch Officer | Persona 3: Forensic Investigator | Persona 4: Systems Engineer |
| :--- | :--- | :--- | :--- | :--- |
| **Max Alert Latency** | $< 1.0\text{ s}$ local edge alert | $< 3.5\text{ s}$ tactical summary | Post-hoc / on demand ($< 10\text{ s}$) | Near-real-time telemetry ($< 5\text{ s}$) |
| **Primary Artifact** | 6s MP4 clip + Keyframe snapshot | Structured Threat Dossier & SOP | Sealed Evidence Package + Event DAG | Health metrics, logs, sync queues |
| **Verification Need** | Instant visual glance confirmation | Contextual intent & cross-camera path | Cryptographic hash & audit trail | Bit-level data consistency & integrity |
| **Interaction Mode** | High-contrast touch/mouse, 1-click | Interactive dashboard, natural Q&A | Multi-variable filter, PDF/JSON export | CLI, Docker metrics, FastAPI docs |
| **Offline Tolerance**| 100% operational capability required | Cached regional view | Local database access | Automatic queue drain & sync |
