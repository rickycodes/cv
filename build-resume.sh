#!/usr/bin/env bash
set -Eeuo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$script_dir"

python3 generate-resume.py
pdflatex -interaction=nonstopmode -halt-on-error ricky-miller-resume.tex
pdflatex -interaction=nonstopmode -halt-on-error ricky-miller-resume.tex
