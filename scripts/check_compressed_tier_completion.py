from __future__ import annotations

import argparse
import json
from pathlib import Path

from aegis_py.retrieval.compressed_tier import (
    DEFAULT_COMPRESSED_TIER_ARTIFACT,
    evaluate_compressed_tier_gate,
    load_compressed_tier_artifact,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check whether the software-level compressed tier is complete.")
    parser.add_argument(
        "--artifact",
        type=Path,
        default=DEFAULT_COMPRESSED_TIER_ARTIFACT,
        help="Path to the compressed candidate tier benchmark summary JSON.",
    )
    args = parser.parse_args()

    artifact = load_compressed_tier_artifact(args.artifact)
    passed, failures, summary_metrics = evaluate_compressed_tier_gate(artifact)
    payload = {
        "capability": "software_level_compressed_tier",
        "passed": passed,
        "summary_metrics": summary_metrics,
        "failures": failures,
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
