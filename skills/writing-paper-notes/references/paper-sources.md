# Paper sources: acquisition reference

Loaded on demand by `writing-paper-notes` when acquiring a paper. The skill's `## Establish the source and output location` section defines the priority cascade (LaTeX source > HTML > PDF) and the fallback discipline; this document holds the venue-specific URLs, the format-availability matrix, and the exact commands.

Reuse the Read tool (which renders PDF pages visually via the `pages` parameter) and the `document-skills:pdf` skill (pdftotext, table extraction, OCR) for PDFs. Both are harness/plugin-provided and are referenced here by name.

## Format-availability matrix

The cascade collapses to PDF immediately for venues with no LaTeX source and no full-text HTML.

| Venue | LaTeX source | Full-text HTML | PDF | Notes |
|---|---|---|---|---|
| arXiv | Yes (e-print tarball or single .tex) | Yes (newer papers; ar5iv fallback for old) | Yes | Preferred |
| ACL Anthology | No | No | Yes (.pdf) + .bib + Supplement | Go straight to PDF |
| PMLR | No | No (.html is abstract-only) | Yes (.pdf) | Go straight to PDF |
| NeurIPS (papers.nips.cc) | No | No | Yes + Supplement | 2021+ on OpenReview |
| DOI / publisher | No | Often paywalled | Often paywalled | Unpaywall first, then arXiv title search |

## arXiv

Normalize old-format ids (e.g. `cs.LG/0501001`) to the new form; the native `/html/` link is versioned (`v3`) and absent for old papers. Fetch the latest version unless the user pinned one.

### LaTeX source (preferred)

URL: `https://arxiv.org/e-print/<id>`

Detect the format by Content-Type, not the filename:

- `application/x-tex` - a single `.tex`; save and read it directly, no extraction.
- `application/gzip` or `application/x-eprint-tar` - a tarball; extract it.

```bash
ID=2401.12345
mkdir -p .paper-source && cd .paper-source
curl -sL -D src.h -o src.bin "https://arxiv.org/e-print/$ID"
ct=$(grep -i '^content-type:' src.h | tr -d '\r' | head -1)

if printf '%s' "$ct" | grep -qi 'x-tex'; then
  mv src.bin paper.tex
else
  mkdir -p extracted && tar -xf src.bin -C extracted   # tar auto-detects gzip; do NOT force -z
fi
```

Locate the root `.tex` (the file with `\documentclass` that nothing else `\input`s) and follow includes; `\input{foo}` may omit the `.tex` extension:

```bash
grep -rl '\\documentclass' extracted/
grep -rnE '\\(input|include)\{' extracted/
find extracted -type f \( -iname '*.png' -o -iname '*.pdf' -o -iname '*.eps' -o -iname '*.jpg' -o -iname '*.jpeg' \)
find extracted -type f \( -iname '*.bib' -o -iname '*.bbl' \)
```

Then use the Read tool on the root `.tex`, each `\input`'d file, and the `.bib` (or the compiled `.bbl` when `.bib` is absent - it carries the full reference list). Read figures directly from the tarball.

Gotchas:

- `tar -xf` (no `-z`) is robust to both gzipped and plain tarballs; forcing `-z` fails on plain `.tar`.
- The root `.tex` is the file with `\documentclass` that no other file `\input`s. When several files have `\documentclass`, pick the one whose `\input`s cover the others and whose title matches the abs page.
- arXiv may strip oversized figures; if a figure is missing, recover it from the HTML or PDF render.
- The e-print URL returns the latest version by default; cross-check against the abs page if the user cited a specific version.

### HTML (second choice)

Try the native render first; fall back to ar5iv for older papers that 404:

```bash
curl -sL "https://arxiv.org/html/$ID" -o paper.html || \
curl -sL "https://ar5iv.labs.arxiv.org/html/$ID" -o paper.html
```

Do not use WebFetch for full paper content - it converts the page to markdown via a small fast model and drops MathJax math, complex tables, and figures, which is exactly the material a close reading needs. Use WebFetch only for metadata checks (does an HTML version exist? what is the arXiv id? title or abstract?).

Convert preserving structure, math, and tables:

```bash
if command -v pandoc >/dev/null 2>&1; then
  pandoc -f html -t markdown paper.html -o paper.md   # MathJax/MathML -> $...$ / $$...$$
else
  : # read paper.html directly; grep <script type="math/tex"> and <math> blocks for formulas
fi
```

Prefer arXiv native `/html/` over ar5iv (first-party, versioned, more reliable); use ar5iv only as the fallback that extends coverage to older papers.

### PDF (last resort)

```bash
curl -sL "https://arxiv.org/pdf/$ID" -o paper.pdf
```

Read with both channels and combine - never one alone:

- Read tool with the `pages` parameter (max 20 pages per request; required for PDFs over 10 pages) - presents pages visually, recovering layout, figures, tables, and text that extraction loses.
- `document-skills:pdf` skill - `pdftotext` for exact searchable text, table extraction, and OCR (`ocrmypdf`/tesseract) for scanned or image-only PDFs.

## ACL Anthology

No LaTeX source, no full-text HTML. The landing page is metadata plus BibTeX only.

- PDF: `https://aclanthology.org/<id>.pdf`
- BibTeX: `https://aclanthology.org/<id>.bib`
- Supplement / code: grep the landing page for `Supplement` or `Code` links and download separately.

## PMLR

No HTML article (the `.html` page is abstract-only), no source.

- PDF: `https://proceedings.mlr.press/<vol>/<key>.pdf` (the volume index page lists `<key>.html` links).
- The key (e.g. `abad-rocamora24a`) comes from the volume's paper listing.

## NeurIPS / OpenReview

`papers.nips.cc` serves abstract pages only; 2021+ papers are on OpenReview (`openreview.net/forum?id=...`), which is also PDF-primary.

- PDF: `https://papers.nips.cc/paper_files/paper/<year>/file/<hash>-Paper.pdf`
- Supplement: `https://papers.nips.cc/paper_files/paper/<year>/file/<hash>-Supplemental.{pdf,zip}`
- The `<hash>` comes from the Abstract page URL: `/paper_files/paper/<year>/hash/<hash>-Abstract.html`.

## DOI / paywalled

`https://doi.org/<doi>` redirects to the publisher and is often paywalled. Before giving up, try open-access resolution.

First query Unpaywall for an open-access URL:

```bash
curl -sL "https://api.unpaywall.org/v2/<doi>?email=<real-email>"
# read best_oa_location.url from the JSON
```

The `email=` parameter must be a genuine address; Unpaywall rejects `test@example.com`. It returns OA locations including arXiv, PubMed Central, repositories, and publisher OA.

If Unpaywall finds nothing, WebSearch the paper title for an arXiv preprint, then acquire via the arXiv path above. Only after both fail, state the limitation and request the source from the user.

## Per-format reading tactics

- **LaTeX**: Read the root `.tex`, every `\input`'d file, and the `.bib` or `.bbl`. Read figures (`.png`/`.pdf`/`.eps`) directly from the extracted tarball with the Read tool. Math, tables, and structure are exact.
- **HTML**: `curl` the raw HTML, then `pandoc -f html -t markdown` (or read the raw HTML directly). MathJax renders as `$...$` or `$$...$$` via pandoc; if reading raw HTML, grep `<script type="math/tex">` and `<math>` blocks to recover formulas.
- **PDF**: Read tool `pages` parameter for visual layout, figures, and tables; `document-skills:pdf` for exact text, table extraction, and OCR on scans. Combine both channels; do not rely on either alone.
