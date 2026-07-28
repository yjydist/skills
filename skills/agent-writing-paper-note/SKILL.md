---
name: agent-writing-paper-note
description: Analyze an academic paper end to end and write a structured set of beginner-friendly Markdown reading notes that preserve the depth and learning value of a close reading. Use when the user asks to read, analyze, explain, study, or take notes on a paper, preprint, journal article, conference paper, or technical manuscript, especially when the output should be split by the paper's sections under a notes/ directory. Accepts a local file, an arXiv ID or URL, a DOI, or a paper title; fetches the most parseable open-access source available.
---

# Write Paper Notes

Produce a self-contained guided reading that lets a reader with no prior knowledge reach the understanding they would gain from closely reading the paper. Optimize for understanding and fidelity, not brevity.

## Establish the source and output location

1. Resolve what the user gave you: a local file or directory, an arXiv ID or URL, a DOI, an ACL Anthology / PMLR / NeurIPS / OpenReview URL, a general paper URL, or a bare title. Normalize to a canonical identifier and venue. Cache every download into a local working directory (e.g. `.paper-source/` beside the eventual `notes/`), never into the output directory.

2. Acquire the most parseable source available, trying each in turn and stopping at the first complete paper (one containing the main body sections, not just the abstract or figures):
   - **(1) LaTeX source - preferred.** Exact math, structure, figures, and tables with no extraction loss.
   - **(2) HTML - second choice.** Structured and easy to parse; loses little.
   - **(3) PDF - last resort.** Hard to parse; layout, math, and tables are easily lost.

   The venue-specific URLs, format-availability matrix, and exact curl/tar/pandoc commands are in `references/paper-sources.md` - load it now. Note that ACL, PMLR, and NeurIPS offer no LaTeX source and no full-text HTML, so for them the cascade collapses to PDF immediately. If a higher-priority format is unavailable, drop to the next format rather than asking the user.

3. For a DOI behind a paywall, query Unpaywall (https://api.unpaywall.org/v2/<doi>?email=<real-email>) for an open-access URL before giving up; if it finds nothing, search arXiv by the paper title for a preprint. If only a bare title was given, search the web first to find an arXiv or open-access copy, then proceed.

4. Read the entire paper before drafting notes. Include footnotes, figure and table captions, appendices, and supplementary material when they affect the argument or evidence. For ACL/NeurIPS this means any separate Supplement download; for arXiv it means ancillary files and the .bib/.bbl reference list.

5. Create `notes/` in the user-specified output directory. If none is specified, create it in the current working directory - never inside the download cache.

6. Preserve existing note files unless the user explicitly asks to replace them. When a target filename already exists, update it only if it clearly belongs to the same paper; otherwise stop and report the conflict.

Do not begin drafting from the abstract alone. If all three formats fail after the open-access resolution steps above, state the limitation and request the missing source rather than presenting abstract-only notes as a close reading.

## Map the paper before writing

Build a private coverage map with:

- the paper's central question, thesis, contributions, and claimed novelty;
- the logical dependency chain from motivation through method to evidence and conclusion;
- every top-level section and its subsections in source order;
- all important definitions, assumptions, equations, algorithms, figures, tables, datasets, metrics, baselines, ablations, and limitations;
- the location of each important claim, using page and section plus equation, figure, or table identifiers when available.

Distinguish what the authors demonstrate from what they assume, speculate, inherit from prior work, or leave unresolved. Use this map as a completeness checklist after drafting.

## Create the note files

Always create:

```text
notes/
|-- 00.abstract.md
|-- 01.<section-name>.md
|-- 02.<section-name>.md
`-- ...
```

Apply these naming rules:

- Name the overview exactly `00.abstract.md`.
- Create one subsequent file for every substantive top-level section, in paper order, starting at `01` and zero-padding to at least two digits.
- Derive `<section-name>` from the section's printed title. For English titles, use lowercase kebab-case; for titles in other languages, retain readable native words and replace whitespace or filesystem-unsafe punctuation with hyphens.
- Keep subsections inside their parent section file rather than creating separate files.
- Treat an unnumbered introduction, conclusion, or other substantive heading as a section.
- Create separate, consecutively numbered files for appendices or supplementary sections when they add methods, proofs, experiments, or details needed to understand or reproduce the work.
- Do not create standalone files for acknowledgments, author contributions, or the references list unless they contain substantive technical content. Explain important cited work where it becomes relevant instead.

If the source has no useful section structure, infer a small set of logical sections from the argument and make clear in each file that the division was inferred.

## Write `00.abstract.md`

Write this file after understanding the whole paper. It is a guided map of the work, not merely a translation of the published abstract. Include:

1. **The paper in one sentence**: the problem, approach, and result in plain language.
2. **Why this problem matters**: the real-world or scientific stakes and what was difficult before this work.
3. **What the paper does**: the research question, core idea, method, and scope.
4. **What it finds**: the strongest evidence and exact headline results, with source locators.
5. **What is genuinely new**: separate claimed contributions from incremental reuse of prior work.
6. **What the result does not establish**: key assumptions, limitations, and boundaries.
7. **Prerequisite concepts**: a short glossary of the minimum concepts a newcomer needs before reading the section notes.
8. **Reading map**: one or two sentences on the purpose of each generated section file, using relative Markdown links.

## Write each section note

Use the paper's original section title as the top-level heading and state the original section number when one exists. Organize the explanation around the material rather than forcing empty boilerplate, but cover every applicable item below:

- **Purpose and takeaway**: explain why this section exists in the paper's argument and what the reader should know after it.
- **Background from zero**: introduce every prerequisite before relying on it. Define technical terms on first use and contrast easily confused concepts.
- **Step-by-step reasoning**: reconstruct how the authors move from premises to conclusion. Make hidden intermediate steps explicit.
- **Concrete example**: give a small example, analogy, counterexample, or toy calculation that makes each difficult idea operational. Label examples invented for teaching as such.
- **Formal details**: preserve definitions, assumptions, objectives, constraints, algorithms, proofs, and implementation details that affect correctness or reproducibility.
- **Evidence**: explain experiments, qualitative analysis, theoretical support, and negative or null results, including what each piece of evidence can and cannot support.
- **Connection to the paper**: show what this section consumes from earlier sections and what later sections depend on it. Link to the relevant note files.
- **Section recap**: finish with the few conclusions the reader should retain and two or more short self-check questions with answers.

Keep the prose in the user's requested language; otherwise use the language of the user's request. Quote original terminology when translation could create ambiguity.

## Explain technical material

### Equations and symbols

For every equation central to the argument:

1. State what question the equation answers in ordinary language.
2. Reproduce it accurately or cite its equation number if reproduction is unreliable.
3. Define every symbol at first use, including type, shape, index range, and units when relevant.
4. Explain each term's role and the intuition behind the operation.
5. Walk through a small numerical or conceptual example when practical.
6. State assumptions, boundary conditions, and what changes when an input increases, decreases, or reaches an edge case.
7. Explain how the paper derives or uses the equation; do not call a step "obvious" or "standard" without unpacking the part a newcomer needs.

Preserve the distinction between equality, approximation, proportionality, optimization, probability, and expectation.

### Algorithms and systems

Trace inputs, transformations, state, outputs, training or fitting, and inference or deployment. Explain pseudocode line by line when it carries information not available in the prose. Record complexity, hyperparameters, initialization, stopping conditions, and failure behavior when reported.

### Figures and tables

For every substantive figure or table, explain:

- the question it is intended to answer;
- how to read axes, legends, colors, panels, scales, uncertainty, and comparison groups;
- the most important exact values or visible patterns;
- the authors' interpretation and any reasonable caveat;
- whether it supports the stated claim.

Never refer to a visual as "self-explanatory." Include its figure or table number and page when available.

### Experiments and evaluation

Explain the hypothesis, data source and splits, preprocessing, baselines, metrics, protocol, important settings, and statistical treatment. Define what each metric measures and which direction is better. Report exact numbers with units and uncertainty as written. Discuss fairness of comparisons, ablations, sensitivity analysis, threats to validity, and reproducibility gaps.

## Maintain fidelity

- Attach source locators to major claims, quantitative results, definitions, and interpretations. Prefer forms such as `Section 3.2, p. 7, Eq. 4` or `Table 2, p. 9`.
- Clearly label statements as **Authors' claim**, **Interpretation**, **Teaching example**, or **Open question** whenever readers might confuse their status.
- Do not invent motivations, derivations, experimental details, citations, or numerical values. Mark missing or ambiguous information explicitly.
- Do not silently repair an apparent error in the paper. Quote or describe it, explain the suspected issue, and identify the uncertainty.
- Preserve meaningful caveats and negative results. Do not turn correlation into causation or empirical performance into a universal guarantee.
- Paraphrase and teach rather than copying long passages. Use short quotations only when exact wording matters.
- Avoid unexplained jargon, circular definitions, and summaries that merely restate section headings.

## Verify the finished notes

Before finishing, compare all files against the private coverage map and verify that:

- every substantive top-level section has exactly one note file and the order matches the paper;
- the abstract file links to every section note and all relative links resolve;
- central claims, equations, algorithms, figures, tables, and results appear in the appropriate notes;
- every technical term needed by a newcomer is defined before use;
- exact values, signs, units, equation identifiers, and figure/table references match the source;
- teaching examples are clearly distinguished from the paper's own examples or evidence;
- cross-file terminology and notation are consistent;
- a reader can explain the problem, reproduce the method at the level supported by the paper, interpret the evidence, and articulate the limitations without reopening the paper.

Finally, report the created or updated files, which source format was used, and any source-quality or completeness limitations (including anything that format did not preserve). Do not claim close-reading equivalence when required content was unavailable.
