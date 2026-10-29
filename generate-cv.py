#!/usr/bin/env python3
"""Generate the LaTeX CV from cv.md."""

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "cv.md"
OUTPUT = ROOT / "ricky-miller-cv.tex"


STYLE = {
    # Fonts
    "body_font_package": "plex-sans",
    "heading_font_package": "plex-mono",
    "heading_font_command": r"\plexmono",
    # Page
    "document_font_size": "10pt",
    "paper_size": "letterpaper",
    "margin": "0.58in",
    "top_margin": "0.52in",
    "bottom_margin": "0.52in",
    # Colors
    "ink": "181818",
    "muted": "5D6268",
    "accent": "DCFFFE",
    "rule": "A7D1D1",
    "paper": "FBFAF7",
    "teal": "167C80",
    # Design rules:
    # - 4pt spacing scale: block gaps use multiples of 4pt, a common spacing
    #   system in interface and editorial design.
    # - Typographic leading: body text stays in the conventional 120-140%
    #   range; headings remain tighter so hierarchy is carried by scale,
    #   weight, and proximity rather than decoration.
    # - Component ownership: paragraphs, lists, sections, and entries own
    #   their spacing; the global paragraph gap stays zero to avoid stacking
    #   unrelated spacing rules.
    # This is a spacing scale with conventional leading, not a strict
    # baseline grid: the 10pt body font and 12.8pt description leading do not
    # divide evenly into 4pt rows.
    #
    # Typography and spacing tokens.
    "line_spacing": "1.30",
    "description_line_spacing": "1.40",
    "list_line_spacing": "1.36",
    # Paragraphs are separated by their owning component's spacing token;
    # leaving the global paragraph gap at zero avoids double-spacing lists.
    "paragraph_spacing": "0pt",
    "list_left_margin": "1.15em",
    "list_item_spacing": "4pt",
    "emergency_stretch": "2em",
    "name_font_size": "25",
    "name_line_height": "28",
    "title_font_size": "14",
    "title_line_height": "16",
    "section_before": "8pt",
    "section_after": "0pt",
    "section_rule_before": "4pt",
    "rule_thickness": "0.6pt",
    "section_rule_after": "8pt",
    "header_rule_thickness": "1.2pt",
    "header_rule_before": "8pt",
    "header_rule_after": "8pt",
    "role_gap": "12pt",
    "role_after": "4pt",
    "project_gap": "4pt",
    "entry_baseline_adjustment": "0pt",
}


PREAMBLE_TEMPLATE = r"""\documentclass[@DOCUMENT_FONT_SIZE@,@PAPER_SIZE@]{article}
\usepackage[margin=@MARGIN@,top=@TOP_MARGIN@,bottom=@BOTTOM_MARGIN@]{geometry}
\usepackage[T1]{fontenc}
\usepackage[sfdefault]{@BODY_FONT_PACKAGE@}
\usepackage{@HEADING_FONT_PACKAGE@}
\usepackage{xcolor}
\usepackage{enumitem}
\usepackage{titlesec}
\usepackage{hyperref}
\usepackage[normalem]{ulem}
\usepackage[nopatch=footnote]{microtype}
\usepackage{tabularx}
\usepackage{parskip}
\usepackage{setspace}
\usepackage{fancyhdr}
\usepackage{lastpage}

\definecolor{ink}{HTML}{@INK@}
\definecolor{muted}{HTML}{@MUTED@}
\definecolor{accent}{HTML}{@ACCENT@}
\definecolor{rule}{HTML}{@RULE@}
\definecolor{paper}{HTML}{@PAPER@}
\definecolor{tealink}{HTML}{@TEAL@}

\pagecolor{paper}
\color{ink}
\setstretch{@LINE_SPACING@}
\hypersetup{colorlinks=true, urlcolor=tealink, linkcolor=ink, pdfborder={0 0 0}, pdftitle={Ricky Miller - CV}, pdfauthor={Ricky Miller}, pdfsubject={Senior Software Engineer CV}}
\setlength{\parindent}{0pt}
\setlength{\parskip}{@PARAGRAPH_SPACING@}
\setlist[itemize]{leftmargin=@LIST_LEFT_MARGIN@,itemsep=@LIST_ITEM_SPACING@,topsep=@LIST_ITEM_SPACING@,parsep=0pt}
\setlength{\emergencystretch}{@EMERGENCY_STRETCH@}

% Semantic leading tokens: descriptions get reading leading, while lists use
% a slightly tighter rhythm that still has room for wrapped lines.
\newcommand{\descriptionleading}{\setstretch{@DESCRIPTION_LINE_SPACING@}}
\newcommand{\listleading}{\setstretch{@LIST_LINE_SPACING@}}

\newcommand{\headingfont}{@HEADING_FONT_COMMAND@}
\newcommand{\sectionrule}[1][@SECTION_RULE_AFTER@]{\vspace{@SECTION_RULE_BEFORE@}\color{rule}\hrule height @RULE_THICKNESS@\color{ink}\vspace{#1}}
\newcommand{\role}[3]{%
  \begin{tabularx}{\textwidth}{@{}X r@{}}
    {\headingfont\bfseries\large #1} & {\headingfont\small\color{muted} #3}\\[@ENTRY_BASELINE_ADJUSTMENT@]
    {\headingfont\bfseries\color{tealink} #2} &
  \end{tabularx}\vspace{@ROLE_AFTER@}
}
\newcommand{\smallrole}[3]{%
  \begin{tabularx}{\textwidth}{@{}X r@{}}
    {\headingfont\bfseries #1 \textcolor{muted}{@} \textcolor{tealink}{#2}} & {\headingfont\small\color{muted} #3}
  \end{tabularx}\vspace{0.5pt}
}

\titleformat{\section}
  {\headingfont\bfseries\large\color{ink}}
  {}{0pt}{}
\titlespacing*{\section}{0pt}{@SECTION_BEFORE@}{@SECTION_AFTER@}

\pagestyle{fancy}
\fancyhf{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}
\fancyfoot[R]{\headingfont\scriptsize\color{muted} ricky.codes \quad \thepage/\pageref{LastPage}}

\begin{document}
"""

FOOTER = r"""
\vfill
{\headingfont\small\color{muted} Additional project details and contact information available at \href{https://ricky.codes}{ricky.codes}.\par\vspace{4pt} \href{https://github.com/rickycodes/cv/blob/main/cv.md}{Read as Markdown}}

\end{document}
"""


def build_preamble():
    """Apply the configurable style values to the LaTeX preamble."""
    replacements = {
        key.upper(): value for key, value in STYLE.items()
    }
    preamble = PREAMBLE_TEMPLATE
    for key, value in replacements.items():
        preamble = preamble.replace(f"@{key}@", str(value))
    return preamble


def latex_escape(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in text)


def inline(text: str) -> str:
    """Convert the small Markdown subset used by the CV."""
    parts = re.split(r"(\*\*.*?\*\*|\[.*?\]\(.*?\))", text)
    converted = []
    for part in parts:
        if part.startswith("**") and part.endswith("**"):
            converted.append(r"\textbf{" + latex_escape(part[2:-2]) + "}")
        else:
            link = re.fullmatch(r"\[(.*?)\]\((.*?)\)", part)
            if link:
                label, url = link.groups()
                converted.append(
                    r"\href{" + latex_escape(url) + r"}{\uline{" + inline(label) + r"}}"
                )
            else:
                converted.append(latex_escape(part))
    return "".join(converted)


def read_document():
    lines = SOURCE.read_text().splitlines()
    metadata = {}
    index = 0
    if lines and lines[0] == "---":
        index = 1
        while lines[index] != "---":
            key, value = lines[index].split(":", 1)
            metadata[key.strip()] = value.strip()
            index += 1
        index += 1
    return metadata, lines[index:]


def render_body(lines):
    output = []
    section = None
    entry = None
    paragraph = []
    bullets = []
    first_experience = True
    first_project = True

    def flush_paragraph():
        nonlocal paragraph
        if paragraph:
            output.append(
                "\\begingroup\\descriptionleading "
                + inline(" ".join(paragraph))
                + "\\par\\endgroup"
            )
            paragraph = []

    def flush_bullets():
        nonlocal bullets
        if bullets:
            output.append("\\begin{itemize}\\listleading")
            output.extend(f"  \\item {item}" for item in bullets)
            output.append("\\end{itemize}")
            bullets = []

    def flush_entry():
        flush_paragraph()
        flush_bullets()

    for line in lines + [""]:
        if line == "<!-- pagebreak -->":
            flush_entry()
            output.append("\\newpage")
            if section == "Professional Experience":
                output.append("\\section[Professional Experience continued]{Professional Experience \\textnormal{\\color{muted}\\small continued}}")
                output.append("\\sectionrule")
            first_experience = True
            continue

        if line == "<!-- cta-gap -->":
            flush_entry()
            output.append(f"\\vspace{{{STYLE['project_gap']}}}")
            continue

        match = re.match(r"^## (.+)$", line)
        if match:
            flush_entry()
            section = match.group(1)
            if section != "Summary":
                output.append(f"\\section{{{latex_escape(section)}}}")
                output.append("\\sectionrule")
            continue

        match = re.match(r"^### (.+?) \| (.+?) \| (.+)$", line)
        if match:
            flush_entry()
            role, company, dates = (inline(value) for value in match.groups())
            if section == "Professional Experience":
                if not first_experience:
                    output.append(f"\\vspace{{{STYLE['role_gap']}}}")
                command = "smallrole" if company in {"MetaLab", "High Road Communications"} else "role"
                output.append(f"\\{command}{{{role}}}{{{company}}}{{{dates}}}")
                first_experience = False
            continue

        match = re.match(r"^### (.+)$", line)
        if match:
            flush_entry()
            title = match.group(1)
            if section == "Selected Projects":
                if not first_project:
                    output.append(f"\\vspace{{{STYLE['project_gap']}}}")
                output.append(
                    f"{{\\headingfont\\bfseries {inline(title)}}}"
                    f"\\\\[{STYLE['entry_baseline_adjustment']}]"
                )
                first_project = False
            elif section == "Community":
                name, organization = title.split(" @ ", 1)
                output.append(
                    f"{{\\headingfont\\bfseries {inline(name)} "
                    f"\\textcolor{{muted}}{{@}} \\textcolor{{tealink}}{{{inline(organization)}}}}}"
                    f"\\\\[{STYLE['entry_baseline_adjustment']}]"
                )
            continue

        if line.startswith("- "):
            flush_paragraph()
            bullets.append(inline(line[2:]))
        elif line.strip():
            paragraph.append(line.strip())
        else:
            flush_entry()

    body = "\n\n".join(output)
    return body.replace("\\\\[0pt]\n\n", "\\\\[0pt]\n")


def main():
    metadata, lines = read_document()
    contact = (
        f"\\href{{mailto:{metadata['email']}}}{{{metadata['email']}}}"
        f"\\quad\\textcolor{{tealink}}{{•}}\\quad"
        f"\\href{{{metadata['website']}}}{{{metadata['website'].removeprefix('https://')}}}"
        f"\\quad\\textcolor{{tealink}}{{•}}\\quad"
        f"\\href{{{metadata['github']}}}{{{metadata['github'].removeprefix('https://')}}}"
    )
    header = (
        f"{{\\headingfont\\bfseries\\fontsize{{{STYLE['name_font_size']}}}"
        f"{{{STYLE['name_line_height']}}}\\selectfont {inline(metadata['name'])}}}\\hfill\n"
        f"{{\\headingfont\\small\\color{{muted}} {inline(metadata['location'])}}}\n\n"
        f"\\vspace{{2pt}}\n{{\\headingfont\\small\n{contact}}}\n\n"
        f"\\vspace{{{STYLE['header_rule_before']}}}\n"
        f"{{\\color{{tealink}}\\hrule height {STYLE['header_rule_thickness']}}}\n"
        f"\\vspace{{{STYLE['header_rule_after']}}}\n\n"
        f"{{\\headingfont\\bfseries\\fontsize{{{STYLE['title_font_size']}}}"
        f"{{{STYLE['title_line_height']}}}\\selectfont {inline(metadata['title'])}}}\n\n"
    )
    OUTPUT.write_text(build_preamble() + header + render_body(lines) + FOOTER)
    print(f"Generated {OUTPUT}")


if __name__ == "__main__":
    main()
