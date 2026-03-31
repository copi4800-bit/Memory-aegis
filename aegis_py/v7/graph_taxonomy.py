from __future__ import annotations


EDGE_TYPE_ALIASES = {
    "same_subject": "DERIVED_FROM",
    "procedural_supports_semantic": "PRECONDITION_FOR",
    "supports": "RESULTS_IN",
    "extends": "PART_OF",
    "summary_of": "DERIVED_FROM",
    "contradicts": "CONTRADICTS",
    "supersedes": "SUPERSEDES",
}


def canonical_edge_type(link_type: str) -> str:
    return EDGE_TYPE_ALIASES.get(link_type, link_type.upper())
