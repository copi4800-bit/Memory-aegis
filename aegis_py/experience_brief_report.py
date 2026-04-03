from __future__ import annotations

import html
from typing import Any


def _escape(value: Any) -> str:
    return html.escape("" if value is None else str(value))


def render_experience_brief_html(payload: dict[str, Any], *, title: str = "TruthKeep Experience Brief") -> str:
    result = payload["result"]
    hero = result["hero"]
    summary_html = "".join(f"<li>{_escape(item)}</li>" for item in result["executive_summary"])
    profile_html = "".join(f"<li>{_escape(item)}</li>" for item in result["profile_snapshot"])
    actions_html = "".join(f"<li>{_escape(item)}</li>" for item in result["next_actions"])
    why_not = result.get("why_not", [])
    why_not_html = (
        "".join(
            f"<li><strong>{_escape(item.get('content'))}</strong><span>{_escape(item.get('reason'))}</span></li>"
            for item in why_not
        )
        if why_not
        else "<li><strong>No suppressed alternatives</strong><span>This truth stood alone for the current query.</span></li>"
    )
    compressed = result["compressed_snapshot"]
    runtime = result["runtime_snapshot"]
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{_escape(title)}</title>
  <style>
    :root {{
      --bg: #f5efe6;
      --panel: rgba(255,255,255,0.92);
      --line: rgba(32,36,34,0.12);
      --ink: #202422;
      --muted: #5a645d;
      --accent: #0f766e;
      --warm: #c76a2c;
      --shadow: 0 18px 60px rgba(32,36,34,0.12);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Aptos", "Segoe UI Variable Text", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(15,118,110,0.15), transparent 30%),
        radial-gradient(circle at top right, rgba(199,106,44,0.14), transparent 28%),
        linear-gradient(180deg, #faf5ee 0%, var(--bg) 100%);
    }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 40px 24px 80px; }}
    .hero, .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 28px;
      box-shadow: var(--shadow);
    }}
    .hero {{ padding: 32px; }}
    .hero h1 {{ margin: 0; font-family: Georgia, serif; font-size: clamp(2.4rem, 5vw, 4rem); line-height: 0.96; max-width: 11ch; }}
    .kicker {{ text-transform: uppercase; letter-spacing: 0.16em; font-size: 0.75rem; color: var(--accent); font-weight: 700; margin-bottom: 14px; }}
    .lede {{ margin-top: 18px; max-width: 70ch; color: var(--muted); line-height: 1.7; }}
    .chips {{ display: flex; flex-wrap: wrap; gap: 10px; margin-top: 20px; }}
    .chip {{ padding: 10px 14px; border-radius: 999px; border: 1px solid var(--line); background: rgba(255,255,255,0.8); color: var(--muted); }}
    .chip.accent {{ background: rgba(15,118,110,0.12); color: var(--ink); font-weight: 700; }}
    .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 16px; margin-top: 24px; }}
    .metric {{ padding: 16px; border-radius: 20px; background: rgba(255,255,255,0.72); border: 1px solid var(--line); }}
    .metric strong {{ display: block; font-size: 1.65rem; margin-top: 8px; }}
    .grid {{ display: grid; grid-template-columns: 1.2fr 1fr; gap: 20px; margin-top: 24px; }}
    .panel {{ padding: 22px; }}
    h2 {{ margin: 0 0 14px; font-family: Georgia, serif; font-size: 1.5rem; }}
    p, li, span {{ color: var(--muted); line-height: 1.65; }}
    ul {{ margin: 0; padding-left: 18px; }}
    li strong {{ display: block; color: var(--ink); margin-bottom: 4px; }}
    .full {{ margin-top: 20px; }}
    pre {{ margin: 0; white-space: pre-wrap; background: #171b19; color: #eef3ef; padding: 18px; border-radius: 20px; overflow: auto; font-family: "Cascadia Code", Consolas, monospace; }}
    @media (max-width: 900px) {{ .grid {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <div class="kicker">TruthKeep Product Brief</div>
      <h1>{_escape(title)}</h1>
      <p class="lede">A product-facing memory briefing that turns TruthKeep's governed core into one readable experience: current truth, confidence, profile fit, runtime health, compressed-tier readiness, and what to do next.</p>
      <div class="chips">
        <span class="chip accent">{_escape(hero['label'])}</span>
        <span class="chip">{_escape(hero['truth_role'])}</span>
        <span class="chip">{_escape(hero['governance_status'])}</span>
        <span class="chip">compressed passed={_escape(compressed['passed'])}</span>
      </div>
      <div class="metrics">
        <article class="metric"><span>Trust</span><strong>{float(hero['trust_score'] or 0.0):.3f}</strong></article>
        <article class="metric"><span>Readiness</span><strong>{float(hero['readiness_score'] or 0.0):.3f}</strong></article>
        <article class="metric"><span>Memories</span><strong>{_escape(runtime['memory_count'])}</strong></article>
        <article class="metric"><span>Compressed Coverage</span><strong>{float(compressed['coverage_rate'] or 0.0):.3f}</strong></article>
      </div>
    </section>
    <section class="grid">
      <article class="panel">
        <h2>What TruthKeep Believes</h2>
        <p>{_escape(hero['selected_memory'])}</p>
        <h2 style="margin-top:22px;">Why It Believes This</h2>
        <p>{_escape(result['human_reason'])}</p>
      </article>
      <article class="panel">
        <h2>Executive Summary</h2>
        <ul>{summary_html}</ul>
      </article>
    </section>
    <section class="grid">
      <article class="panel">
        <h2>Profile Snapshot</h2>
        <ul>{profile_html}</ul>
      </article>
      <article class="panel">
        <h2>Next Actions</h2>
        <ul>{actions_html}</ul>
      </article>
    </section>
    <section class="grid">
      <article class="panel">
        <h2>Runtime Discipline</h2>
        <p>health_state={_escape(runtime['health_state'])} | open_conflicts={_escape(runtime['open_conflicts'])} | historical_rows={_escape(runtime['historical_rows'])} | smilodon={float(runtime['smilodon_peak_retirement_pressure'] or 0.0):.3f}</p>
      </article>
      <article class="panel">
        <h2>Suppressed Alternatives</h2>
        <ul>{why_not_html}</ul>
      </article>
    </section>
    <section class="panel full">
      <h2>Full Brief</h2>
      <pre>{_escape(payload['brief_text'])}</pre>
    </section>
  </main>
</body>
</html>"""
