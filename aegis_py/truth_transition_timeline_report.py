from __future__ import annotations

import html
from typing import Any


def _escape(value: Any) -> str:
    return html.escape("" if value is None else str(value))


def render_truth_transition_timeline_html(payload: dict[str, Any], *, title: str = "TruthKeep Truth Transition Timeline") -> str:
    result = payload["result"]
    hero = result["hero"]
    winner_path = "".join(("<li>" f"<strong>{_escape(item['label'])}</strong>" f"<span>{_escape(item['created_at'] or 'unknown')} | {_escape(item['summary'])}</span>" "</li>") for item in result["winner_path"]) or "<li><strong>No winner path entries</strong><span>The current truth has no recorded transition path yet.</span></li>"
    suppressed = "".join(("<li>" f"<strong>{_escape(item['content'])}</strong>" f"<span>suppressed_reason={_escape(item['reason'])} | latest_state={_escape(item['latest_state'])} | latest_reason={_escape(item['latest_reason'])} | at={_escape(item['latest_at'] or 'unknown')}</span>" "</li>") for item in result["suppressed_memories"]) or "<li><strong>No suppressed memories</strong><span>No competing fact was suppressed for this query.</span></li>"
    scope_events = "".join(("<li>" f"<strong>{_escape(item['label'])}</strong>" f"<span>{_escape(item['created_at'] or 'unknown')} | {_escape(item['summary'])}</span>" "</li>") for item in result["scope_events"]) or "<li><strong>No scope events</strong><span>No recent governance pulse was recorded for this scope.</span></li>"
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{_escape(title)}</title>
  <style>
    :root {{ --bg:#f6efe5; --panel:rgba(255,255,255,0.94); --line:rgba(25,29,28,0.12); --ink:#191d1c; --muted:#59625d; --accent:#0f766e; --shadow:0 18px 60px rgba(25,29,28,0.12); }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family:"Aptos","Segoe UI Variable Text",sans-serif; color:var(--ink); background:linear-gradient(180deg,#fcf8f2 0%,var(--bg) 100%); }}
    main {{ max-width:1240px; margin:0 auto; padding:40px 24px 80px; }}
    .hero,.panel {{ background:var(--panel); border:1px solid var(--line); border-radius:28px; box-shadow:var(--shadow); }}
    .hero {{ padding:32px; }}
    .kicker {{ text-transform:uppercase; letter-spacing:.16em; color:var(--accent); font-size:.75rem; font-weight:700; margin-bottom:14px; }}
    h1,h2 {{ margin:0; font-family:Georgia,serif; }}
    h1 {{ font-size:clamp(2.4rem,5vw,4rem); line-height:.96; max-width:10ch; }}
    .lede {{ margin-top:18px; color:var(--muted); max-width:78ch; line-height:1.72; }}
    .chips {{ display:flex; gap:10px; flex-wrap:wrap; margin-top:20px; }}
    .chip {{ padding:10px 14px; border:1px solid var(--line); border-radius:999px; background:rgba(255,255,255,.82); color:var(--muted); }}
    .chip.accent {{ background:rgba(15,118,110,.12); color:var(--ink); font-weight:700; }}
    .grid {{ display:grid; grid-template-columns:1fr 1fr; gap:20px; margin-top:24px; }}
    .panel {{ padding:22px; }}
    ul {{ margin:12px 0 0; padding-left:18px; }}
    li {{ color:var(--muted); line-height:1.65; margin-bottom:10px; }}
    li strong {{ display:block; color:var(--ink); margin-bottom:4px; }}
    pre {{ margin-top:14px; white-space:pre-wrap; background:#171b19; color:#eef3ef; padding:16px; border-radius:18px; overflow:auto; font-family:"Cascadia Code",Consolas,monospace; }}
    .full {{ margin-top:20px; }}
    @media (max-width: 900px) {{ .grid {{ grid-template-columns:1fr; }} }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <div class="kicker">Truth Transition Timeline</div>
      <h1>{_escape(title)}</h1>
      <p class="lede">See how TruthKeep moved from older facts to the current truth, which competing memories were suppressed, and which governance events shaped the field.</p>
      <div class="chips">
        <span class="chip accent">{_escape(hero.get('truth_role'))}</span>
        <span class="chip">{_escape(hero.get('governance_status'))}</span>
        <span class="chip">winner_memory_id={_escape(hero.get('memory_id') or 'unknown')}</span>
      </div>
      <p class="lede">{_escape(hero.get('selected_memory'))}</p>
      <p class="lede">{_escape(result.get('transition_story'))}</p>
    </section>
    <section class="grid">
      <article class="panel"><h2>Winner Path</h2><ul>{winner_path}</ul></article>
      <article class="panel"><h2>Superseded Memories</h2><ul>{suppressed}</ul></article>
    </section>
    <section class="panel full"><h2>Scope Governance Pulse</h2><ul>{scope_events}</ul></section>
    <section class="panel full"><h2>Timeline Text</h2><pre>{_escape(payload['timeline_text'])}</pre></section>
  </main>
</body>
</html>'''
