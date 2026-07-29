---
name: writing-paper-notes
description: Read one academic paper end to end and create a durable, rigorous, beginner-friendly Markdown close reading plus a paper-specific active-recall worksheet. Use when the user explicitly asks for complete or section-by-section paper notes, a persistent close-reading workspace, or the notes/ and SUMMARY.CARD.md artifact set from a local file, URL, arXiv ID, DOI, or title. Do not use for a one-off explanation, research-idea development, code inspection, or any reproduction plan or execution.
---

# Write Paper Notes

Create a guided close reading that teaches the paper faithfully and gives the reader a demanding way to test whether they can reconstruct it without looking. Optimize for an accurate mental model and verifiable notes, not for shortness or mechanical coverage.

## Keep the workflow boundary explicit

- Produce files only because the user explicitly requested durable paper notes.
- Use `$study-paper` for a focused explanation or read-only implementation inspection.
- Use `$develop-paper-ideas` when the primary goal is critique and candidate research directions.
- Use `$reproduce-paper` for any reproduction plan, rerun, experiment, debugging, result comparison, or independent implementation.
- Do not create `REPRODUCT.md`, a `reproduce/` directory, a reproduction ledger, or an experiment plan as part of this skill.

## Define the task and output root

1. Resolve the paper and any user constraints: requested language, audience background, output directory, pinned paper version, and whether existing files may be replaced. If the user does not specify a language, use the language of their request. If no output directory is specified, use the current working directory.

2. Treat the chosen directory as `<output-root>` and produce this public contract:

   ```text
   <output-root>/
   |-- SUMMARY.CARD.md
   `-- notes/
       |-- 00.abstract.md
       |-- 01.<section-name>.md
       |-- 02.<section-name>.md
       `-- ...
   ```

3. Keep downloaded and extracted source material in a hidden working directory such as `<output-root>/.paper-source/`, never under `notes/`.
   Put every persisted non-deliverable artifact there as well: extracted text, page renders, source inventories, the section map, the paper model, ledgers, scratch calculations, and temporary scripts. The only public artifacts this skill creates are `SUMMARY.CARD.md` and the Markdown files directly under `notes/`.

4. Protect existing work:
   - Inventory the target paths before writing anything so conflict handling does not depend on noticing a collision late in the run.
   - Treat an existing `SUMMARY.CARD.md` as human-authored, even if it looks blank. Do not modify or replace it unless the user explicitly asks you to do so.
   - Preserve existing note files unless the user explicitly asks to replace them. Update a file only when it clearly belongs to the same paper and the requested task requires the update.
   - Stop and report a conflict when a target file belongs to another paper. Do not work around a conflict by silently choosing a different filename.

## Acquire a complete, readable source

Resolve local files, arXiv IDs or URLs, DOIs, venue pages, general paper URLs, and bare titles. Load `references/paper-sources.md` before acquiring a remote paper; it contains the source cascade, venue-specific behavior, and extraction commands.

Prefer the most structurally faithful complete source:

1. LaTeX source, including every included file, bibliography, and available figure.
2. Full-text HTML with preserved math, tables, figures, and captions.
3. PDF inspected through both searchable text extraction and page rendering.

Do not mistake an abstract page, metadata page, figure listing, or truncated preview for the paper. Read the complete main text before drafting. Include footnotes, appendices, supplementary material, captions, and reference context when they affect the method, evidence, or interpretation.

If no complete source is available after reasonable open-access resolution, explain what is missing and request the source. Do not present abstract-only notes as a close reading.

## Build a paper model before writing

Create a private paper model that captures how the work hangs together, not merely where topics appear. If it is persisted, save it under `.paper-source/`, never under `notes/`. Record:

- the motivating problem, research question, thesis, and claimed contributions;
- the dependency chain from assumptions and prior results through method and evidence to conclusion;
- every substantive section and subsection in source order;
- the main entities, definitions, variables, assumptions, equations, algorithms, datasets, metrics, baselines, figures, tables, ablations, and limitations;
- a claim-evidence ledger linking each important claim to its actual support and source locator;
- unresolved ambiguities, missing details, threats to validity, and results that are negative or weaker than the headline;
- what a reader must be able to explain, derive, predict, or critique to demonstrate understanding.

For every important statement, distinguish among:

- what the paper observes or proves;
- what the authors infer from that evidence;
- what they assume or inherit from prior work;
- what you infer while teaching the paper;
- what remains unknown.

Use this model as the shared source for the notes, the recall card, and final verification.

## Draft in three passes

Use three distinct passes so readable prose never outruns the evidence:

1. **Evidence pass:** assign every major claim, exact value, equation, visual, and limitation a source locator and a destination note before writing explanatory prose. Draft from this ledger, not from memory.
2. **Teaching pass:** reorder each section into prerequisite order for the target reader. Move from a plain-language orientation to mechanism, formal detail, worked example, and evidence. Define a concept before its first use and reuse one stable term and notation afterward.
3. **Reverse-verification pass:** trace every central statement and every exact number, sign, unit, equation, and comparison in the draft back to the source. Recompute small examples and sanity-check dimensions, limiting cases, and claimed metric direction. Label invented examples as teaching material and remove explanations that cannot be supported or clearly marked as interpretation.

Keep short or simple sections proportionally short. Add background only when it unlocks the paper's reasoning; do not pad every note with the same headings or generic textbook material.

## Match the analysis to the paper

Do not force every paper through an identical checklist. Give the greatest depth to the reasoning that determines whether the conclusion is warranted.

- **Theoretical or mathematical work:** reconstruct definitions, assumptions, theorem dependencies, proof ideas, edge cases, and the gap between formal claims and informal interpretation.
- **Empirical or scientific work:** reconstruct hypotheses, study design, sampling, controls, measurement, statistical analysis, uncertainty, alternative explanations, and external validity.
- **Algorithm or machine-learning work:** trace objectives, data flow, optimization, training and inference, computational cost, baselines, ablations, and reproducibility details.
- **Systems work:** explain architecture, interfaces, invariants, workloads, bottlenecks, resource tradeoffs, failure modes, and whether evaluations represent deployment conditions.
- **Survey, position, or conceptual work:** reconstruct taxonomy, selection criteria, argumentative structure, competing views, evidence standards, and omissions.

Many papers mix types. Apply all relevant lenses without adding empty boilerplate.

## Create the note files

Name the overview exactly `notes/00.abstract.md`. Then create one file per substantive top-level section in paper order, starting at `01` and zero-padding to at least two digits.

- Derive filenames from printed section titles. Use lowercase kebab-case for English titles. For other languages, retain readable native words while replacing whitespace and unsafe punctuation with hyphens.
- Keep subsections inside their parent file.
- Include substantive unnumbered sections.
- Give appendices or supplements their own consecutively numbered files when they add methods, proofs, experiments, or information needed to interpret or reproduce the paper.
- Skip standalone files for acknowledgments, author contributions, and references unless they contain substantive technical content.
- If the paper has no useful section structure, infer a small logical structure and label it as an instructional reorganization.

### Write `00.abstract.md` last

Make the overview a navigable model of the whole paper rather than a translation of its published abstract. Include:

1. the paper in one plain-language sentence: problem, approach, and result;
2. why the problem matters and what made it difficult;
3. the research question, scope, assumptions, and core mechanism;
4. a compact claim-evidence table with the strongest exact results and source locators;
5. what is genuinely new versus reused or extended;
6. what the evidence does not establish and where the method can fail;
7. a prerequisite glossary that defines only concepts needed to enter the section notes;
8. a reading map linking every generated section file and explaining why it matters;
9. a relative link to `../SUMMARY.CARD.md`, described as the closed-book understanding check.

### Write each section as a guided reconstruction

Use the original section title as the top-level heading and include its printed number when available. Organize around the section's actual reasoning. Cover applicable elements below, but do not manufacture empty headings.

- **Role in the argument:** what this section receives from earlier sections, what it must establish, and what later sections depend on it.
- **Background from zero:** prerequisites, precise definitions, and contrasts between easily confused concepts before they are used.
- **Reasoning or mechanism:** reconstruct each important transition from premise or input to conclusion or output. Surface hidden intermediate steps.
- **Operational intuition:** add a toy example, counterexample, analogy, or small calculation for each genuinely difficult idea. Mark anything invented for teaching.
- **Formal content:** preserve definitions, assumptions, objectives, constraints, algorithms, proofs, and implementation details that affect correctness or reproducibility.
- **Evidence and calibration:** explain what each important result tests, what was observed, what it supports, and what it cannot support.
- **Section synthesis:** end with the few ideas worth retaining and at least two active-recall questions. Put answers inside collapsed `<details>` blocks so the reader must choose to reveal them.

Use relative links when connecting files. Define a term before relying on it and keep notation and translations consistent across all notes.

Use one fold per question so revealing one answer does not reveal the others. Translate the visible labels, but retain the machine-readable comment:

```markdown
<!-- self-check: 1 -->
**Question 1: [section-specific reconstruction question]**

<details>
<summary>Reveal answer</summary>

[A concise answer justified by this section]

</details>
```

Repeat with consecutive numbers local to the section. Do not put multiple questions in one `<details>` block. Each section note must link back to `00.abstract.md` so navigation works in both directions.

## Explain technical material precisely

### Equations, definitions, and proofs

For each equation central to the paper's logic:

1. state the question the equation answers;
2. reproduce it accurately, or cite its number if extraction is unreliable;
3. define every symbol, including type, shape, index range, and units when relevant;
4. explain the role and intuition of each term or operation;
5. work a small numerical or conceptual example when practical;
6. state assumptions, boundary conditions, and qualitative behavior at important limits;
7. show how the paper derives or uses it.

Preserve distinctions among equality, approximation, proportionality, optimization, probability, expectation, correlation, and causation. For proofs, explain the strategy and dependency chain before walking through technical steps. Do not call a step "obvious" or "standard" when it hides knowledge the target reader needs.

### Algorithms and systems

Trace inputs, transformations, state, outputs, training or fitting, and inference or deployment. Explain informative pseudocode, complexity, initialization, hyperparameters, stopping conditions, resource requirements, and reported failure behavior. Separate what is required by the method from one implementation choice.

### Figures and tables

For each visual that materially affects the argument, explain the question it answers, how to read it, the exact values or patterns that matter, the authors' interpretation, plausible caveats, and whether it supports the associated claim. Include figure or table number and page when available. Do not spend equal space on decorative or redundant visuals.

### Experiments and evaluation

Explain the hypothesis, data provenance and splits, preprocessing, controls, baselines, metrics, protocol, important settings, uncertainty, and statistical treatment. Define each metric and which direction is better. Report exact numbers with units and uncertainty as written. Examine comparison fairness, ablations, sensitivity, threats to validity, and reproducibility gaps.

## Create the active-recall card

After the notes are complete, load `references/summary-card.md` and create `<output-root>/SUMMARY.CARD.md` from the paper model. The card is a worksheet for the reader, not another summary.

Tailor every substantive question to this paper's actual concepts, method, evidence, and weaknesses. Prefill bibliographic metadata and question text only. Keep every answer, confidence assessment, correction, and reflection field blank. Do not include solutions, hints, expected keywords, sample answers, or hidden answer keys.

The card should make shallow familiarity uncomfortable: a reader who cannot reconstruct the whole dependency chain—problem -> assumptions -> method or argument -> evidence -> conclusion -> limits—connect claims to evidence, predict a counterfactual, and state the limits should discover exactly where their understanding breaks. At the same time, the post-check section should require reopening the notes, recording discrepancies without erasing the closed-book attempt, and turning each failure into a concrete study target.

## Maintain source fidelity

- Attach locators to major claims, exact results, definitions, and interpretations in the notes. Prefer `Section 3.2, p. 7, Eq. 4` or `Table 2, p. 9` when available.
- Clearly label **Authors' claim**, **Evidence-supported conclusion**, **Interpretation**, **Teaching example**, and **Open question** whenever their status could be confused.
- Never invent motivations, derivations, details, citations, or values. Mark missing or ambiguous information explicitly.
- Do not silently repair an apparent paper error. Preserve it, explain the suspected problem, and state the uncertainty.
- Preserve caveats, negative findings, and null results. Do not upgrade empirical performance into a universal guarantee.
- Paraphrase and teach rather than copying long passages. Quote briefly only when exact wording matters.
- When versions differ, analyze the user-pinned version or the latest version and record which one was used.

## Verify before finishing

Compare the finished artifacts against the private paper model and verify:

- every substantive top-level section maps to one correctly ordered note file;
- `00.abstract.md` links to every section file and to `../SUMMARY.CARD.md`, every section links back to `00.abstract.md`, and every relative link resolves;
- central claims, mechanisms, equations, algorithms, evidence, and limitations are explained where they belong;
- exact values, signs, units, identifiers, captions, and terminology match the source;
- invented teaching material cannot be mistaken for paper evidence;
- the recall card is in the output root, contains 8-12 paper-specific questions, exposes no answers or hints, and leaves all reader fields unfilled;
- existing human-authored files were not overwritten;
- terminology, notation, translations, and entity names remain consistent across files;
- a reader can use the notes to reconstruct the paper's argument without the original prose, distinguish paper evidence from teaching material, and use the card to identify what they still cannot explain.

Run the bundled structural validator after the content review:

```bash
python3 <skill-directory>/scripts/validate_outputs.py <output-root>
```

Fix every reported error before finishing. The validator checks the file contract, note numbering, bidirectional links, card question numbering and blank fields, common answer leakage, unreplaced placeholders, and one collapsed answer block per section self-check. It cannot establish factual correctness, scientific completeness, or teaching quality, so do not use a clean validation result as a substitute for the reverse-verification pass against the paper model.

Finally report the files created or updated, the source identity and format used, and any source-quality or completeness limitations. Do not claim close-reading equivalence when material required for the argument was unavailable.
