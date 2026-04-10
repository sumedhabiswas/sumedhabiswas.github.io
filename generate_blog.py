#!/usr/bin/env python3
"""
generate_blog.py
================
Converts Markdown files in blog/posts/ into individual HTML pages,
and updates the blog card list in index.html.

Usage:
    python generate_blog.py

Post format (blog/posts/YYYY-MM-DD-slug.md):
---
title: My Post Title
date: 2026-04-10
tag: Astrodynamics
summary: One sentence summary shown in the card.
---

Full Markdown content here...

Requirements:
    pip install markdown python-frontmatter
"""

import os
import re
import json
import glob
import shutil
import frontmatter
import markdown
from datetime import datetime
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT        = Path(__file__).parent
POSTS_DIR   = ROOT / "blog" / "posts"
OUTPUT_DIR  = ROOT / "blog"
INDEX_HTML  = ROOT / "index.html"
TEMPLATE    = ROOT / "blog" / "post_template.html"

POSTS_DIR.mkdir(parents=True, exist_ok=True)

# ── Post HTML template ───────────────────────────────────────────────────────
POST_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} | Sumedha Biswas</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&family=DM+Mono:wght@300;400&family=Outfit:wght@300;400;500&display=swap" rel="stylesheet">
<!-- MathJax for equations -->
<script>
  MathJax = {{ tex: {{ inlineMath: [['$','$'],['\\\\(','\\\\)']] }}, svg: {{ fontCache: 'global' }} }};
</script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js" async></script>
<style>
:root {{
  --bg: #09090f; --bg2: #0e0e1a; --surface: #17172a;
  --border: rgba(255,255,255,0.07);
  --gold: #c9a84c; --gold-dim: #a07830;
  --text: #e8e4da; --text-dim: #8a8480; --text-mid: #b8b0a0;
  --accent: #5b8dd9; --accent2: #7ec8c8;
  --serif: 'Cormorant Garamond', Georgia, serif;
  --mono:  'DM Mono', monospace;
  --sans:  'Outfit', sans-serif;
}}
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
html {{ scroll-behavior: smooth; }}
body {{ background: var(--bg); color: var(--text); font-family: var(--sans); font-weight: 300; line-height: 1.7; padding: 0; }}
::selection {{ background: rgba(201,168,76,0.18); color: var(--gold); }}
::-webkit-scrollbar {{ width: 4px; }}
::-webkit-scrollbar-track {{ background: var(--bg); }}
::-webkit-scrollbar-thumb {{ background: var(--gold-dim); border-radius: 2px; }}

nav {{
  position: fixed; top: 0; left: 0; right: 0; z-index: 100;
  height: 64px; display: flex; align-items: center; justify-content: space-between;
  padding: 0 2.5rem;
  background: rgba(9,9,15,0.9); backdrop-filter: blur(14px);
  border-bottom: 1px solid var(--border);
}}
.nav-logo {{ font-family: var(--serif); font-size: 1.2rem; color: var(--gold); text-decoration: none; }}
.nav-back {{
  font-family: var(--mono); font-size: 0.7rem; letter-spacing: 0.12em;
  text-transform: uppercase; color: var(--text-dim); text-decoration: none;
  border: 1px solid var(--border); padding: 0.4rem 1rem; border-radius: 2px;
  transition: all 0.2s;
}}
.nav-back:hover {{ color: var(--gold); border-color: var(--gold-dim); }}

.post-wrap {{
  max-width: 720px; margin: 0 auto;
  padding: 6rem 2rem 5rem;
}}

.post-meta {{
  margin-bottom: 2.5rem;
}}

.post-tag {{
  font-family: var(--mono); font-size: 0.65rem; letter-spacing: 0.12em;
  text-transform: uppercase; padding: 0.2rem 0.6rem; border-radius: 2px;
  background: rgba(91,141,217,0.1); color: var(--accent);
  border: 1px solid rgba(91,141,217,0.2); display: inline-block; margin-bottom: 1rem;
}}

.post-date {{
  font-family: var(--mono); font-size: 0.72rem; color: var(--gold);
  letter-spacing: 0.08em; display: block; margin-bottom: 0.8rem;
}}

.post-wrap h1 {{
  font-family: var(--serif); font-size: clamp(2rem, 5vw, 3rem);
  font-weight: 300; color: var(--text); line-height: 1.15; margin-bottom: 0.5rem;
}}

.post-summary {{
  font-size: 1rem; color: var(--text-mid); margin-bottom: 2.5rem;
  padding-bottom: 2rem; border-bottom: 1px solid var(--border);
  font-style: italic;
}}

/* ── Article body ── */
.post-body {{ font-size: 1rem; color: var(--text-mid); line-height: 1.85; }}
.post-body h2 {{ font-family: var(--serif); font-size: 1.6rem; font-weight: 400; color: var(--text); margin: 2.5rem 0 0.8rem; }}
.post-body h3 {{ font-family: var(--serif); font-size: 1.2rem; font-weight: 400; color: var(--text); margin: 2rem 0 0.6rem; }}
.post-body p  {{ margin-bottom: 1.2rem; }}
.post-body a  {{ color: var(--accent2); text-decoration: underline; text-underline-offset: 3px; }}
.post-body a:hover {{ color: var(--gold); }}
.post-body blockquote {{
  border-left: 3px solid var(--gold); margin: 1.5rem 0;
  padding: 0.8rem 1.2rem; background: var(--surface); border-radius: 0 3px 3px 0;
  color: var(--text-mid); font-style: italic;
}}
.post-body code {{
  font-family: var(--mono); font-size: 0.85em;
  background: var(--surface); padding: 0.15em 0.4em; border-radius: 3px;
  color: var(--accent2);
}}
.post-body pre {{
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 4px; padding: 1.2rem; overflow-x: auto; margin: 1.5rem 0;
}}
.post-body pre code {{ background: none; padding: 0; }}
.post-body img {{
  max-width: 100%; border-radius: 4px; margin: 1.5rem 0;
  border: 1px solid var(--border);
}}
.post-body ul, .post-body ol {{ padding-left: 1.5rem; margin-bottom: 1.2rem; }}
.post-body li {{ margin-bottom: 0.3rem; }}
.post-body hr {{ border: none; border-top: 1px solid var(--border); margin: 2.5rem 0; }}
.post-body table {{ width: 100%; border-collapse: collapse; margin: 1.5rem 0; font-size: 0.9rem; }}
.post-body th, .post-body td {{ padding: 0.6rem 0.8rem; border: 1px solid var(--border); text-align: left; }}
.post-body th {{ background: var(--surface); color: var(--text); }}

footer {{
  border-top: 1px solid var(--border); padding: 2rem;
  text-align: center; font-family: var(--mono); font-size: 0.65rem;
  letter-spacing: 0.1em; color: var(--text-dim); margin-top: 4rem;
}}
</style>
</head>
<body>
<nav>
  <a href="../index.html" class="nav-logo">SB</a>
  <a href="../index.html#blog" class="nav-back">← All Posts</a>
</nav>

<div class="post-wrap">
  <div class="post-meta">
    <span class="post-tag">{tag}</span>
    <span class="post-date">{date}</span>
    <h1>{title}</h1>
    <p class="post-summary">{summary}</p>
  </div>
  <div class="post-body">
{body}
  </div>
</div>

<footer>
  <p>© 2026 Sumedha Biswas &nbsp;·&nbsp; <a href="../index.html" style="color: var(--gold-dim);">sumedhabiswas.github.io</a></p>
</footer>
</body>
</html>
"""

# ── Card HTML snippet (injected into index.html) ─────────────────────────────
CARD_TEMPLATE = """\
      <a href="blog/{slug}.html" class="blog-card">
        <div class="blog-card-date">{date}</div>
        <h3>{title}</h3>
        <p>{summary}</p>
        <span class="blog-card-tag">{tag}</span>
      </a>"""

def slugify(filename: str) -> str:
    """Extract slug from filename like 2026-04-10-my-post.md → 2026-04-10-my-post"""
    return Path(filename).stem

def format_date(d) -> str:
    if isinstance(d, str):
        try:
            d = datetime.strptime(d, "%Y-%m-%d")
        except ValueError:
            return d
    return d.strftime("%d %b %Y").lstrip("0")

def build_post(md_path: Path) -> dict:
    """Parse a Markdown post and return metadata dict."""
    post = frontmatter.load(md_path)
    slug = slugify(md_path.name)

    title   = post.get("title",   "Untitled Post")
    date    = format_date(post.get("date", ""))
    tag     = post.get("tag",     "Note")
    summary = post.get("summary", "")

    # Convert Markdown body to HTML
    md_ext  = ["fenced_code", "tables", "footnotes", "attr_list", "toc"]
    body_html = markdown.markdown(post.content, extensions=md_ext)

    # Write post HTML
    out_path = OUTPUT_DIR / f"{slug}.html"
    html = POST_TEMPLATE.format(
        title=title, date=date, tag=tag,
        summary=summary, body=body_html
    )
    out_path.write_text(html, encoding="utf-8")
    print(f"  ✓  {slug}.html")

    return {"slug": slug, "title": title, "date": date, "tag": tag, "summary": summary,
            "raw_date": post.get("date", "1970-01-01")}

def update_index(cards_html: str):
    """Replace the blog-list contents in index.html."""
    html = INDEX_HTML.read_text(encoding="utf-8")

    # Replace everything between <!-- BLOG_START --> and <!-- BLOG_END -->
    pattern = r'(<!-- BLOG_START -->).*?(<!-- BLOG_END -->)'
    replacement = f'<!-- BLOG_START -->\n{cards_html}\n      <!-- BLOG_END -->'

    if re.search(pattern, html, re.DOTALL):
        new_html = re.sub(pattern, replacement, html, flags=re.DOTALL)
    else:
        # Fallback: replace the blog-empty placeholder
        empty = '<div class="blog-empty">'
        end   = '</div>'
        idx   = html.find(empty)
        if idx == -1:
            print("  ⚠  Could not find injection point in index.html. Add <!-- BLOG_START --><!-- BLOG_END --> inside #blog-list.")
            return
        end_idx = html.find(end, idx) + len(end)
        new_html = html[:idx] + f'<!-- BLOG_START -->\n{cards_html}\n      <!-- BLOG_END -->' + html[end_idx:]

    INDEX_HTML.write_text(new_html, encoding="utf-8")
    print(f"  ✓  index.html blog section updated ({len(cards_html)} chars injected)")

def main():
    md_files = sorted(POSTS_DIR.glob("*.md"), reverse=True)  # newest first

    if not md_files:
        print("No posts found in blog/posts/. Create a .md file there to get started.")
        print("\nExample filename:  blog/posts/2026-04-10-keplers-laws.md")
        print("Required frontmatter:\n  ---\n  title: Kepler's Laws and Why They Matter\n  date: 2026-04-10\n  tag: Astrodynamics\n  summary: A short summary for the card.\n  ---\n")
        return

    print(f"Found {len(md_files)} post(s). Building...")
    posts = []
    for f in md_files:
        try:
            posts.append(build_post(f))
        except Exception as e:
            print(f"  ✗  {f.name}: {e}")

    # Build card HTML
    cards = "\n".join(CARD_TEMPLATE.format(**p) for p in posts)
    update_index(cards)
    print(f"\nDone. {len(posts)} post(s) built.")

if __name__ == "__main__":
    main()
