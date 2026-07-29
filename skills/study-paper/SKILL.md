---
name: study-paper
description: Explain and analyze one specific academic paper interactively, including focused questions about its concepts, equations, proofs, experiments, claims, or official implementation. Use when the user wants to understand a paper or inspect how its method maps to code without requesting a complete durable note set, a reproduction, or research-idea development. Answer in the conversation by default and do not modify files unless the user explicitly asks to save or update material.
---

# Study Paper

Help the user solve the present understanding problem about one paper. Keep the work conversational and proportionate to the question.

## Keep the boundary narrow

- Answer in the conversation unless the user explicitly asks to save or update material.
- Do not create a paper workspace, notes tree, summary card, ideas file, reproduction plan, or experiment directory by default.
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

Finish with the direct answer, supporting evidence, important uncertainty, and the most useful next question when one is clear. List files only if the user explicitly asked for a saved change.
