# Submitting the paper

Nothing has been submitted. These steps need your accounts.

## Build

```sh
cd paper
python3 ../bench/texnums.py ../bench/runs/seed8/results/test.json ../bench/runs/main/results/test.json \
  ../bench/runs/main/results/agent-test.json > numbers.tex
tectonic main.tex && mv main.pdf index-cards.pdf
```

`numbers.tex`, `table-main.tex`, `fig-sweep.tex` and `agent.tex` are generated or checked in; the PDF is committed as
`index-cards.pdf`.

## arXiv

1. Log in at https://arxiv.org/user (register if needed; first-time cs submitters may need an endorsement for the
   category, requested from the submission page).
2. Start a new submission: https://arxiv.org/submit. License: CC BY 4.0 is the usual choice.
3. Primary category: cs.CL (Computation and Language). Cross-list: cs.AI, cs.IR.
4. Upload a .tar.gz of `paper/` with `main.tex`, `numbers.tex`, `table-main.tex`, `fig-sweep.tex`, `agent.tex` and
   `figs/` (`tar czf index-cards-arxiv.tar.gz main.tex *.tex figs`). arXiv compiles with pdflatex; the source uses
   only standard packages.
5. Title and abstract: copy from `main.tex`. Comments field: "Code, data and cached answers:
   https://github.com/abhaymettu/index-cards".
6. Check the compiled PDF arXiv shows you, then submit. It appears after the next daily announcement.

## Zenodo DOI for the repository (optional)

1. Log in at https://zenodo.org with GitHub, open https://zenodo.org/account/settings/github/ and switch the
   `index-cards` repository on.
2. Make a GitHub release (`v0.2.0`). Zenodo archives it and mints a DOI.
3. Put the DOI badge in the README and the citation.
