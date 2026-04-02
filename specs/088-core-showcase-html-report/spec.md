# Feature Spec: 088 Core Showcase HTML Report

## Summary

Turn the full-core showcase into a polished local HTML experience so Aegis can be demonstrated like a product, not only like an operator tool.

## Problem

The full-core showcase now reveals nearly the whole Aegis core story, but it still lives primarily as terminal/tool output. That makes it harder to share and less visually convincing for product-level demos.

## Goals

- Render the existing core showcase payload into a polished HTML artifact.
- Keep the experience local, static, and deterministic.
- Present Aegis as a product-grade governed-memory briefing rather than raw diagnostic output.

## Non-Goals

- Building a live web app or JS-heavy frontend.
- Rewriting the showcase payload contract.
- Replacing the runtime tool path.

## Acceptance Criteria

1. The repo gains a script that renders a polished HTML core-showcase artifact.
2. Tests cover the HTML renderer.
3. The existing showcase and full suite remain green.
