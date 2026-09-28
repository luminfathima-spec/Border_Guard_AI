# SentinelAI — AI & Computer Vision Architecture

## Architectural Philosophy: Strict Layer Separation

A key innovation in SentinelAI is the clean separation of duties between **Deterministic Computer Vision** and **Generative Cognitive Reasoning**:

```
┌────────────────────────────────────────────────────────┐
│   LAYER 1: Deterministic Computer Vision & Tracking    │
│   (YOLOv8 + ByteTrack / IoU + Spatial Geometry)        │
├────────────────────────────────────────────────────────┤
│   - Millisecond-level inference                        │
│   - Exact bounding boxes & class confidences           │
│   - Mathematical point-in-polygon & vector crossing    │
│   - Outputs: Hard structured telemetry (JSON facts)    │
└──────────────────────────┬─────────────────────────────┘
                           │
                 [Structured Facts]
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│   LAYER 2: Cognitive Reasoning & Natural Language      │
│   (Google Gemini 2.5 Flash / Pro)                      │
├────────────────────────────────────────────────────────┤
│   - Consumes deterministic telemetry facts             │
│   - Evaluates multi-event breach patterns              │
│   - Produces tactical military threat assessments     │
│   - Recommends actionable SOP containment protocols    │
│   - Answers natural language analyst questions         │
└────────────────────────────────────────────────────────┘
```

---

## Why This Separation Matters

1. **Zero Hallucination of Physical Facts**:
   - The GenAI model is never asked to "detect" if a person is in a video from raw unstructured text.
   - YOLO and spatial ray-casting establish the physical facts with mathematical certainty.
2. **Explainability & Chain of Custody**:
   - Every Gemini summary cites specific event IDs, timestamps, camera identifiers, and SHA-256 evidence files.
3. **Graceful Degradation**:
   - If internet connectivity is interrupted at remote border outposts, Layer 1 continues operating autonomously at 100% capacity with local heuristic reasoning.
