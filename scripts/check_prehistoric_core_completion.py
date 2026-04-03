from __future__ import annotations

import json
from pathlib import Path

from aegis_py.prehistoric_completion import build_prehistoric_completion_report


def main() -> int:
    report = build_prehistoric_completion_report()
    out_dir = Path('.planning') / 'benchmarks'
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / 'prehistoric_core_completion.json'
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
