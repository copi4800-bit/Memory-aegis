from __future__ import annotations

from pathlib import Path
import runpy


def main() -> int:
    script = Path(__file__).resolve().parent.parent / "bin" / "truthkeep-setup"
    runpy.run_path(str(script), run_name="__main__")
    return 0


__all__ = ["main"]


if __name__ == "__main__":
    raise SystemExit(main())
