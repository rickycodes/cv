# Ricky Miller’s CV

[![Publish CV PDF](https://github.com/rickycodes/cv/actions/workflows/publish-pdf.yml/badge.svg)](https://github.com/rickycodes/cv/actions/workflows/publish-pdf.yml)

Source and tooling for [Ricky Miller’s curriculum vitae](ricky-miller-cv.pdf), published as a PDF and [HTML mini-site](https://ricky.codes/cv/).

The content lives in [`cv.md`](cv.md). [`generate-cv.py`](generate-cv.py) converts the small Markdown subset used there to LaTeX, and [`generate-cv-html.py`](generate-cv-html.py) renders the same source to a standalone HTML page.

## Preview

The repository includes the built PDF, which GitHub opens in its PDF viewer:

[View the repository PDF](ricky-miller-cv.pdf)

The website serves the deployed copy at [ricky.codes/cv.pdf](https://ricky.codes/cv.pdf).

The [Publish CV PDF workflow](https://github.com/rickycodes/cv/actions/workflows/publish-pdf.yml) shows the latest build and deployment runs.

The local build flow is:

```text
cv.md → generate-cv.py → ricky-miller-cv.tex → pdflatex → ricky-miller-cv.pdf
     ↘ generate-cv-html.py → cv-site/index.html
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
3. Builds the PDF and HTML site.
4. Checks out [`rickycodes/www`](https://github.com/rickycodes/www).
5. Copies the PDF to `www/static/cv.pdf`.
6. Copies the HTML page to `www/static/cv/index.html`.
7. Commits and pushes the website changes when either output has changed.

## Typography and layout

The HTML CV keeps the site’s typefaces while using a deliberately minimal presentation:

- SuisseIntl for headings and body text, GT America Mono for metadata
- A centered reading column with responsive gutters and heading sizes
- Black text on a white background
- No decorative background, borders, color treatment, or extra controls
- Date ranges use an en dash (`–`); the Markdown source keeps `--` for the LaTeX build

The PDF retains its separate print-oriented layout.

## GitHub history tools

The repository also includes scripts for collecting and summarizing GitHub pull-request history with the GitHub CLI:

- [`mine-github-history.sh`](mine-github-history.sh) collects pull requests from an organization.
- [`normalize-github-pr.py`](normalize-github-pr.py) normalizes pull-request data.
- [`generate-github-report.py`](generate-github-report.py) creates a Markdown report.

These reports are supporting research for the CV; `cv.md` remains the source of truth for the published document.

## Editing workflow

1. Edit [`cv.md`](cv.md).
2. Run `./build-cv.sh`.
3. Inspect `ricky-miller-cv.pdf` locally and open `cv-site/index.html` in a browser.
4. Commit and push changes to `main` to publish the updated PDF and `/cv/` page.

## License

This project is licensed under the [MIT License](LICENSE).
