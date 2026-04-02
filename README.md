# Memory Aegis v10 — The Constitutional Memory Engine 🛡️

**A Governance-First memory engine for AI agents. Truth over Score. Policy over Guesswork.**

Aegis v10 is a long-term memory system that enforces truth through a **5-tier Constitutional Policy pipeline (C0-C4)**. Every memory must pass through hard governance rules before it can be returned to the user, ensuring absolute accuracy and zero hallucination leakage.

---

## 🚀 Key Features

### ⚖️ Constitutional Governance (C0-C4)
Every retrieval result is filtered through 5 precedence layers:

| Level | Name | Function |
|---|---|---|
| **C0** | System Safety | Block harmful or illegal content |
| **C1** | User Override | User corrections always take priority |
| **C2** | Canonical Truth | Hard-exclude superseded facts, protect slot winners |
| **C3** | Governance Risk | Quarantine high-conflict memories, budget pressure escalation |
| **C4** | Soft Judgment | Filter low-relevance results |

### 🧠 Residual Judgment Engine
Mathematical scoring core with a four-tier residual formula:
```
S_final = S_base + Δ_judge + Δ_life + H_constraints
```
- **Base**: Initial semantic/lexical recall signal
- **Judge**: Truth alignment, evidence strength, conflict penalties
- **Life**: Temporal decay and habit-based readiness
- **Constraints**: Hard floors for superseded/archived records

### 🔐 Truth Registry
Manages fact ownership with margin-aware winner selection:
- **Winner**: The current truth. Always returned. Protected by `C2_SLOT_WINNER_PROTECTION`.
- **Contender**: Competing fact pending review. Surfaces only in audit mode.
- **Superseded**: Old truth. Hard-excluded from normal recall.

### 🗣️ Zero-Locking Identity
No hardcoded pronouns or persona labels. The system learns persona exclusively from explicit user commands and adapts immediately.

### 🩺 Health Diagnostics
Built-in memory health monitoring with 4 severity levels, conflict detection, staleness tracking, and actionable remediation guidance.

### 📝 Explainable Results
Every result includes a human-readable reason, policy trace, trust state, and suppressed candidates with "why-not" explanations for full transparency.

---

## 🛠 Installation

### Requirements
- Python 3.11+
- SQLite with FTS5

### Option 1: NPM (recommended for OpenClaw)
```bash
git clone https://github.com/copi4800-bit/Memory-aegis.git
cd Memory-aegis
npm install
```

### Option 2: Shell Script
```bash
git clone https://github.com/copi4800-bit/Memory-aegis.git
cd Memory-aegis
bash install.sh
```

### Option 3: Pip (for developers)
```bash
git clone https://github.com/copi4800-bit/Memory-aegis.git
cd Memory-aegis
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
```

---

## 🔌 OpenClaw Integration

Add to your `config.json`:
```json
{
  "mcpServers": {
    "aegis": {
      "command": "/path/to/Memory-aegis/.venv/bin/python",
      "args": ["/path/to/Memory-aegis/aegis_py/mcp/server.py"],
      "env": { "PYTHONPATH": "/path/to/Memory-aegis" }
    }
  }
}
```

---

## 🧱 Architecture

```
aegis_py/
├── v10/                    # Constitutional Governance Engine
│   ├── engine.py           # govern(): Score → Rules → Constitution → Review
│   ├── policy.py           # MemoryConstitution (C0-C4)
│   ├── truth_registry.py   # Winner/Contender/Loser slot management
│   ├── review.py           # Priority-based review queue
│   ├── events.py           # Governance audit trail
│   └── models.py           # DecisionObject, GovernanceStatus, TruthRole
├── v10_scoring/            # Residual Judgment Engine (math scoring core)
├── facade.py               # Zero-config API: remember/recall/correct/status
├── app.py                  # Main orchestrator (2500+ lines)
├── preferences/            # Zero-Locking identity extractor
├── ux/                     # i18n, Health diagnostics
├── storage/                # SQLite + FTS5 + Evidence + Graph
├── mcp/                    # 40+ MCP Tools
├── retrieval/              # Search pipeline + Spreading activation
├── conflict/               # Conflict detection & resolution
└── hygiene/                # Maintenance & state machine
```

---

## 🧪 Stress Testing

```bash
export PYTHONPATH=.

# V10 Constitutional Gauntlet
python3 scripts/v10_gauntlet_test.py

# V10 Super Stress
python3 scripts/super_stress_v10.py

# V10 Extreme Gauntlet (5000+ noise memories)
python3 scripts/v10_extreme_gauntlet.py
```

---

## 🎯 Core Spotlight

Want to see Aegis' strongest differentiator quickly?

Run:

```bash
export PYTHONPATH=.
python3 scripts/demo_core_spotlight.py
```

This spotlight demo shows one old fact, one correction, one query, and the governed result:

- selected current truth
- human-readable explanation
- governance/truth state
- why-not output for the older fact

To see the same spotlight idea on competing contenders, run:

```bash
export PYTHONPATH=.
python3 scripts/demo_conflict_spotlight.py
```

To measure the same advantage with deterministic fixtures, run:

```bash
export PYTHONPATH=.
python3 scripts/benchmark_truth_spotlight.py
```

To enforce the governed pass/fail bar for that artifact:

```bash
python3 scripts/check_truth_spotlight_gate.py
```

To render a readable report from the same artifact:

```bash
python3 scripts/render_truth_spotlight_report.py
```

If `.planning/benchmarks/truth_spotlight_summary.before.json` exists, the report also includes a historical trend section against that prior artifact.

To bundle the current summary, report, and gate status into one manifest:

```bash
python3 scripts/bundle_truth_release_evidence.py
```

To run the broader Aegis gauntlet across core truth, scale, adversarial, and product-readiness checks:

```bash
python3 scripts/aegis_gauntlet.py
```

To diagnose whether repetitive write pressure is landing as exact deduplication or admission-policy blocks:

```bash
python3 scripts/diagnose_ingest_pressure.py
```

To decide whether the current admission policy is healthy enough to close the write-path investigation for the current deployment class:

```bash
python3 scripts/check_ingest_policy_readiness.py
```

To render one full-core Aegis experience that shows selected truth, why-this, why-not, evidence, governance, signals, graph context, and scope health in one place:

```bash
python3 scripts/demo_core_showcase.py
```

To generate the same story as a polished local HTML report:

```bash
python3 scripts/render_core_showcase_html.py
```

To compare a previous benchmark artifact with the current one:

```bash
export PYTHONPATH=.
python3 scripts/compare_truth_spotlight.py path/to/older_summary.json
```

For the short written version of that story, see [docs/WHY_AEGIS_CORE_WINS.md](docs/WHY_AEGIS_CORE_WINS.md).

---

## 📋 MCP Tools (40+)

### Consumer Tools
| Tool | Description |
|---|---|
| `memory_remember` | Store information into long-term memory |
| `memory_recall` | Retrieve memories related to a query |
| `memory_correct` | Correct or update existing information |
| `memory_forget` | Remove information from memory |
| `memory_stats` | View memory status and health |
| `memory_profile` | See what Aegis remembers about you |

### Advanced Tools
`memory_spotlight`, `memory_governance`, `memory_doctor`, `memory_scan`, `memory_visualize`, `memory_backup_*`, `memory_sync_*`, `memory_background_*`, `memory_vector_inspect`, `memory_evidence_artifacts`, `memory_storage_*`, and more.

---

## 📜 License

MIT

---

*Built for absolute trust. Aegis v10 — The Constitution for AI Memory.* 🛡️
