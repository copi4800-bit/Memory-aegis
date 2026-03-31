"""Aegis v8 runtime surfaces.

Keep package import side effects minimal so storage modules can import
`aegis_py.v7.<submodule>` without triggering runtime cycles.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

__all__ = [
    "GovernedBackgroundIntelligence",
    "MemoryStateMachine",
    "PolicyGateDecision",
    "RetrievalOrchestrator",
    "SpecializedStorageSurfaces",
    "ValidationPolicyGate",
]

_EXPORT_MAP = {
    "GovernedBackgroundIntelligence": (".background", "GovernedBackgroundIntelligence"),
    "MemoryStateMachine": (".state_machine", "MemoryStateMachine"),
    "PolicyGateDecision": (".policy_gate", "PolicyGateDecision"),
    "RetrievalOrchestrator": (".retrieval_orchestrator", "RetrievalOrchestrator"),
    "SpecializedStorageSurfaces": (".storage_surfaces", "SpecializedStorageSurfaces"),
    "ValidationPolicyGate": (".policy_gate", "ValidationPolicyGate"),
}


def __getattr__(name: str) -> Any:
    target = _EXPORT_MAP.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attr_name = target
    module = import_module(module_name, __name__)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value
