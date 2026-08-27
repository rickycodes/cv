# Ricky Miller’s CV

[![Publish CV PDF](https://github.com/rickycodes/cv/actions/workflows/publish-pdf.yml/badge.svg)](https://github.com/rickycodes/cv/actions/workflows/publish-pdf.yml)

Source and tooling for [Ricky Miller’s curriculum vitae](ricky-miller-cv.pdf).

The content lives in [`cv.md`](cv.md). [`generate-cv.py`](generate-cv.py) converts the small Markdown subset used there to LaTeX, and [`build-cv.sh`](build-cv.sh) builds the final PDF with `pdflatex`.

## Preview

The repository includes the built PDF, which GitHub opens in its PDF viewer:

[View the repository PDF](ricky-miller-cv.pdf)

The website serves the deployed copy at [ricky.codes/cv.pdf](https://ricky.codes/cv.pdf).

The [Publish CV PDF workflow](https://github.com/rickycodes/cv/actions/workflows/publish-pdf.yml) shows the latest build and deployment runs.

## Build and deployment

The local build flow is:

```text
cv.md → generate-cv.py → ricky-miller-cv.tex → pdflatex → ricky-miller-cv.pdf
```

Build locally with:

```sh
./build-cv.sh
```

Requirements are Python 3 and a LaTeX installation containing the packages and fonts used by the workflow:

- TeX Live 2022
- `scheme-basic`
- `collection-latexextra`
- `plex`
- `fontaxes`
- `mweights`

On pushes to `main` that change the CV source or build tooling, GitHub Actions:

1. Checks out the repository.
2. Installs the pinned LaTeX toolchain.
3. Builds the PDF.
4. Checks out [`rickycodes/www`](https://github.com/rickycodes/www).
5. Copies the PDF to `www/static/cv.pdf`.
6. Commits and pushes the website change when the PDF has changed.

The workflow can also be started manually with `workflow_dispatch`. Deployment requires the repository’s `WWW_REPO_TOKEN` secret.

## Typography and layout

The visual system is kept as named tokens near the top of [`generate-cv.py`](generate-cv.py):

- IBM Plex Sans for body text and IBM Plex Mono for headings and metadata
- 10pt body type on US letter paper
- 4pt spacing scale for sections, entries, lists, and header rules
- Body leading between 120–140%; current values are `1.30` base, `1.40` descriptions, and `1.36` lists
- Hierarchy through type scale, weight, color, and proximity rather than decorative elements
- Muted ink, teal links, and a warm off-white paper color for contrast without pure black and white

The comments beside the style tokens document the rules and their limits. When adjusting the layout, change the tokens there instead of adding isolated spacing values to the renderer.

## GitHub history tools

The repository also includes scripts for collecting and summarizing GitHub pull-request history with the GitHub CLI:

- [`mine-github-history.sh`](mine-github-history.sh) collects pull requests from an organization.
- [`normalize-github-pr.py`](normalize-github-pr.py) normalizes pull-request data.
- [`generate-github-report.py`](generate-github-report.py) creates a Markdown report.

These reports are supporting research for the CV; `cv.md` remains the source of truth for the published document.

## Editing workflow

1. Edit [`cv.md`](cv.md).
2. Run `./build-cv.sh`.
3. Inspect `ricky-miller-cv.pdf` locally.
4. Commit and push changes to `main` to publish the updated PDF.

## License

This project is licensed under the [MIT License](LICENSE).
