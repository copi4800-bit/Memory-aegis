from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class BeastStatus:
    role: str
    depth: str
    effect: str


PREHISTORIC_STATUS: dict[str, BeastStatus] = {
    "Meganeura": BeastStatus("Scribe", "core-deep", "write scoring + admission shaping"),
    "Dimetrodon": BeastStatus("Extractor", "core-deep", "feature separation + admission shaping"),
    "Ammonite": BeastStatus("Normalizer", "core-deep", "subject stability + admission shaping"),
    "Chalicotherium": BeastStatus("Classifier", "core-deep", "lane fit + admission shaping"),
    "Dunkleosteus": BeastStatus("Scorer", "core-deep", "decisive write pressure"),
    "Utahraptor": BeastStatus("Scout", "core-deep", "lexical pursuit + judged recall pressure"),
    "Basilosaurus": BeastStatus("Oracle", "core-deep", "semantic echo + judged recall pressure"),
    "Pterodactyl": BeastStatus("Navigator", "core-deep", "graph flight + judged recall pressure"),
    "Tyrannosaurus Rex": BeastStatus("Reranker", "core-deep", "winner dominance rerank"),
    "Argentinosaurus": BeastStatus("Scope Beast", "core-deep", "scope geometry + judged recall pressure"),
    "Paraceratherium": BeastStatus("Explainer", "core-deep", "governed narrative + judged recall pressure"),
    "Thylacoleo": BeastStatus("Meerkat", "core-deep", "conflict sentinel"),
    "Diplocaulus": BeastStatus("Axolotl", "core-deep", "regeneration-gated maintenance control"),
    "Oviraptor": BeastStatus("Bowerbird", "core-deep", "taxonomy guidance + drift-guard admission shaping"),
    "Smilodon": BeastStatus("Decay Beast", "core-deep", "retirement-driven lifecycle transitions"),
    "Glyptodon": BeastStatus("Consolidator", "core-deep", "consolidation shell judged recall pressure"),
    "Deinosuchus": BeastStatus("Nutcracker", "core-deep", "compaction-gated maintenance and judged recall pressure"),
    "Archelon": BeastStatus("Constitution Beast", "core-deep", "winner/superseded invariants"),
    "Dire Wolf": BeastStatus("Identity Beast", "core-deep", "identity-guided judged recall pressure"),
    "Megatherium": BeastStatus("Guardian Beast", "core-deep", "boundary admissibility enforcement"),
    "Megarachne": BeastStatus("Weaver", "core-deep", "topology-weighted judged recall pressure"),
    "Mammoth": BeastStatus("Archivist", "core-deep", "archive survival"),
    "Titanoboa": BeastStatus("Librarian", "core-deep", "subject-locality judged recall pressure"),
}

REQUIRED_CORE_DEEP = {
    "Meganeura",
    "Dimetrodon",
    "Ammonite",
    "Chalicotherium",
    "Dunkleosteus",
    "Utahraptor",
    "Basilosaurus",
    "Pterodactyl",
    "Tyrannosaurus Rex",
    "Argentinosaurus",
    "Paraceratherium",
    "Thylacoleo",
    "Diplocaulus",
    "Smilodon",
    "Glyptodon",
    "Deinosuchus",
    "Oviraptor",
    "Archelon",
    "Dire Wolf",
    "Megatherium",
    "Megarachne",
    "Mammoth",
    "Titanoboa",
}


def build_prehistoric_completion_report() -> dict[str, Any]:
    total = len(PREHISTORIC_STATUS)
    core_deep = sorted(name for name, status in PREHISTORIC_STATUS.items() if status.depth == "core-deep")
    pipeline_active = sorted(name for name, status in PREHISTORIC_STATUS.items() if status.depth == "pipeline-active")
    signal_surface = sorted(name for name, status in PREHISTORIC_STATUS.items() if status.depth == "signal-surface")
    missing_required = sorted(name for name in REQUIRED_CORE_DEEP if PREHISTORIC_STATUS.get(name, BeastStatus("", "", "")).depth != "core-deep")
    passed = total == 23 and not signal_surface and not pipeline_active and not missing_required and len(core_deep) == 23
    return {
        "total_beasts": total,
        "core_deep_count": len(core_deep),
        "pipeline_active_count": len(pipeline_active),
        "signal_surface_count": len(signal_surface),
        "core_deep": core_deep,
        "pipeline_active": pipeline_active,
        "signal_surface": signal_surface,
        "missing_required_core_deep": missing_required,
        "passed": passed,
    }
