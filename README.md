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
`memory_governance`, `memory_doctor`, `memory_scan`, `memory_visualize`, `memory_backup_*`, `memory_sync_*`, `memory_background_*`, `memory_vector_inspect`, `memory_evidence_artifacts`, `memory_storage_*`, and more.

---

## 📜 License

MIT

---

*Built for absolute trust. Aegis v10 — The Constitution for AI Memory.* 🛡️
