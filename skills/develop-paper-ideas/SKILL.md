---
name: develop-paper-ideas
description: Critique one specific academic paper and develop a small set of evidence-grounded, falsifiable research ideas from its assumptions, limitations, results, official code, or observed behavior. Use when the user's primary goal is to find research directions, extensions, follow-up questions, or paper-specific weaknesses worth testing. Answer in the conversation by default; do not use for general paper explanation, complete study-note generation, literature reviews, or reproduction execution.
---

# Develop Paper Ideas

Develop paper-specific research directions without inflating uncertainty into novelty.

## Keep the work conversational

- Return critique and ideas in the conversation unless the user explicitly asks to save or update them.
- Do not create an `ideas/` directory or modify an existing workspace merely because one exists.
- Use `$study-paper` when the primary goal is understanding.
- Use `$writing-paper-notes` for a complete durable close reading.
- Use `$reproduce-paper` before executing an experiment or independent implementation.

## Ground the analysis

Resolve the paper and version. Read the complete sections, appendices, figures, tables, and official artifacts needed to assess the relevant claim. Prefer first-party sources and preserve meaningful paper-code-version differences.

Read [references/evidence-and-ideas.md](references/evidence-and-ideas.md) before evaluating claim support or shaping ideas.

Keep these categories distinct:

- paper claim or proof;
- official-code observation;
- current-run evidence supplied by the user;
- interpretation;
- hypothesis;
- user-originated idea;
- unresolved unknown.

Do not invent a gap, omitted experiment, implementation detail, or prior-art conclusion.

## Find high-leverage openings

Look for specific triggers such as:

- assumptions or boundary conditions that control the conclusion;
- missing controls, baselines, populations, workloads, ablations, or failure analysis;
- sensitivity to data, seeds, prompts, hardware, preprocessing, or hyperparameters;
- paper-code mismatches or undocumented implementation choices;
- costly, unstable, non-scalable, or inaccessible components;
- metrics that do not represent the stated objective;
- alternative explanations consistent with the evidence;
- mechanisms that could be simplified, verified, calibrated, or transferred for a concrete reason.

Prefer a few ideas with strong evidence and informative failure modes over a broad brainstorming list.

## Shape each candidate

For each worthwhile idea, include:

1. the observed trigger and exact locator;
2. the inference connecting the trigger to the idea;
3. a falsifiable research question;
4. the smallest plausible mechanism or change;
5. a feasible first test with baseline and decision criterion;
6. important confounds, negative outcomes, ethics, and resource constraints;
7. prior-art questions still requiring verification;
8. a calibrated current judgment.

Attribute user ideas to the user and label agent extensions when authorship matters.

## Control novelty claims

Treat every direction as a candidate until relevant primary literature has been searched. The paper's omission and a quick search are not evidence that no prior work exists.

When novelty matters, perform a dedicated primary-literature search, record the queries and search date, compare the closest work, and state the remaining uncertainty. If that search is outside the current request, say that novelty is unverified.

Finish with the strongest candidates, why they are promising or weak, the evidence behind that judgment, and the cheapest discriminating next step. Do not execute the proposed test unless the user explicitly requests reproduction or implementation work.
