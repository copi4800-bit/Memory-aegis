from __future__ import annotations

import html
from typing import Any


def _escape(value: Any) -> str:
    return html.escape("" if value is None else str(value))


def render_dashboard_shell_html(payload: dict[str, Any], *, title: str = "TruthKeep Dashboard Shell") -> str:
    result = payload["result"]
    hero = result["hero"]
    section_html = "".join(
        (
            "<article class='panel'>"
            f"<h2>{_escape(section['title'])}</h2>"
            f"<p>{_escape(section['summary'])}</p>"
            "<ul>"
            + "".join(
                (
                    f"<li><strong>{_escape(item.get('tool') or item.get('title') or 'item')}</strong><span>{_escape(item.get('why') or item.get('summary') or '')}</span></li>"
                    if isinstance(item, dict)
                    else f"<li>{_escape(item)}</li>"
                )
                for item in section["items"]
            )
            + "</ul></article>"
        )
        for section in result["sections"]
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{_escape(title)}</title>
  <style>
    :root {{
      --bg: #f7f0e6;
      --panel: rgba(255,255,255,0.94);
      --line: rgba(25,29,28,0.12);
      --ink: #191d1c;
      --muted: #5a635f;
      --accent: #0f766e;
      --shadow: 0 20px 60px rgba(25,29,28,0.12);
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: "Aptos", "Segoe UI Variable Text", sans-serif; color: var(--ink); background: linear-gradient(180deg, #fcf8f2 0%, var(--bg) 100%); }}
    main {{ max-width: 1240px; margin: 0 auto; padding: 40px 24px 80px; }}
    .hero, .panel {{ background: var(--panel); border: 1px solid var(--line); border-radius: 28px; box-shadow: var(--shadow); }}
    .hero {{ padding: 32px; }}
    .kicker {{ text-transform: uppercase; letter-spacing: 0.16em; color: var(--accent); font-size: 0.75rem; font-weight: 700; margin-bottom: 14px; }}
    h1, h2 {{ margin: 0; font-family: Georgia, serif; }}
    h1 {{ font-size: clamp(2.5rem, 5vw, 4.1rem); line-height: 0.95; max-width: 9ch; }}
    .lede {{ margin-top: 18px; color: var(--muted); max-width: 75ch; line-height: 1.72; }}
    .chips {{ display: flex; gap: 10px; flex-wrap: wrap; margin-top: 20px; }}
    .chip {{ padding: 10px 14px; border: 1px solid var(--line); border-radius: 999px; background: rgba(255,255,255,0.82); color: var(--muted); }}
    .chip.accent {{ background: rgba(15,118,110,0.12); color: var(--ink); font-weight: 700; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-top: 24px; }}
    .panel {{ padding: 22px; }}
    p, li, span {{ color: var(--muted); line-height: 1.65; }}
    ul {{ margin: 14px 0 0; padding-left: 18px; }}
    li strong {{ display: block; color: var(--ink); margin-bottom: 4px; }}
    pre {{ margin: 0; white-space: pre-wrap; background: #171b19; color: #eef3ef; padding: 18px; border-radius: 20px; overflow: auto; font-family: "Cascadia Code", Consolas, monospace; }}
    .full {{ margin-top: 20px; }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <div class="kicker">TruthKeep Unified Dashboard</div>
      <h1>{_escape(title)}</h1>
      <p class="lede">A single destination that unifies first-run guidance, current-truth briefing, and deep inspection into one dashboard-level experience.</p>
      <div class="chips">
        <span class="chip accent">{_escape(hero.get('readiness'))}</span>
        <span class="chip">{_escape(hero.get('health_state'))}</span>
        <span class="chip">{_escape(hero.get('truth_role'))}</span>
        <span class="chip">{_escape(hero.get('governance_status'))}</span>
      </div>
      <p class="lede">{_escape(hero.get('headline'))}</p>
    </section>
    <section class="grid">{section_html}</section>
    <section class="panel full">
      <h2>Dashboard Text</h2>
      <pre>{_escape(payload['dashboard_text'])}</pre>
    </section>
  </main>
</body>
</html>"""
