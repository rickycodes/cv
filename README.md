# CV

Source and tooling for Ricky Miller’s curriculum vitae.

The CV content lives in [`cv.md`](cv.md). `generate-cv.py` converts it to LaTeX, and `build-cv.sh` runs the generator and builds the PDF with `pdflatex`.

The repository also includes scripts for collecting and summarizing GitHub pull-request history with the GitHub CLI.

## Build

Requirements: Python 3 and LaTeX with the packages/fonts used by the generated document.

```sh
./build-cv.sh
```

## License

This project is licensed under the [MIT License](LICENSE).
