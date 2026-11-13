# GenAI BorderGuard — Prior-Art Investigation Methodology & Search Checklist

**Document Identifier:** DOC-RES-03  
**Category:** Intellectual Property & Prior-Art Clearance Protocol  
**Status:** Approved Research Baseline  

---

## 1. Objectives & Scope of Prior-Art Clearance

Before any novel architectural claim can be validated, evaluated by patent counsel, or asserted in academic literature, a structured, repeatable **Prior-Art Investigation** must be executed. 

The objective of this checklist is threefold:
1. **Identify Existing Patents & Published Applications**: Prevent inadvertent infringement of third-party IP and establish the precise boundary of existing statutory claims.
2. **Review Peer-Reviewed Academic Literature**: Understand state-of-the-art academic benchmarks and ensure technical contributions exceed existing published baselines.
3. **Audit Commercial Systems**: Map features of leading commercial Video Management Systems (VMS) and AI surveillance platforms to identify off-the-shelf industry capabilities.

> [!WARNING]
> Prior-art searches must be documented with exact search strings, database identifiers, date stamps, and result counts. Search findings must be delivered to a qualified patent practitioner for formal Freedom-to-Operate (FTO) and patentability opinions.

---

## 2. Patent Classification & Registry Search Protocols

### 2.1 Target Patent Registries
Searches must be executed across the following national and international patent databases:
- **USPTO** (United States Patent and Trademark Office): Patent Public Search (PPUBS), covering Grant and Application databases.
- **EPO** (European Patent Office): Espacenet worldwide database (covering 140+ jurisdictions).
- **WIPO** (World Intellectual Property Organization): PATENTSCOPE (PCT international applications).
- **Google Patents**: Broad discovery index across CNIPA (China), JPO (Japan), KIPO (South Korea), and DPMA (Germany).

### 2.2 Relevant Classification Codes (CPC & IPC)
Searches must focus on intersections of the following Cooperative Patent Classifications:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        COOPERATIVE PATENT CLASSIFICATION (CPC) CODES                  │
├─────────────┬──────────────────────────────────────────────────────────────────────────┤
│ CPC Code    │ Definition / Field Description                                           │
├─────────────┼──────────────────────────────────────────────────────────────────────────┤
│ G06V 20/52  │ Surveillance or monitoring of persons, vehicles, or traffic; CCTV.       │
│ G06V 10/764 │ Classifiers; Pattern recognition using statistical or syntactic models.  │
│ G06V 10/82  │ Arrangements for recognition using neural networks (CNNs, Transformers). │
│ G06N 3/045  │ Multimodal neural networks combining visual and linguistic modalities.   │
│ G06N 3/08   │ Learning / inference architectures for neural networks.                  │
│ G06F 16/78  │ Retrieval of video data based on visual or spatial content.              │
│ G06F 21/64  │ Protecting data integrity; Digital signatures; Blockchain/Hash chains.   │
│ H04N 7/18   │ Closed-circuit television [CCTV] systems; Video surveillance setups.     │
│ G08B 13/196 │ Video intrusion detection; Perimeter alarm verification.                 │
│ H04L 9/32   │ Arrangements for verifying or proving identity; Cryptographic hashing.   │
└─────────────┴──────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Formulated Boolean Search Queries

The following search strings must be systematically executed in USPTO PPUBS and EPO Espacenet:

#### Query Cluster 1: Evidence-Linked Spatio-Temporal Event Graphs
```text
(G06V20/52 OR H04N7/18 OR G08B13/196) AND 
("spatio-temporal" OR "spatiotemporal" OR "event graph" OR "directed acyclic graph" OR "DAG") AND 
("cryptographic" OR "hash chain" OR "SHA-256" OR "chain of custody" OR "tamper-evident" OR "immutable") AND 
("multi-camera" OR "perimeter" OR "surveillance")
```
*Goal: Identify prior patents integrating graph data structures with cryptographic hashing for multi-camera surveillance evidence.*

#### Query Cluster 2: Adaptive Two-Tier Edge-to-Cloud Multimodal Verification
```text
(G06V20/52 OR G06V10/82) AND 
("two-tier" OR "hierarchical" OR "cascaded" OR "edge-cloud" OR "adaptive inference") AND 
("multimodal" OR "vision-language" OR "large language model" OR "VLM" OR "generative") AND 
("false alarm" OR "false positive" OR "salience" OR "bandwidth" OR "uplink")
```
*Goal: Uncover prior claims describing edge deterministic filters triggering on-demand multimodal language/vision models based on dynamic threat scores.*

#### Query Cluster 3: Formally Constrained Evidence-Grounded Reporting
```text
(G06N3/045 OR G06F16/78) AND 
("hallucination" OR "grounding" OR "constrained decoding" OR "schema enforcement") AND 
("incident report" OR "tactical briefing" OR "surveillance narrative") AND 
("bounding box" OR "telemetry" OR "spatial coordinates")
```
*Goal: Determine if methods for restricting generative surveillance reports to verified telemetry fact schemas have been patented.*

#### Query Cluster 4: Distributed Offline Event Graph Reconciliation
```text
(H04N7/18 OR G08B13/196 OR G06F16/78) AND 
("offline" OR "intermittent connectivity" OR "severed network" OR "network drop") AND 
("reconciliation" OR "synchronization" OR "topological sort" OR "vector clock" OR "CRDT") AND 
("video surveillance" OR "event buffer")
```
*Goal: Benchmark distributed synchronization techniques tailored to intermittent CCTV surveillance networks.*

---

## 3. Peer-Reviewed Academic Literature Checklist

The academic investigation must review papers published over the past 5 years (2021–2026) across top-tier computer vision, machine learning, and surveillance venues:

### 3.1 Primary Venues
- **Computer Vision**: CVPR, ICCV, ECCV, WACV, IEEE T-PAMI, IEEE T-CSVT.
- **Multimodal AI & NLP**: NeurIPS, ICLR, ICML, ACL, EMNLP.
- **Multimedia & Surveillance Systems**: ACM Multimedia (ACM MM), IEEE AVSS (Advanced Video and Signal Based Surveillance), IEEE Transactions on Information Forensics and Security (T-IFS).

### 3.2 Literature Investigation Matrix

| Focus Domain | Key Research Themes & Seminal Works to Benchmark | Primary Search Terms |
| :--- | :--- | :--- |
| **Video Event Knowledge Graphs (VEKG)** | - Dynamic scene graphs in long-form video<br>- Multi-camera identity handover & trajectory graphs<br>- Graph Neural Networks (GNNs) for anomaly detection | `"Video Scene Graph"`, `"Spatio-Temporal Knowledge Graph"`, `"Multi-Camera Tracking Graph"` |
| **Cascaded Edge-Cloud Analytics** | - *Focus* (Maniatis et al., OSDI)<br>- *NoScope* (Kang et al., VLDB)<br>- *Chameleon* (Jiang et al., SIGCOMM)<br>- Bandwidth-adaptive video querying | `"Cascaded Video Analytics"`, `"Edge-Cloud Filtering"`, `"Bandwidth-Constrained Surveillance"` |
| **Multimodal Grounding & Anti-Hallucination** | - POPE (Polling-based Object Probing Evaluation)<br>- Grounding DINO / Kosmos / PaLI architectures<br>- Neuro-symbolic verification of LLM outputs | `"VLM Hallucination Reduction"`, `"Structured Grounding"`, `"Vision-Language Spatial Alignment"` |
| **Cryptographic Media Provenance** | - C2PA (Coalition for Content Provenance and Authenticity)<br>- Verifiable video streams / zero-knowledge proofs for video<br>- Distributed hash-chains for digital forensics | `"Cryptographic Video Provenance"`, `"Tamper-Evident CCTV"`, `"Chain of Custody Video"` |
| **Distributed Intermittent Edge Sync** | - CRDTs (Conflict-free Replicated Data Types) in IoT<br>- Causal broadcast and vector clocks in disconnected edge networks | `"Intermittent Edge Sync"`, `"Offline Event Buffer Reconciliation"`, `"Distributed Surveillance Graph"` |

---

## 4. Commercial Systems & Industry Benchmark Audit

The investigation must evaluate the public product documentation, whitepapers, and patent portfolios of leading industry providers:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        COMMERCIAL SURVEILLANCE & AI AUDIT TARGETS                      │
├─────────────────────┬──────────────────────┬────────────────────┬──────────────────────┤
│ 1. Enterprise VMS   │ 2. Defense / Perimeter│ 3. Specialized AI  │ 4. Provenance / C2PA │
├─────────────────────┼──────────────────────┼────────────────────┼──────────────────────┤
│ • Milestone XProtect│ • Anduril Lattice OS │ • Hakimo           │ • Truepic            │
│ • Genetec SecCenter │ • Palantir AIP       │ • Ambient.ai       │ • Sony / Canon C2PA  │
│ • Avigilon (Motorola│ • Dedrone / Echodyne │ • BriefCam (Canon) │ • Axis Edge Vault    │
│ • Axis Camera Stat. │ • General Dynamics   │ • Irisity / AgentVi│ • Hanwha Wisenet     │
└─────────────────────┴──────────────────────┴────────────────────┴──────────────────────┘
```

### 4.1 Detailed System Evaluation Targets

1. **Anduril Industries (Lattice OS)**:
   - *Architecture*: Multi-sensor edge-to-cloud automated threat tracking combining radar, optical, and thermal sensors.
   - *Key Points to Investigate*: How Lattice models target tracks, whether they utilize formal graph data structures, and how they handle disconnected edge nodes.
   - *Patent Checks*: Search Anduril patent filings under USPTO assignee `Anduril Industries, Inc.` (focus on sensor fusion and autonomous track handover).

2. **Palantir Technologies (Palantir AIP / Gotham)**:
   - *Architecture*: Large-scale multi-source ontology graphs and LLM operational workflows.
   - *Key Points to Investigate*: How AIP enforces guardrails when querying physical sensor feeds; whether LLMs directly parse video or consume structured ontology objects.
   - *Patent Checks*: Assignee `Palantir Technologies, Inc.` in relation to graph databases and tactical threat synthesis.

3. **BriefCam (Canon Group) — Video Synopsis & REVIEW**:
   - *Architecture*: Extracting objects from video timelines, indexing them by attributes (clothing color, speed, direction), and compositing simultaneous playback.
   - *Key Points to Investigate*: How BriefCam tracks cross-camera handovers; degree of integration with generative text models.
   - *Patent Checks*: Assignee `BriefCam Ltd.` regarding video synopsis and trajectory indexing.

4. **Hakimo**:
   - *Architecture*: AI-driven alarm verification tailored to access control and perimeter intrusion, filtering false alarms before human review.
   - *Key Points to Investigate*: Whether they use multimodal LLMs or traditional deep learning classifiers for verification; edge vs. cloud distribution.

5. **Ambient.ai**:
   - *Architecture*: Computer vision intelligence layer sitting atop existing enterprise camera infrastructure, applying a signature-based threat detection library.
   - *Key Points to Investigate*: Use of spatio-temporal graphs for behavior recognition; offline survivability architecture.

---

## 5. Investigation Protocol Checklist

For each item in the investigation, researchers must complete the following steps:

- [ ] **Step 1: Record Search Metadata**: Log date, database used, exact boolean syntax, and total results retrieved.
- [ ] **Step 2: Screen Abstracts & Claims**: Identify patents and papers with overlapping claims to SentinelAI's 4 core hypotheses.
- [ ] **Step 3: Download Complete Specifications**: Acquire full PDF copies of top 10 most relevant patent grants/applications and top 15 research papers.
- [ ] **Step 4: Draft Novelty Boundary Matrix**: For each overlapping item, document:
  - What the prior art discloses (their claims/embodiment).
  - What the prior art *fails* to disclose (our hypothesized differentiation).
  - Technical justification for why the difference is non-obvious to a person having ordinary skill in the art (PHOSITA).
- [ ] **Step 5: Synthesize Intellectual Property Dossier**: Collate findings into an internal briefing document for certified patent counsel review.
