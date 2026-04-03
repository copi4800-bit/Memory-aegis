from __future__ import annotations

import html
from typing import Any


def _escape(value: Any) -> str:
    return html.escape("" if value is None else str(value))


def render_workflow_shell_html(payload: dict[str, Any], *, title: str = "TruthKeep Workflow Shell") -> str:
    result = payload["result"]
    hero = result["hero"]
    step_cards = "".join(("<article class='step'>" f"<div class='step-id'>{index + 1}</div>" f"<h3>{_escape(step['title'])}</h3>" f"<p>{_escape(step['summary'])}</p>" f"<div class='tool'>{_escape(step['tool'])}</div>" f"<pre>{_escape(step['proof'])}</pre>" "</article>") for index, step in enumerate(result["workflow_steps"]))
    next_actions = "".join(f"<li>{_escape(item)}</li>" for item in result["next_actions"]) or "<li>No immediate next action.</li>"
    ordinary_ops = "".join(f"<li>{_escape(item)}</li>" for item in result["ordinary_lane"].get("operations", [])) or "<li>No ordinary operations listed.</li>"
    escape_hatches = "".join(f"<li>{_escape(item)}</li>" for item in result["operator_escape_hatches"])
    suppressed = "".join(f"<li>{_escape(item)}</li>" for item in result["verification"]["suppressed_preview"]) or "<li>No suppressed preview.</li>"
    timeline_preview = "".join(f"<li>{_escape(item)}</li>" for item in result["truth_transition_timeline"].get("preview", [])) or "<li>No timeline preview.</li>"
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{_escape(title)}</title>
  <style>
    :root {{ --bg:#f6efe5; --panel:rgba(255,255,255,0.94); --line:rgba(25,29,28,0.12); --ink:#191d1c; --muted:#59625d; --accent:#0f766e; --warm:#c76b30; --shadow:0 18px 60px rgba(25,29,28,0.12); }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family:"Aptos","Segoe UI Variable Text",sans-serif; color:var(--ink); background:linear-gradient(180deg,#fcf8f2 0%,var(--bg) 100%); }}
    main {{ max-width:1240px; margin:0 auto; padding:40px 24px 80px; }}
    .hero,.panel,.step {{ background:var(--panel); border:1px solid var(--line); border-radius:28px; box-shadow:var(--shadow); }}
    .hero {{ padding:32px; }}
    .kicker {{ text-transform:uppercase; letter-spacing:.16em; color:var(--accent); font-size:.75rem; font-weight:700; margin-bottom:14px; }}
    h1,h2,h3 {{ margin:0; font-family:Georgia,serif; }}
    h1 {{ font-size:clamp(2.4rem,5vw,4rem); line-height:.96; max-width:10ch; }}
    .lede {{ margin-top:18px; color:var(--muted); max-width:75ch; line-height:1.72; }}
    .chips {{ display:flex; gap:10px; flex-wrap:wrap; margin-top:20px; }}
    .chip {{ padding:10px 14px; border:1px solid var(--line); border-radius:999px; background:rgba(255,255,255,.82); color:var(--muted); }}
    .chip.accent {{ background:rgba(15,118,110,.12); color:var(--ink); font-weight:700; }}
    .steps {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(250px,1fr)); gap:20px; margin-top:24px; }}
    .step {{ padding:22px; position:relative; }}
    .step-id {{ position:absolute; top:18px; right:18px; width:32px; height:32px; display:grid; place-items:center; border-radius:999px; background:rgba(199,107,48,.12); color:var(--warm); font-weight:700; }}
    .tool {{ display:inline-block; margin-top:12px; padding:8px 12px; border-radius:999px; border:1px solid var(--line); color:var(--accent); font-weight:700; }}
    .grid {{ display:grid; grid-template-columns:1fr 1fr; gap:20px; margin-top:24px; }}
    .panel {{ padding:22px; }}
    ul {{ margin:12px 0 0; padding-left:18px; }}
    li,p {{ color:var(--muted); line-height:1.65; }}
    pre {{ margin-top:14px; white-space:pre-wrap; background:#171b19; color:#eef3ef; padding:16px; border-radius:18px; overflow:auto; font-family:"Cascadia Code",Consolas,monospace; }}
    .full {{ margin-top:20px; }}
    @media (max-width: 900px) {{ .grid {{ grid-template-columns:1fr; }} }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <div class="kicker">TruthKeep Workflow Shell</div>
      <h1>{_escape(title)}</h1>
      <p class="lede">A workflow-first loop for correctness-safe memory, with the everyday path kept narrow and operator inspection clearly separated.</p>
      <div class="chips">
        <span class="chip accent">{_escape(hero.get('readiness'))}</span>
        <span class="chip">{_escape(hero.get('health_state'))}</span>
        <span class="chip">{_escape(hero.get('truth_role'))}</span>
        <span class="chip">{_escape(hero.get('governance_status'))}</span>
      </div>
      <p class="lede">{_escape(hero.get('headline'))}</p>
    </section>
    <section class="steps">{step_cards}</section>
    <section class="grid">
      <article class="panel"><h2>Ordinary Path</h2><p>{_escape(result['ordinary_lane'].get('description'))}</p><ul>{ordinary_ops}</ul></article>
      <article class="panel"><h2>Current Truth</h2><p>{_escape(result['current_truth'])}</p><h2 style="margin-top:18px;">Verification</h2><p>{_escape(result['verification']['human_reason'])}</p><ul>{suppressed}</ul></article>
    </section>
    <section class="grid">
      <article class="panel"><h2>Truth Transition Timeline</h2><p>{_escape(result['truth_transition_timeline'].get('story'))}</p><ul>{timeline_preview}</ul></article>
      <article class="panel"><h2>Next Actions</h2><ul>{next_actions}</ul></article>
    </section>
    <section class="panel full"><h2>Operator Escape Hatches</h2><ul>{escape_hatches}</ul></section>
    <section class="panel full"><h2>Workflow Text</h2><pre>{_escape(payload['workflow_text'])}</pre></section>
  </main>
</body>
</html>'''
