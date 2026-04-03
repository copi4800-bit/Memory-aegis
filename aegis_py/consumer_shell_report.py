from __future__ import annotations

import html
from typing import Any


def _escape(value: Any) -> str:
    return html.escape("" if value is None else str(value))


def render_consumer_shell_html(payload: dict[str, Any], *, title: str = "TruthKeep Consumer Shell") -> str:
    result = payload["result"]
    hero = result["hero"]
    actions = "".join(f"<li><strong>{_escape(item['tool'])}</strong><span>{_escape(item['why'])}</span></li>" for item in result["primary_actions"])
    defaults = "".join(f"<li>{_escape(item)}</li>" for item in result["default_operations"])
    highlights = "".join(f"<li>{_escape(item)}</li>" for item in result["advanced_highlights"])
    guidance = "".join(f"<li>{_escape(item)}</li>" for item in result["guidance"]) or "<li>No setup guidance required.</li>"
    next_actions = "".join(f"<li>{_escape(item)}</li>" for item in result["next_actions"]) or "<li>No immediate next action.</li>"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{_escape(title)}</title>
  <style>
    :root {{
      --bg: #f6efe5;
      --panel: rgba(255,255,255,0.92);
      --line: rgba(25,29,28,0.12);
      --ink: #191d1c;
      --muted: #59625d;
      --accent: #0f766e;
      --warm: #c76b30;
      --shadow: 0 18px 60px rgba(25,29,28,0.12);
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: "Aptos", "Segoe UI Variable Text", sans-serif; color: var(--ink); background: linear-gradient(180deg, #fbf7f1 0%, var(--bg) 100%); }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 40px 24px 80px; }}
    .hero, .panel {{ background: var(--panel); border: 1px solid var(--line); border-radius: 28px; box-shadow: var(--shadow); }}
    .hero {{ padding: 32px; }}
    .kicker {{ text-transform: uppercase; letter-spacing: 0.16em; color: var(--accent); font-size: 0.75rem; font-weight: 700; margin-bottom: 14px; }}
    h1, h2 {{ margin: 0; font-family: Georgia, serif; }}
    h1 {{ font-size: clamp(2.4rem, 5vw, 4rem); line-height: 0.96; max-width: 10ch; }}
    .lede {{ margin-top: 18px; color: var(--muted); max-width: 72ch; line-height: 1.7; }}
    .chips {{ display: flex; gap: 10px; flex-wrap: wrap; margin-top: 20px; }}
    .chip {{ padding: 10px 14px; border: 1px solid var(--line); border-radius: 999px; background: rgba(255,255,255,0.8); color: var(--muted); }}
    .chip.accent {{ background: rgba(15,118,110,0.12); color: var(--ink); font-weight: 700; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 24px; }}
    .panel {{ padding: 22px; }}
    ul {{ margin: 0; padding-left: 18px; }}
    li {{ color: var(--muted); margin: 10px 0; line-height: 1.65; }}
    li strong {{ display: block; color: var(--ink); margin-bottom: 4px; }}
    pre {{ margin: 0; white-space: pre-wrap; background: #171b19; color: #eef3ef; padding: 18px; border-radius: 20px; overflow: auto; font-family: "Cascadia Code", Consolas, monospace; }}
    .full {{ margin-top: 20px; }}
    @media (max-width: 900px) {{ .grid {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <div class="kicker">TruthKeep Consumer Shell</div>
      <h1>{_escape(title)}</h1>
      <p class="lede">A first-run product shell that tells a new user whether TruthKeep is ready, what it currently believes, which tools matter most, and what to do next.</p>
      <div class="chips">
        <span class="chip accent">{_escape(hero['readiness'])}</span>
        <span class="chip">{_escape(hero['health_state'])}</span>
        <span class="chip">{_escape(result['query'])}</span>
      </div>
    </section>
    <section class="grid">
      <article class="panel">
        <h2>Current Brief</h2>
        <p>{_escape(hero['headline'])}</p>
      </article>
      <article class="panel">
        <h2>Start Here</h2>
        <ul>{actions}</ul>
      </article>
    </section>
    <section class="grid">
      <article class="panel">
        <h2>Everyday Tools</h2>
        <ul>{defaults}</ul>
      </article>
      <article class="panel">
        <h2>Advanced Highlights</h2>
        <ul>{highlights}</ul>
      </article>
    </section>
    <section class="grid">
      <article class="panel">
        <h2>Setup Guidance</h2>
        <ul>{guidance}</ul>
      </article>
      <article class="panel">
        <h2>Next Actions</h2>
        <ul>{next_actions}</ul>
      </article>
    </section>
    <section class="panel full">
      <h2>Shell Text</h2>
      <pre>{_escape(payload['shell_text'])}</pre>
    </section>
  </main>
</body>
</html>"""
