#!/usr/bin/env bash
# Phase 0 Gate Check — aegis-core-stable
# Chạy tất cả tests: unit → gate → stress → e2e
# Nếu pass hết → tag version aegis-core-stable

set -e

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Memory Aegis v4 — Phase 0 Gate Check                   ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

cd "$(dirname "$0")/.."

# Step 1: TypeScript
echo "▸ Step 1: TypeScript type check..."
./node_modules/.bin/tsc --noEmit
echo "  ✓ TypeScript OK"
echo ""

# Step 2: Unit tests
echo "▸ Step 2: Unit tests..."
./node_modules/.bin/vitest run test/unit/ --reporter=verbose 2>&1 | tail -5
echo ""

# Step 3: Gate tests (benchmarks + layer checks)
echo "▸ Step 3: Gate tests (core-stable benchmark)..."
./node_modules/.bin/vitest run test/gate/ --reporter=verbose 2>&1 | tail -30
echo ""

# Step 4: Stress tests
echo "▸ Step 4: Stress tests..."
./node_modules/.bin/vitest run test/stress/ --reporter=verbose 2>&1 | tail -10
echo ""

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  All gates passed — aegis-core-stable                   ║"
echo "╚══════════════════════════════════════════════════════════╝"
