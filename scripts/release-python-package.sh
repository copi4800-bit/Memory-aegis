#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(CDPATH='' cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT_DIR="${1:-$REPO_ROOT/dist/python-release}"
STAGE_DIR="$OUTPUT_DIR/aegis-python-vnext"
SCRIPTS_DIR="$STAGE_DIR/scripts"
BIN_DIR="$STAGE_DIR/bin"

rm -rf "$STAGE_DIR"
mkdir -p "$STAGE_DIR"
mkdir -p "$SCRIPTS_DIR"
mkdir -p "$BIN_DIR"

cp -R "$REPO_ROOT/aegis_py" "$STAGE_DIR/"
cp "$REPO_ROOT/README.md" "$STAGE_DIR/"
cp "$REPO_ROOT/requirements.txt" "$STAGE_DIR/"
cp "$REPO_ROOT/openclaw.plugin.json" "$STAGE_DIR/"
cp "$REPO_ROOT/scripts/demo_first_memory.py" "$SCRIPTS_DIR/"
cp "$REPO_ROOT/scripts/demo_integration_boundary.py" "$SCRIPTS_DIR/"
cp "$REPO_ROOT/scripts/demo_grounded_recall.py" "$SCRIPTS_DIR/"
cp "$REPO_ROOT/bin/aegis-setup" "$BIN_DIR/"

cat > "$STAGE_DIR/RELEASE_NOTES.txt" <<'EOF'
Aegis Python vNext release bundle

Validation before packaging:
  PYTHONPATH=/path/to/repo .venv/bin/pytest -q tests

Included artifacts:
  - aegis_py/
  - bin/aegis-setup
  - README.md
  - requirements.txt
  - scripts/demo_first_memory.py
  - scripts/demo_integration_boundary.py
  - scripts/demo_grounded_recall.py
  - openclaw.plugin.json
EOF

cat > "$STAGE_DIR/QUICKSTART.txt" <<'EOF'
Aegis Python vNext quickstart

1. Create a local virtual environment:
   python3 -m venv .venv

2. Install runtime dependencies:
   .venv/bin/python -m pip install -r requirements.txt

3. Run setup:
   python3 ./bin/aegis-setup

4. Run the first-value demo:
   .venv/bin/python scripts/demo_first_memory.py

5. Run the integration demo:
   .venv/bin/python scripts/demo_integration_boundary.py

6. Run the grounding demo:
   .venv/bin/python scripts/demo_grounded_recall.py

7. Run the full Python validation suite if needed:
   PYTHONPATH=. .venv/bin/python -m pytest -q tests
EOF

mkdir -p "$OUTPUT_DIR"
tar -czf "$OUTPUT_DIR/aegis-python-vnext.tar.gz" -C "$OUTPUT_DIR" "aegis-python-vnext"

echo "Release bundle created at: $OUTPUT_DIR/aegis-python-vnext.tar.gz"
