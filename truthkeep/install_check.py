from __future__ import annotations

import json
from pathlib import Path

from aegis_py.install_check import (
    build_install_readiness_report,
    check_command,
    check_python_version,
    check_sqlite_fts5,
)


def main() -> int:
    report = build_install_readiness_report(Path.cwd())
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


__all__ = [
    "build_install_readiness_report",
    "check_command",
    "check_python_version",
    "check_sqlite_fts5",
    "main",
]


if __name__ == '__main__':
    raise SystemExit(main())

