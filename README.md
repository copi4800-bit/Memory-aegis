# Memory Aegis v9 (The Fortress Edition)

**Mathematical Truth-Alignment & Residual Judgment Engine for AI Agents.**

## Product Overview
Aegis v9 is a revolutionary leap from search to **Judgment**. It is a pure Python-centric memory engine designed to eliminate hallucination, resolve complex contradictions, and guarantee that your agent always operates on the "Current Truth."

## 🚀 Key v9 "Fortress" Enhancements:

*   **Residual Judgment Engine**: Uses a multi-tier mathematical formula (`S_final = S_base + Δ_judge + Δ_life + H_constraints`) to prioritize truth over keywords.
*   **Zero-Trust Fortress**: Features a **Nuclear Penalty (-15.0)** that automatically neutralizes low-trust or unverified information, making the system immune to "flashy" noise.
*   **Faithful Explanations**: Every result comes with a human-centric narrative and a deep mathematical audit trace, explaining exactly why it outranked other candidates.
*   **Correction-First Architecture**: Naturally handles deep correction chains, ensuring that new facts instantly supersede outdated ones without manual intervention.
*   **Conflict Storm Resilience**: Identifies and penalizes unresolved contradictions at the architectural level to ensure safe-fail operation.

## Why Aegis v9?
Aegis v9 moves beyond simple database lookups. It treats memory as a dynamic field:
*   **Crystallization**: Important, repeated facts gain stability.
*   **Exponential Decay**: Stale, unverified data fades away automatically to reduce cognitive noise.
*   **Truth-Alignment**: Uses evidence events and phả hệ (lineage) to differentiate between "noise" and "verity."

## 🛠 Installation & Quick Start
### Requirements:
*   Python 3.10+
*   SQLite (FTS5 enabled)

### Setup:
1.  Clone the repository.
2.  `pip install -r requirements.txt`
3.  `export PYTHONPATH=.`
4.  Run the gauntlet to verify the fortress:
    `python3 scripts/v9_extreme_gauntlet.py --noise-memories 1000`

## 🧱 Architecture
The v9 runtime is organized into specialized judgment modules:
*   **v9 Scorer**: The mathematical brain (`aegis_py/v9/scorer.py`).
*   **v9 Adapter**: Data-to-signal mapper (`aegis_py/v9/adapter.py`).
*   **Retrieval**: Rerank-before-filter pipeline (`aegis_py/retrieval/search.py`).
*   **Surface**: Faithful explanation and audit layer (`aegis_py/surface.py`).

---
*Built for absolute reliability. Designed for the Truth. Aegis v9 — The conscience of your agent.*
