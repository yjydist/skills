---
name: study-paper
description: Explain and analyze one specific academic paper interactively while maintaining a lightweight .study/TODO.md progress checklist and .study/STUDY.md teaching transcript. Use when the user wants to understand a paper or inspect how its method maps to code without requesting a complete section-by-section note set, a reproduction, or research-idea development.
---

# Study Paper

Help the user understand one paper through an interactive teaching loop. Keep the explanation conversational and proportionate to the question while preserving a lightweight learning trail.

## Maintain the study trail

At the start of the study task, create `.study/` in the user's current study workspace. Do not place it inside this skill's directory. Create or resume:

- `.study/TODO.md`: the progress plan for the current paper;
- `.study/STUDY.md`: an append-only record of completed teaching exchanges.

Never overwrite existing study history. If the files already exist for the same paper, read them and resume from the first unchecked item. Preserve completed items and prior transcript entries.

In `TODO.md`, identify the paper and version, then list every currently known teaching item using valid Markdown task syntax:

```markdown
# Study TODO

Paper: <title and version>

- [ ] <one observable learning objective>
- [ ] <next objective>
```

Make each item small enough to teach and verify in one focused exchange. Order prerequisites before dependent concepts. Add newly discovered prerequisites or follow-up items when needed; do not pretend the initial plan is exhaustive.

For each unchecked item:

1. Teach the item using the relevant evidence and locators.
2. Check understanding with a focused question, small derivation, example, comparison, or user confirmation appropriate to the item.
3. Treat the item as passed only when the learner demonstrates understanding or explicitly confirms that the issue is resolved. Do not mark an item complete merely because an explanation was delivered.
4. Append the relevant learner-tutor exchange to `STUDY.md`, including the item, explanation, understanding check, learner response, and any remaining caveat.
5. Only after the transcript is safely appended, change that item's checkbox in `TODO.md` from `- [ ]` to `- [x]`.

Use a stable entry structure:

```markdown
## <completed item>

### Learner
<question or starting understanding>

### Tutor
<teaching response>

### Check
<check and learner response>

### Outcome
Passed. <remaining caveat, if any>
```

If the learner has not yet passed an item, leave it unchecked and do not add a completed entry. Continue the teaching dialogue in the conversation, then record it once the item passes. Before ending each turn, keep both files consistent with the actual state.

## Keep the boundary narrow

- Use only `.study/TODO.md` and `.study/STUDY.md` for default persistence.
- Do not create a broader paper workspace, notes tree, summary card, ideas file, reproduction plan, or experiment directory by default.
- Use `$writing-paper-notes` when the user explicitly requests a complete, durable, section-by-section close reading.
- Use `$develop-paper-ideas` when the primary goal is critique that produces candidate research directions.
- Use `$reproduce-paper` only when the user explicitly asks to plan, run, debug, or compare a reproduction or independent implementation.
- Treat reading official code as study, not reproduction, while the work remains read-only and evidence-seeking.

## Establish enough evidence

Resolve the exact paper and version. Prefer the most structurally faithful complete source available:

1. LaTeX source, including relevant included files, bibliography, appendices, tables, captions, and figures.
2. Complete full-text HTML with preserved structure and math.
3. PDF inspected through searchable text and visual page rendering when equations, figures, tables, or layout matter.

Read the complete portions needed to answer the question, including appendices or supplementary material that change the answer. Do not rely on an abstract, metadata page, or search snippet when the claim can be checked in the paper.

Prefer first-party paper, code, data, model, errata, and project sources. Record meaningful version differences. If the evidence is incomplete or conflicting, state the limitation instead of filling the gap from memory.

## Build the explanation

Read [references/study-and-analysis.md](references/study-and-analysis.md) when the request involves a method, equation, proof, experiment, or substantial technical explanation. Select only the relevant lenses.

Adapt the depth to the user's demonstrated background. Teach in dependency order:

1. State the question the paper is trying to answer.
2. Give a plain-language mental model.
3. Introduce only the prerequisites needed now.
4. Trace the mechanism, reasoning, or evidence precisely.
5. Use a small example or counterexample when it removes ambiguity.
6. State what the result supports, what it does not support, and what remains uncertain.

Attach useful locators such as section, page, equation, theorem, figure, table, appendix, repository path, symbol, or configuration key.

## Inspect an implementation without reproducing

When official code helps explain the paper:

- pin or record the inspected revision when behavior may have changed;
- read installation and configuration files, entry points, and the executed data or control path;
- map paper concepts to concrete files, functions, parameters, and defaults;
- distinguish the paper's required mechanism from repository-specific choices;
- preserve paper-code mismatches instead of silently reconciling them.

Do not install environments, modify code, download large artifacts, or run experiments merely to improve an explanation. If the user requests those actions, hand the task to `$reproduce-paper` and require its fidelity gate.

## Keep evidence categories distinct

Distinguish paper statements, official-code observations, external evidence, interpretation, and unknowns whenever they could be confused. Never present a later implementation choice or community convention as something established by the paper.

Finish with the direct answer, supporting evidence, important uncertainty, the current checklist progress, and the most useful next unchecked item when one is clear.
