#!/usr/bin/env python3
"""Generate the LaTeX CV from cv.md."""

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "cv.md"
OUTPUT = ROOT / "ricky-miller-cv.tex"


PREAMBLE = r"""\documentclass[10pt,letterpaper]{article}
\usepackage[margin=0.58in,top=0.52in,bottom=0.52in]{geometry}
\usepackage[T1]{fontenc}
\usepackage[sfdefault]{plex-sans}
\usepackage{plex-mono}
\usepackage{xcolor}
\usepackage{enumitem}
\usepackage{titlesec}
\usepackage{hyperref}
\usepackage[nopatch=footnote]{microtype}
\usepackage{tabularx}
\usepackage{parskip}
\usepackage{setspace}
\usepackage{fancyhdr}
\usepackage{lastpage}

\definecolor{ink}{HTML}{181818}
\definecolor{muted}{HTML}{5D6268}
\definecolor{accent}{HTML}{DCFFFE}
\definecolor{rule}{HTML}{A7D1D1}
\definecolor{paper}{HTML}{FBFAF7}
\definecolor{tealink}{HTML}{167C80}

\pagecolor{paper}
\color{ink}
\setstretch{1.18}
\hypersetup{colorlinks=true, urlcolor=tealink, linkcolor=ink, pdfborder={0 0 0}, pdftitle={Ricky Miller - CV}, pdfauthor={Ricky Miller}, pdfsubject={Senior Software Engineer CV}}
\setlength{\parindent}{0pt}
\setlength{\parskip}{2.5pt}
\setlist[itemize]{leftmargin=1.15em,itemsep=3.5pt,topsep=3.5pt,parsep=0pt}
\setlength{\emergencystretch}{2em}

\newcommand{\headingfont}{\plexmono}
\newcommand{\sectionrule}{\vspace{1pt}\color{rule}\hrule height 0.6pt\color{ink}\vspace{5pt}}
\newcommand{\role}[3]{%
  \begin{tabularx}{\textwidth}{@{}X r@{}}
    {\headingfont\bfseries\large #1} & {\headingfont\small\color{muted} #3}\\[-1pt]
    {\headingfont\bfseries\color{tealink} #2} &
  \end{tabularx}\vspace{0.5pt}
}
\newcommand{\smallrole}[3]{%
  \begin{tabularx}{\textwidth}{@{}X r@{}}
    {\headingfont\bfseries #1 \textcolor{muted}{@} \textcolor{tealink}{#2}} & {\headingfont\small\color{muted} #3}
  \end{tabularx}\vspace{0.5pt}
}

\titleformat{\section}
  {\headingfont\bfseries\large\color{ink}}
  {}{0pt}{}
\titlespacing*{\section}{0pt}{9pt}{1pt}

\pagestyle{fancy}
\fancyhf{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}
\fancyfoot[R]{\headingfont\scriptsize\color{muted} ricky.codes \quad \thepage/\pageref{LastPage}}

\begin{document}
"""

FOOTER = r"""
\vfill
{\headingfont\small\color{muted} References and additional project details available at \href{https://ricky.codes}{ricky.codes}.}

\end{document}
"""


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
    parts = re.split(r"(\*\*.*?\*\*)", text)
    converted = []
    for part in parts:
        if part.startswith("**") and part.endswith("**"):
            converted.append(r"\textbf{" + latex_escape(part[2:-2]) + "}")
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
            output.append(inline(" ".join(paragraph)))
            paragraph = []

    def flush_bullets():
        nonlocal bullets
        if bullets:
            output.append("\\begin{itemize}")
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
                    output.append("\\vspace{4pt}")
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
                    output.append("\\vspace{5pt}")
                output.append(f"{{\\headingfont\\bfseries {inline(title)}}}\\\\[-1pt]")
                first_project = False
            elif section == "Community":
                name, organization = title.split(" @ ", 1)
                output.append(
                    f"{{\\headingfont\\bfseries {inline(name)} "
                    f"\\textcolor{{muted}}{{@}} \\textcolor{{tealink}}{{{inline(organization)}}}}}\\\\[-1pt]"
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
    return body.replace("\\\\[-1pt]\n\n", "\\\\[-1pt]\n")


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
        f"{{\\headingfont\\bfseries\\fontsize{{25}}{{27}}\\selectfont {inline(metadata['name'])}}}\\hfill\n"
        f"{{\\headingfont\\small\\color{{muted}} {inline(metadata['location'])}}}\n\n"
        f"\\vspace{{2pt}}\n{{\\headingfont\\small\n{contact}}}\n\n"
        f"\\vspace{{6pt}}\n{{\\color{{tealink}}\\hrule height 1.2pt}}\n\\vspace{{7pt}}\n\n"
        f"{{\\headingfont\\bfseries\\fontsize{{14}}{{16}}\\selectfont {inline(metadata['title'])}}}\n\n"
    )
    OUTPUT.write_text(PREAMBLE + header + render_body(lines) + FOOTER)
    print(f"Generated {OUTPUT}")


if __name__ == "__main__":
    main()
