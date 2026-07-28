# SUMMARY.CARD.md generation reference

Load this reference only after the complete paper model and section notes exist. The card is deliberately downstream of the notes: its questions should test the understanding the notes were designed to build.

## Design principles

The card is an active-recall and error-repair worksheet, not a compact answer sheet.

- Write it in the same language as the notes.
- Prefill only bibliographic metadata, links, and question text.
- Leave all responses, confidence ratings, corrections, and reflections blank.
- Do not include answers in HTML comments, collapsed blocks, footnotes, link titles, headings, examples, or metadata.
- Do not leak an answer by embedding the conclusion, exact result, causal explanation, or expected terminology in a question.
- Make questions specific enough that they could not be reused unchanged for an unrelated paper.
- Prefer prompts that require reconstruction, comparison, prediction, or criticism over prompts that ask for a list.
- Keep the card usable in plain Markdown source without special rendering.
- Keep the language-neutral blank-field comments from the template exactly as written. They let the validator confirm that no reader response was prefilled while visible labels remain translatable.

## Select the questions

Generate 8-12 questions. Cover every category below once, then use the remaining questions for the paper's hardest or most consequential content.

1. **Problem and thesis:** reconstruct the precise problem, why it matters, and the paper's answer.
2. **Mechanism or argument chain:** trace how the method, proof, study design, or argument moves from inputs and assumptions to the claimed outcome.
3. **Central technical object:** explain the paper's most important equation, definition, algorithm, experimental manipulation, or system invariant without merely naming it.
4. **Evidence:** identify the strongest evidence, the relevant comparison, and why it supports the claim.
5. **Evidence boundary:** state one tempting conclusion that the evidence does not justify.
6. **Novelty:** separate the paper's new contribution from inherited methods, data, assumptions, or prior results.
7. **Assumptions and failure:** identify assumptions and predict a condition under which the approach or conclusion would fail.
8. **Counterfactual or ablation:** predict what should change if a central component, assumption, control, or causal link were removed.
9. **Transfer:** apply the idea to a new but concrete scenario and state what would need to change.
10. **Open uncertainty:** identify the most important unresolved question or missing evidence.

Use the paper model to choose which named component, equation, result, figure, comparison, or controversy each question targets. Naming the object under examination is acceptable; supplying its role, behavior, result, or interpretation is not.

## Required document structure

Use this structure. Translate visible labels to the notes language. Replace every bracketed generator instruction with paper-specific content; never leave generator instructions in the output.

```markdown
# SUMMARY CARD: [paper title]

## Paper

- **Title:** [title]
- **Authors:** [authors]
- **Venue / year:** [venue and year]
- **Canonical source:** [DOI, arXiv ID, or stable URL]
- **Paper version studied:** [version or access date]
- **Notes:** [relative link to notes/00.abstract.md]

## Closed-book reconstruction

Close the paper and notes before starting. Write what you currently believe, including uncertainty. An incomplete answer is useful because it identifies the next thing to learn.

### 1. [paper-specific question]

**Your answer:**

<!-- response: blank -->

**Confidence before checking:** [ ] 1  [ ] 2  [ ] 3  [ ] 4  [ ] 5
<!-- confidence: blank -->

[Repeat the same answer and confidence structure for 8-12 questions.]

## Reconstruct the whole paper

Without looking at the notes, connect the paper in one chain:

**Problem -> assumptions -> method or argument -> evidence -> conclusion -> limits**

<!-- reconstruction: blank -->

## Review after reopening the notes

Only use this section after completing the closed-book attempt. Reopen the linked notes, check each answer, and record discrepancies without deleting the original response.

### Questions to revisit

<!-- revisit-question-numbers: blank -->

### What I had wrong or could not explain

<!-- gap-analysis: blank -->

### Corrected understanding, in my own words

<!-- corrected-understanding: blank -->

### Why the gap happened

- [ ] Missing prerequisite
- [ ] Remembered a label but not the mechanism
- [ ] Confused the authors' claim with their evidence
- [ ] Could not interpret the equation, figure, table, or experiment
- [ ] Overlooked an assumption or limitation
- [ ] Other:

### Next review

- **What I will revisit:**
- **Question I should be able to answer next time:**
- **Review date:**
```

The six exact HTML comments are blank writing markers, not content. Repeat `response: blank` and `confidence: blank` once for every numbered question; use each remaining marker exactly once. Do not add other HTML comments or place paper facts inside comments.

## Quality check

Before saving the card, verify that:

- there are 8-12 numbered, paper-specific questions;
- all ten question categories are covered when the question count permits, with no near-duplicate prompts;
- answering the questions would require explaining the paper rather than recognizing phrases;
- at least one question targets the paper's central evidence and one targets a real limitation;
- at least one question requires a counterfactual prediction and one requires transfer;
- no answer can be recovered by copying wording already embedded in its question;
- all reader-authored fields remain empty;
- the notes link resolves from the output root;
- the card contains no solution, answer key, or disguised hint.
