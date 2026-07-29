# Studying and Writing Notes

Use this reference when explaining a paper, creating durable notes, or analyzing its technical or empirical content. Select only the lenses that clarify the user's task.

## Build a teachable model

Before drafting a substantial explanation, determine:

- the concrete problem and why it matters;
- the paper's thesis and claimed contributions;
- the minimum prerequisites a newcomer needs;
- the dependency chain from assumptions or prior work through method and evidence to conclusion;
- the main entities, symbols, modules, datasets, metrics, and comparisons;
- the strongest evidence, the weakest link, and unresolved ambiguity.

Teach in conceptual dependency order. Start with a plain-language mental model, then add precision. Translate terminology, but retain the original term so the learner can map the explanation back to the paper. Use a small running example when abstraction is high.

Do not mechanically restate every section. Give depth in proportion to its role in the paper's conclusion. Keep negative results, caveats, and exceptions visible.

## Explain a method

Cover the following when relevant:

1. Define the input, desired output, and constraints.
2. State the core intuition without notation.
3. Trace one example through the complete data or reasoning flow.
4. Explain each component's responsibility and why it is needed.
5. Connect the components to the formal objective, algorithm, architecture, or study procedure.
6. Contrast the decisive difference from a meaningful prior approach.
7. Identify assumptions, information unavailable at deployment, cost, and likely failure conditions.
8. Map claims to the experiments, proofs, or analyses intended to support them.

Use a compact diagram or pseudocode only when it materially clarifies flow.

## Explain an equation

For each important equation:

- state what question the equation answers;
- define every symbol, index, operator, domain, shape, unit, and convention needed here;
- identify inputs, output, constants, learned quantities, and intermediate values;
- explain each term's role and the effect of increasing, decreasing, removing, or changing it;
- connect the equation to the preceding and following equations;
- work through a tiny numerical, geometric, or counterexample-based illustration where useful;
- map it to code, configuration, or an algorithm step if an implementation exists;
- mark notation that is overloaded, undefined, or inferred rather than stated.

For an optimization objective, distinguish the mathematical optimum from the practical training procedure. For a probability expression, state the conditioning assumptions. For an approximation, state what is discarded and when that may fail.

## Explain a proof or theoretical result

- Restate the theorem in plain language without weakening its quantifiers.
- List assumptions and say where each enters.
- Show the dependency on prior definitions, lemmas, and results.
- Give the proof strategy before line-level algebra.
- Explain the non-obvious step and why tempting alternatives fail.
- Test edge cases and clarify whether the result is existential, constructive, asymptotic, average-case, or worst-case.
- Separate the formal result from broader claims made in prose.
- Map a constructive proof or algorithm to executable steps when possible.

Do not imply that empirical evidence proves a theorem or that a theorem guarantees behavior outside its assumptions.

## Analyze experiments

For each central experiment, identify:

- the claim or question being tested;
- dataset, sample, task, workload, split, preprocessing, and access conditions;
- metric definition, direction, uncertainty, and practical meaning;
- baselines and whether the comparison is fair in data, compute, tuning, information, and implementation quality;
- controls, ablations, randomization, seeds, statistical tests, and multiplicity where relevant;
- what the result supports, what it does not support, and plausible alternative explanations;
- external validity, missing settings, failure cases, and whether the evaluation resembles intended use.

Read figures and tables as evidence, not decoration. Check captions, axes, scales, aggregation, error bars, denominators, omitted rows, and inconsistent reporting. Recalculate simple deltas or ratios when they determine the interpretation.

## Adapt the notes

Choose headings that match the material, such as problem orientation, prerequisite, core intuition, method flow, worked example, formula, proof idea, evidence, code mapping, limitations, or open questions. Do not emit all of them by default.

Make a durable note independently readable:

- identify the paper and version;
- explain unfamiliar concepts at first use;
- include source locators for important claims;
- link to related workspace notes instead of duplicating them;
- distinguish paper statements, interpretation, run evidence, and unresolved questions;
- preserve the user's useful observations and attribute them.

If an existing note is coherent, extend it in place. If it mixes clearly independent topics and navigation has become difficult, split it carefully and repair links.
