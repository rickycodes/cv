# Resume

Source and tooling for Ricky Miller’s résumé.

The résumé content lives in [`resume.md`](resume.md). `generate-resume.py` converts it to LaTeX, and `build-resume.sh` runs the generator and builds the PDF with `pdflatex`.

The repository also includes scripts for collecting and summarizing GitHub pull-request history with the GitHub CLI.

## Build

Requirements: Python 3 and LaTeX with the packages/fonts used by the generated document.

```sh
./build-resume.sh
```

## License

This project is licensed under the [MIT License](LICENSE).
