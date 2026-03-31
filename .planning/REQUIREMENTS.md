# Requirements

## v1: Foundation & Core Retrieval

| ID | Requirement | Logic |
|---|---|---|
| **STOR-01** | SQLite+FTS5 Storage | Local-first persistence for memories and links. |
| **STOR-02** | 4 Memory Types | Support `working`, `episodic`, `semantic`, and `procedural`. |
| **STOR-03** | Refined Schema | Include `metadata_json`, `scope_id`, `source_ref`, etc. |
| **RETR-01** | Scope-Aware Search | Exact or strong scope filtering to prevent leakage. |
| **RETR-02** | Explainable Results | Include `reasons` and `provenance` in every search result. |
| **RETR-03** | FTS5 Pipeline | Normalize -> FTS5 -> Scope Filter -> Rerank. |
| **LIFE-01** | Session Lifecycle | Working memory expiration or demotion at session end. |
| **LIFE-02** | Memory Worthiness | Filter ingestion based on fact/preference/instruction value. |
| **HYG-01** | Reinforcement/Decay | Bounded activation scoring and aging. |
| **HYG-02** | Conflict Detection | Meerkat-style scan for contradictions (suggestions only). |
| **PROF-01** | Style Profiles | Interaction preference tracking and response styling. |
| **INT-01** | MCP Tool Surface | Standard interface (`store`, `search`, `clean`, `status`). |
| **INT-02** | Lifecycle Hooks | `session_start`, `on_message`, `session_end` integration. |
| **QUAL-01** | Benchmark Harness | Mandatory metrics (Recall@K, MRR, Latency). |

## v2: Advanced Hygiene & Sync (Out of Scope for v1)
- **V2-SYNC**: Cloud hosting/multi-device sync.
- **V2-VECTOR**: Vector DB as default path.
- **V2-AUTO**: Broad hard auto-resolution for ambiguous conflicts.
- **V2-Cognition**: Full agent orchestration.
