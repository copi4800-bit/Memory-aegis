from __future__ import annotations

import html
import json
from typing import Any


def _escape(value: Any) -> str:
    return html.escape("" if value is None else str(value))


def _json_block(value: Any) -> str:
    return html.escape(json.dumps(value, indent=2, ensure_ascii=False))


def render_core_showcase_html(payload: dict[str, Any], *, title: str = "Aegis Core Showcase") -> str:
    verdict = payload["verdict"]
    summary_items = "".join(f"<li>{_escape(item)}</li>" for item in payload["executive_summary"])
    why_not_items = payload.get("why_not", [])
    why_not_html = (
        "".join(
            (
                "<li>"
                f"<strong>{_escape(item.get('content'))}</strong>"
                f"<span>{_escape(item.get('reason'))}</span>"
                "</li>"
            )
            for item in why_not_items
        )
        if why_not_items
        else "<li><strong>No suppressed alternatives</strong><span>This winner stood alone for the current query.</span></li>"
    )
    evidence_items = payload["evidence_summary"].get("items", [])
    evidence_html = "".join(
        (
            "<li>"
            f"<strong>{_escape(item.get('source_kind'))}</strong>"
            f"<span>{_escape(item.get('source_ref'))}</span>"
            f"<code>{_escape(item.get('raw_content'))}</code>"
            "</li>"
        )
        for item in evidence_items
    )
    governance_events = payload["governance_summary"].get("events", [])
    governance_html = "".join(
        (
            "<li>"
            f"<strong>{_escape(item.get('event_kind'))}</strong>"
            f"<span>{_escape(item.get('created_at'))}</span>"
            f"<code>{_escape(item.get('payload'))}</code>"
            "</li>"
        )
        for item in governance_events
    )
    chips = (
        f"<span class='chip accent'>{_escape(verdict['label'])}</span>"
        f"<span class='chip'>{_escape(payload['truth_state'].get('governance_status'))}</span>"
        f"<span class='chip'>{_escape(payload['truth_state'].get('truth_role'))}</span>"
        f"<span class='chip'>{_escape(payload['signal_summary']['labels']['trust'])} trust</span>"
        f"<span class='chip'>{_escape(payload['signal_summary']['labels']['readiness'])}</span>"
        f"<span class='chip'>{_escape(payload['health_summary']['health_label'])} health</span>"
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{_escape(title)}</title>
  <style>
    :root {{
      --bg: #f7f1e8;
      --panel: rgba(255,255,255,0.78);
      --panel-strong: rgba(255,255,255,0.92);
      --ink: #1f2321;
      --muted: #59615c;
      --accent: #0f766e;
      --accent-warm: #c26028;
      --line: rgba(31,35,33,0.12);
      --shadow: 0 24px 70px rgba(31,35,33,0.12);
      --radius: 24px;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Aptos", "Trebuchet MS", "Segoe UI Variable Text", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(15,118,110,0.18), transparent 28%),
        radial-gradient(circle at top right, rgba(194,96,40,0.16), transparent 24%),
        linear-gradient(180deg, #fbf6ef 0%, var(--bg) 100%);
      min-height: 100vh;
    }}
    .shell {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 40px 24px 80px;
    }}
    .hero {{
      background: linear-gradient(135deg, rgba(255,255,255,0.92), rgba(255,255,255,0.72));
      border: 1px solid var(--line);
      border-radius: 32px;
      box-shadow: var(--shadow);
      padding: 32px;
      position: relative;
      overflow: hidden;
    }}
    .hero::after {{
      content: "";
      position: absolute;
      inset: auto -80px -80px auto;
      width: 220px;
      height: 220px;
      background: radial-gradient(circle, rgba(15,118,110,0.14), transparent 70%);
    }}
    h1, h2, h3 {{
      margin: 0;
      font-family: "Georgia", "Times New Roman", serif;
      letter-spacing: -0.02em;
    }}
    h1 {{
      font-size: clamp(2.4rem, 5vw, 4.2rem);
      line-height: 0.96;
      max-width: 10ch;
    }}
    .kicker {{
      text-transform: uppercase;
      letter-spacing: 0.18em;
      font-size: 0.75rem;
      color: var(--accent);
      font-weight: 700;
      margin-bottom: 14px;
    }}
    .lede {{
      margin-top: 18px;
      max-width: 68ch;
      color: var(--muted);
      font-size: 1.05rem;
      line-height: 1.65;
    }}
    .chips {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 22px;
    }}
    .chip {{
      display: inline-flex;
      align-items: center;
      padding: 10px 14px;
      border-radius: 999px;
      border: 1px solid var(--line);
      background: rgba(255,255,255,0.75);
      color: var(--muted);
      font-size: 0.92rem;
    }}
    .chip.accent {{
      background: linear-gradient(135deg, rgba(15,118,110,0.16), rgba(15,118,110,0.08));
      color: var(--ink);
      border-color: rgba(15,118,110,0.18);
      font-weight: 700;
    }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 16px;
      margin-top: 28px;
    }}
    .metric {{
      padding: 18px;
      border-radius: 20px;
      background: var(--panel);
      border: 1px solid var(--line);
    }}
    .metric strong {{
      display: block;
      font-size: 1.7rem;
      margin-top: 8px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: 1.3fr 1fr;
      gap: 20px;
      margin-top: 24px;
    }}
    .panel {{
      background: var(--panel-strong);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      padding: 22px;
    }}
    .panel p {{
      margin: 0;
      color: var(--muted);
      line-height: 1.65;
    }}
    .stack {{
      display: grid;
      gap: 20px;
      margin-top: 24px;
    }}
    ul {{
      margin: 14px 0 0;
      padding-left: 18px;
    }}
    li {{
      margin: 10px 0;
      color: var(--muted);
    }}
    li strong {{
      display: block;
      color: var(--ink);
      margin-bottom: 4px;
    }}
    code, pre {{
      font-family: "Cascadia Code", "Consolas", monospace;
      font-size: 0.9rem;
    }}
    code {{
      display: block;
      margin-top: 6px;
      padding: 10px 12px;
      background: rgba(31,35,33,0.05);
      border-radius: 14px;
      overflow-wrap: anywhere;
      white-space: pre-wrap;
    }}
    pre {{
      margin: 0;
      padding: 16px;
      border-radius: 18px;
      background: #171b19;
      color: #eef3ef;
      overflow: auto;
    }}
    .footer-note {{
      margin-top: 28px;
      color: var(--muted);
      font-size: 0.95rem;
    }}
    @media (max-width: 900px) {{
      .grid {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <div class="kicker">Aegis Final-Form Memory Brief</div>
      <h1>{_escape(title)}</h1>
      <p class="lede">A single governed-memory briefing that surfaces selected truth, explanation, evidence, governance, core signals, graph context, and scope health in one deliberate experience.</p>
      <div class="chips">{chips}</div>
      <div class="metrics">
        <article class="metric"><span>Trust Score</span><strong>{verdict['trust_score']:.3f}</strong></article>
        <article class="metric"><span>Readiness</span><strong>{verdict['readiness_score']:.3f}</strong></article>
        <article class="metric"><span>Evidence</span><strong>{verdict['evidence_count']}</strong></article>
        <article class="metric"><span>Governance Events</span><strong>{verdict['governance_events']}</strong></article>
      </div>
    </section>

    <section class="grid">
      <article class="panel">
        <div class="kicker">Executive Summary</div>
        <h2>Why Aegis chose this memory</h2>
        <ul>{summary_items}</ul>
      </article>
      <article class="panel">
        <div class="kicker">Winner</div>
        <h2>{_escape(payload['selected_memory'])}</h2>
        <p>{_escape(payload['human_reason'])}</p>
      </article>
    </section>

    <section class="grid">
      <article class="panel">
        <div class="kicker">Truth State</div>
        <h3>{_escape(payload['truth_state'].get('truth_role'))} / {_escape(payload['truth_state'].get('governance_status'))}</h3>
        <p>Policy trace: {_escape(", ".join(payload['truth_state'].get('policy_trace', [])) or "none")}</p>
      </article>
      <article class="panel">
        <div class="kicker">Scope Health</div>
        <h3>{_escape(payload['health_summary']['health_label'])}</h3>
        <p>Active memories: {_escape(payload['health_summary']['total_active'])}. Conflicts: {_escape(payload['health_summary']['num_conflicts'])}. Stale records: {_escape(payload['health_summary']['num_stale'])}.</p>
      </article>
    </section>

    <section class="stack">
      <article class="panel">
        <div class="kicker">Evidence Trail</div>
        <h2>Grounding behind the winner</h2>
        <ul>{evidence_html or '<li><strong>No evidence events</strong><span>No linked evidence was available.</span></li>'}</ul>
      </article>

      <article class="panel">
        <div class="kicker">Governance Timeline</div>
        <h2>How the system judged this memory</h2>
        <ul>{governance_html or '<li><strong>No governance events</strong><span>No recent events were available.</span></li>'}</ul>
      </article>

      <article class="panel">
        <div class="kicker">Core Signals</div>
        <h2>Internal confidence and transition posture</h2>
        <pre>{_json_block(payload['signal_summary'])}</pre>
      </article>

      <article class="panel">
        <div class="kicker">Why Not</div>
        <h2>Suppressed alternatives</h2>
        <ul>{why_not_html}</ul>
      </article>
    </section>

    <p class="footer-note">This page is generated from the live Aegis core showcase payload, not hand-written demo copy.</p>
  </main>
</body>
</html>
"""
