#!/usr/bin/env python3
"""Generate the HTML CV site from cv.md."""

from html import escape
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "cv.md"
OUTPUT = ROOT / "cv-site" / "index.html"


STYLESHEET = """
@font-face {
  font-family: 'GT America Mono';
  font-style: normal;
  font-weight: 400;
  font-display: swap;
  src: url(https://oxide.computer/fonts/GT-America-Mono-Regular-OCC.woff2) format('woff2');
}

@font-face {
  font-family: 'SuisseIntl';
  font-style: normal;
  font-weight: 400;
  font-display: swap;
  src: url(https://oxide.computer/fonts/SuisseIntl-Regular-WebS.woff2) format('woff2');
}

@font-face {
  font-family: 'SuisseIntl';
  font-style: normal;
  font-weight: 500;
  font-display: swap;
  src: url(https://oxide.computer/fonts/SuisseIntl-Medium-WebS.woff2) format('woff2');
}
* { box-sizing: border-box; }

html { scroll-behavior: smooth; }

body {
  margin: 2em;
  color: #000;
  background: #fff;
  font-family: 'SuisseIntl', sans-serif;
  font-size: 1rem;
  line-height: 1.4;
}

a {
  color: inherit;
  text-underline-offset: .15em;
}

h1, h2, h3, .location, .contact, .title, .dates, .site-footer {
  font-family: 'GT America Mono', monospace;
  font-weight: 400;
}

.site-header { margin-bottom: 2rem; }
main {
  font-size: 1.1rem;
  line-height: 1.55;
}

.identity {
  display: block;
}

h1 {
  margin: 0;
  font-size: 2rem;
  line-height: 1.1;
}

.location {
  margin: .5rem 0 0;
  font-size: .9rem;
}

.contact {
  display: block;
  margin: .75rem 0 0;
  font-size: .82rem;
}

.contact > span {
  display: block;
  margin-top: .35rem;
}

.contact > span:first-child { margin-top: 0; }

.contact > span::before {
  content: '·';
  margin-right: .4rem;
}


.title {
  margin: 2rem 0 0;
  font-size: 1.2rem;
  line-height: 1.2;
}

.section { margin-top: 2rem; }

.section h2 {
  margin: 0 0 .75rem;
  font-size: 1.35rem;
  line-height: 1.35;
}

.entry { margin-top: 1.2rem; }
.entry + .entry { margin-top: 2rem; }
.experience .entry + .entry { margin-top: 3rem; }

.entry-heading {
  margin: 0 0 .75rem;
  font-size: 1.15rem;
  line-height: 1.4;
}

.entry-heading .role { font-weight: 500; }
.role-company .company::before { content: ' | '; }
strong { font-weight: 500; }

.entry-heading .dates {
  display: block;
  margin-top: .35rem;
  font-size: .82rem;
  font-weight: 400;
  white-space: normal;
}
p { margin: .75rem 0 0; }
.entry > p:first-of-type { margin-top: 0; }

ul {
  margin: .75rem 0 0;
  padding-left: 1.25rem;
}

li { padding-left: .2rem; }
li + li { margin-top: .5rem; }

.cta-gap { margin-top: .4rem; }

.site-footer {
  margin-top: 3rem;
  font-size: .78rem;
}
.footer-separator { margin: 0 .25rem; }
.source { white-space: nowrap; }

.page-break { display: none; }

@media (max-width: 620px) {
  .site-footer > a,
  .site-footer > .source {
    display: block;
    margin-top: .35rem;
  }
  .site-footer > a:first-child { margin-top: 0; }
  .footer-separator { display: none; }
  .entry-heading .role-company { display: block; }
  .entry-heading .company { display: block; }
  .role-company .company::before { content: ''; }
}

@media print {
  .page-break { display: block; break-before: page; }
  a { color: inherit; }
}
"""


HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Ricky Miller — Senior Software Engineer">
  <title>Ricky Miller — CV</title>
  <style>{stylesheet}</style>
</head>
<body>
{body}
</body>
</html>
"""


def read_document():
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    metadata = {}
    index = 0
    if lines and lines[0] == "---":
        index = 1
        while index < len(lines) and lines[index] != "---":
            key, value = lines[index].split(":", 1)
            metadata[key.strip()] = value.strip()
            index += 1
        index += 1
    return metadata, lines[index:]


def inline(text: str) -> str:
    """Convert the small Markdown subset used by the CV to HTML."""
    text = re.sub(r"\s--\s", " – ", text)
    parts = re.split(r"(\*\*.*?\*\*|\[.*?\]\(.*?\))", text)
    converted = []
    for part in parts:
        if part.startswith("**") and part.endswith("**"):
            converted.append(f"<strong>{escape(part[2:-2])}</strong>")
            continue
        link = re.fullmatch(r"\[(.*?)\]\((.*?)\)", part)
        if link:
            label, url = link.groups()
            converted.append(
                f'<a href="{escape(url, quote=True)}">{inline(label)}</a>'
            )
            continue
        converted.append(escape(part))
    return "".join(converted)


def header(metadata):
    email = metadata["email"]
    website = metadata["website"]
    github = metadata["github"]
    return f"""<header class="site-header">
  <div class="identity">
    <h1>{inline(metadata['name'])}</h1>
    <p class="location">{inline(metadata['location'])}</p>
  </div>
  <nav class="contact" aria-label="Contact">
    <span><a href="mailto:{escape(email, quote=True)}">{escape(email)}</a></span>
    <span><a href="{escape(website, quote=True)}">{escape(website.removeprefix('https://'))}</a></span>
    <span><a href="{escape(github, quote=True)}">{escape(github.removeprefix('https://'))}</a></span>
  </nav>
    <h2 class="title">{inline(metadata['title'])}</h2>
</header>"""


def render_body(lines):
    output = []
    section_open = False
    entry_open = False
    paragraph = []
    bullets = []

    def flush_paragraph():
        nonlocal paragraph
        if paragraph:
            output.append(f"<p>{inline(' '.join(paragraph))}</p>")
            paragraph = []

    def flush_bullets():
        nonlocal bullets
        if bullets:
            output.append("<ul>")
            output.extend(f"  <li>{item}</li>" for item in bullets)
            output.append("</ul>")
            bullets = []

    def flush_block():
        flush_paragraph()
        flush_bullets()

    def close_entry():
        nonlocal entry_open
        flush_block()
        if entry_open:
            output.append("</article>")
            entry_open = False

    def close_section():
        nonlocal section_open
        close_entry()
        if section_open:
            output.append("</section>")
            section_open = False

    for line in lines + [""]:
        if line == "<!-- pagebreak -->":
            close_entry()
            output.append('<div class="page-break" aria-hidden="true"></div>')
            continue

        if line == "<!-- cta-gap -->":
            close_entry()
            output.append('<div class="cta-gap" aria-hidden="true"></div>')
            continue

        match = re.match(r"^## (.+)$", line)
        if match:
            close_section()
            section_open = True
            section_name = match.group(1)
            output.append(
                f'<section class="section{" experience" if section_name == "Professional Experience" else ""}">'
            )
            output.append(f"<h2>{inline(section_name)}</h2>")
            continue

        match = re.match(r"^### (.+?) \| (.+?) \| (.+)$", line)
        if match:
            close_entry()
            role, company, dates = (inline(value) for value in match.groups())
            output.append('<article class="entry">')
            output.append(
                f'<h3 class="entry-heading"><span class="role-company">'
                f'<span class="role">{role}</span>'
                f'<span class="company">{company}</span></span>'
                f'<time class="dates">{dates}</time></h3>'
            )
            entry_open = True
            continue

        match = re.match(r"^### (.+)$", line)
        if match:
            close_entry()
            title = match.group(1)
            if section_open:
                output.append('<article class="entry">')
                if " @ " in title:
                    name, organization = title.split(" @ ", 1)
                    heading = (
                        f'<span>{inline(name)} '
                        f'<span class="company">@ {inline(organization)}</span></span>'
                    )
                else:
                    heading = inline(title)
                output.append(f'<h3 class="entry-heading">{heading}</h3>')
                entry_open = True
            continue

        if line.startswith("- "):
            flush_paragraph()
            bullets.append(inline(line[2:]))
        elif line.strip():
            paragraph.append(line.strip())
        else:
            flush_block()

    close_section()
    return "\n".join(output)


def main():
    metadata, lines = read_document()
    body = header(metadata) + "\n<main>\n" + render_body(lines) + "\n</main>"
    body += """
<footer class="site-footer">
  <a href="https://ricky.codes">ricky.codes</a>
  <span class="footer-separator">·</span>
  <a href="../cv.pdf">Download PDF</a>
  <span class="footer-separator">·</span>
  <span class="source">Updated from <a href="https://github.com/rickycodes/cv/blob/main/cv.md">cv.md</a>.</span>
</footer>"""
    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(
        HTML_TEMPLATE.format(stylesheet=STYLESHEET, body=body), encoding="utf-8"
    )
    print(f"Generated {OUTPUT}")


if __name__ == "__main__":
    main()
