# Aegis v9 Canonical Specification

## 1. Scoring Architecture
Aegis v9 follows the **Residual Judgment Engine** design. Every memory record is evaluated through four distinct tiers:

**Formula**: `S_final = S_base + Δ_judge + Δ_life + H_constraints`

### Tier 1: Base Relevance (`S_base`)
- **Semantic Relevance (60%)**: Contextual meaning match.
- **Lexical Match (5%)**: Direct keyword overlap (drastically reduced in v9).
- **Link Support (10%)**: Relationship-based relevance.
- **Scope Fit**: Hard multiplier (1.0 or penalty).

### Tier 2: Judgment Delta (`Δ_judge`)
- **Trust**: Boosted by evidence events and source quality.
- **Conflict**: Penalized by unresolved contradictions.
- **Correction**: Promoted if marked as 'Slot Winner', penalized if 'Superseded'.
- **Bias Calibration**: Aggressive penalty if lexical overlap is high but trust is low.

### Tier 3: Lifecycle Delta (`Δ_life`)
- **Staleness**: Penalizes records that haven't been accessed or updated.
- **Readiness**: Boosts records with high validated reuse count.

### Tier 4: Hard Constraints (`H_constraints`)
- **Archived**: Hard floor (-10.0).
- **Superseded**: Hard floor (-5.0).
- **Truth Winner**: Mandatory boost (+0.15 to +2.0 depending on intent).

## 2. Data Contract
### MemoryRecordV9
- `fact_kind`: `singleton` (overwrite) or `multivalued` (coexist).
- `is_slot_winner`: Explicitly determined by `adapter.py` based on status and metadata.

## 3. Operational Modes
- `v9_primary`: v9 controls ranking and filtering (Default).
- `shadow_v9`: v8 controls ranking, v9 metadata attached for audit.
- `v8_primary`: Bypass v9 entirely.

## 4. Explanation Contract
- **Compact**: Single sentence decisive factor.
- **Standard**: Adds primary boosts and penalties.
- **Deep (Audit)**: Includes exact math deltas (`base`, `judge`, `life`).
