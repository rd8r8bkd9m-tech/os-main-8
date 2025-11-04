# Kolibri AI Edge: Core Architecture

**Version**: 0.1.0 (alpha)  
**Date**: 3 ноября 2025  
**Status**: In development

## Executive Summary

Kolibri AI Edge is a **native, local-first AI operating system** combining kernel-level decision-making, energy-aware scheduling, and verifiable knowledge snapshots. This document defines the reference architecture, component interactions, and deployment model for the prototype.

---

## 1. High-Level Design

### 1.1 Core Principles

- **Native & Local-First**: All computation happens on-device without mandatory cloud dependency.
- **Energy-Aware**: Scheduler makes decisions based on device power budget and latency SLO.
- **Verifiable**: Knowledge snapshots are signed; reasoning traces are auditable.
- **Modular**: Pluggable runners (KolibriScript, local inference, optional upstream) enable flexible deployment.
- **Kernel-Level Integration**: VGA text UI and serial I/O for hardware-level feedback.

### 1.2 Deployment Topology

```
┌──────────────────────────────────────────┐
│        Local Device / Edge Node          │
├──────────────────────────────────────────┤
│  Kolibri Kernel (kernel/main.c)          │
│  - Native VGA UI (kernel/ui_text.c)      │
│  - Serial I/O relay                      │
│  - Energy metrics collection             │
└────────────┬────────────────────────────┘
             │
        [QEMU/Bare Metal]
             │
┌────────────▼────────────────────────────┐
│   FastAPI Backend Service                │
│   (backend/service/routes/inference.py)  │
│  ┌───────────────────────────────────┐  │
│  │ Energy-Aware Scheduler            │  │
│  │ (backend/service/scheduler.py)    │  │
│  └───┬────────────┬──────────┬──────┘  │
│      │            │          │         │
│   KS │          Local        │ Upstream│
│  Script   Persistent Runner  │  LLM    │
│      │            │          │   API   │
└──────┴────────────┴──────────┴─────────┘
```

---

## 2. Component Architecture

### 2.1 Meta-Controller (Scheduler)

**Module**: `backend/service/scheduler.py`

Centralized decision engine that routes inference requests based on:

- **Energy Budget** (`device_power_budget_j`): Device-specific power allocation in joules.
- **Latency SLO** (`default_latency_slo_ms`): Per-request or global latency requirement.
- **Complexity Estimation**: Heuristic based on prompt length, code markers, mathematical notation.

#### Scheduler Flow

```
User Request → Prompt Analysis → Complexity Score
                                        ↓
                                  Estimate Costs
                                   ├─ Script: 0.05–0.15J, 50–300ms
                                   ├─ Local: 0.2–0.5J, 200–600ms
                                   └─ Upstream: 0.1–2.5J, 500–2000ms
                                        ↓
                                  Filter by Constraints
                                   (energy & latency)
                                        ↓
                                  Select Best Candidate
                                   (minimize cost)
                                        ↓
                                  Return RunnerChoice + Metadata
```

#### Output: `RunnerChoice`

```python
@dataclass(frozen=True)
class RunnerChoice:
    runner_type: Literal["script", "local", "upstream"]
    estimated_cost_j: float
    estimated_latency_ms: float
    reason: str
    metadata: Dict[str, object]
```

### 2.2 Inference Pipeline

**Module**: `backend/service/routes/inference.py`

Enhanced with scheduler integration:

1. **Prompt Policy Enforcement**: Forbidden topics check.
2. **Scheduler Decision**: `_scheduler.schedule(prompt)` → `RunnerChoice`.
3. **Upstream Call** (if LLM mode): Execute via configured `llm_endpoint`.
4. **Moderation**: Tone analysis, forbidden topics in response.
5. **Audit Logging**: Include scheduler metadata in genome events.

#### Audit Event Example

```json
{
  "event_type": "llm.infer",
  "stage": "response",
  "actor": "user@example.com",
  "payload": {
    "provider": "upstream",
    "latency_ms": 850.5,
    "scheduler": {
      "runner_choice": "upstream",
      "runner_reason": "Selected Upstream LLM API (cost 0.95J, latency 950ms)",
      "estimated_cost_j": 0.95,
      "estimated_latency_ms": 950.0
    },
    "moderation": {
      "tone": "neutral",
      "tone_score": 0.3,
      "paraphrased": false
    }
  }
}
```

### 2.3 Persistent Runner (Prototype)

**Status**: Planned  
**Location**: `backend/service/plugins/persistent_runner.py` (future)

A long-lived inference process communicating via Unix socket:

- **Health Check**: `/healthz` → `{ "status": "ready" }`
- **Infer API**: `POST /infer` → streaming tokens
- **Metadata**: Track CPU time, memory usage, tokens generated

```python
# Pseudo-interface
class PersistentRunner:
    async def infer(self, prompt: str) -> AsyncIterator[str]:
        """Stream inference tokens."""
        
    async def healthz(self) -> HealthStatus:
        """Check runner health."""
```

### 2.4 Verifiable Knowledge Snapshots

**Status**: Planned  
**Location**: `backend/tools/snapshot_*.py`

Structured representation of model beliefs at a point in time:

```json
{
  "version": 1,
  "timestamp": "2025-11-03T10:00:00Z",
  "model_id": "kolibri-ai-edge-v0.1",
  "knowledge_hash": "sha256:abc123...",
  "claims": [
    {
      "id": "claim_001",
      "text": "Energy cost for local script execution is 0.05–0.15J",
      "confidence": 0.95,
      "sources": ["benchmark_run_20251103"]
    }
  ],
  "signature": "hmac-sha256:xyz..."
}
```

**Verification**: `snapshot_verify.py` checks HMAC against known keys.

### 2.5 Streaming Pipeline

**Status**: Planned  
**Endpoints**:
- `POST /api/v1/infer/stream` → Server-Sent Events (SSE)
- `WS /ws/v1/infer` → WebSocket (bidirectional)

Each event includes scheduler choice and estimated vs. actual latency.

### 2.6 Kernel UI Extensions

**Module**: `kernel/ui_text.c`

Current: Single-prompt chat interface with history.

Planned:
- Real-time token streaming display
- Energy meter (estimated power draw in watts)
- Latency meter (request time vs. SLO)
- Runner selection indicator (script/local/upstream)

---

## 3. Request Lifecycle

### 3.1 Happy Path: Inference Request

```
1. Frontend/Serial Input
   └─→ "Explain Kolibri architecture"
   
2. FastAPI Endpoint (infer)
   └─→ Deserialize InferenceRequest
   
3. Policy Check
   └─→ enforce_prompt_policy() ✓
   
4. Scheduler Decision
   └─→ _scheduler.schedule(prompt)
   └─→ Chooses "upstream" (1200ms SLO, 0.5J budget)
   
5. Upstream Call
   └─→ httpx.post(llm_endpoint) → 850ms latency
   
6. Moderation
   └─→ evaluate_tone(), moderate_response() ✓
   
7. Audit Log
   └─→ log_genome_event(payload with scheduler metadata)
   
8. Response
   └─→ InferenceResponse(response="...", provider="llm", latency_ms=850)
```

### 3.2 Constrained Path: Energy Budget Exceeded

```
1. Scheduler estimates cost for prompt
2. Cost (1.2J) exceeds budget (1.0J)
3. Fallback to "script" option (0.08J) ✓
4. KolibriScript executes locally
5. Response + reason logged
```

---

## 4. Energy Model

### 4.1 Cost Estimation

Based on complexity heuristic:

- **Length-based**: `min(len(prompt) / 500, 1.0)`
- **Code markers**: `+0.2` if `"```"` or `"def "` present
- **Math markers**: `+0.1` if `"$"` or `"∫"` present

### 4.2 Runner Cost Functions

| Runner | Min Cost | Max Cost | Latency Range | Notes |
|--------|----------|----------|---------------|-------|
| KolibriScript | 0.05J | 0.15J | 50–300ms | Local, deterministic |
| Persistent | 0.2J | 0.5J | 200–600ms | Local, persistent state |
| Upstream | 0.1J | 2.5J | 500–2000ms | Network-dependent |

---

## 5. Configuration & Environment

### 5.1 Scheduler Settings

Configured at startup:

```python
_scheduler = EnergyAwareScheduler(
    device_power_budget_j=10.0,
    default_latency_slo_ms=1000.0,
    local_runner_available=False,
    upstream_available=True,
)
```

### 5.2 Backend Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `KOLIBRI_RESPONSE_MODE` | "llm", "script", or "local" | `llm` |
| `KOLIBRI_LLM_ENDPOINT` | Upstream API URL | `http://localhost:8080/infer` |
| `KOLIBRI_LLM_TIMEOUT` | Request timeout (seconds) | `30` |
| `KOLIBRI_LLM_TEMPERATURE` | Generation temperature | `0.7` |

---

## 6. Roadmap & Integration Points

### Phase 1: Base Scheduler (Current)
- ✅ `EnergyAwareScheduler` module with heuristic cost estimation
- ✅ Integration into inference pipeline
- ✅ Metadata logging in audit events

### Phase 2: Local Runners (Next)
- [ ] Persistent runner with Unix socket RPC
- [ ] Healthcheck & load monitoring
- [ ] Plugin architecture in FastAPI

### Phase 3: Knowledge Snapshots (Later)
- [ ] Snapshot serialization (JSON, protobuf)
- [ ] HMAC signing & verification
- [ ] CLI tools for snapshot operations

### Phase 4: Streaming & Kernel UI (Future)
- [ ] SSE/WebSocket endpoints
- [ ] Token-by-token streaming display in kernel
- [ ] Energy/latency meters

### Phase 5: AGI Metrics & Telemetry (Experimental)
- [ ] Verifiable reasoning traces
- [ ] Token-level attribution
- [ ] Energy efficiency scoring

---

## 7. Security & Compliance

### 7.1 Trust Model

- **Kernel as Root of Trust**: Kernel UI and serial relay provide hardware-level evidence.
- **Signed Snapshots**: Knowledge snapshots are HMAC-signed with verifiable timestamps.
- **Audit Trail**: All decisions logged with scheduler metadata for post-hoc analysis.

### 7.2 Isolation

- **Local Runners**: Sandboxed via OS process isolation.
- **Upstream Calls**: Authenticated via bearer token (if SSO enabled).
- **Moderation**: Prompt & response filtering per policy.

---

## 8. Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| Scheduler latency | <5ms | No-I/O decision time |
| Script response | <300ms | In-browser WASM |
| Local runner response | <600ms | Persistent process |
| Upstream response | <1500ms (p95) | Network-bound |
| Energy per request | <1J (avg) | Device budget dependent |

---

## 9. Appendix: File Structure

```
backend/service/
├── scheduler.py          # Energy-aware scheduler module
├── routes/
│   └── inference.py      # Enhanced with scheduler integration
├── plugins/              # (Future)
│   └── persistent_runner.py
└── tools/                # (Future)
    ├── snapshot_sign.py
    └── snapshot_verify.py

kernel/
├── ui_text.c             # VGA chat UI (streaming tokens planned)
└── main.c

projects/kolibri_ai_edge/
├── AGI_ARCHITECTURE.md   # This file
├── AGI_MANIFESTO.md
└── IP_README.md          # (Future)
```

---

## References

- AGENTS.md: Contribution guidelines for Kolibri ecosystem
- KOLIBRI_OS.md: Kernel architecture documentation
- docs/deployment.md: Deployment playbooks
- backend/service/config.py: Runtime configuration schema

