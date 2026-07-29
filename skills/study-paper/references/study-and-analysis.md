# Study and Analysis Lenses

Load only the sections that clarify the user's question.

## Explain a method

Determine:

1. the input, desired output, and constraints;
2. the core intuition without notation;
3. one complete example through the data or reasoning flow;
4. each component's responsibility and why it is needed;
5. the connection to the formal objective, algorithm, architecture, or study procedure;
6. the decisive difference from a meaningful prior approach;
7. assumptions, unavailable-at-deployment information, cost, and likely failures;
8. which experiments, proofs, or analyses support each important claim.

Use a compact diagram or pseudocode only when it materially clarifies the flow.

## Explain an equation

For each important equation:

- state the question it answers;
- define every needed symbol, index, operator, domain, shape, unit, and convention;
- distinguish inputs, outputs, constants, learned quantities, and intermediate values;
- explain each term's role and how changing or removing it affects behavior;
- connect it to surrounding equations and the algorithm or code when available;
- work through a tiny numerical, geometric, or counterexample-based illustration when useful;
- mark notation that is overloaded, undefined, or inferred.

Distinguish a mathematical optimum from the practical training procedure. State conditioning assumptions in probability expressions and what an approximation discards.

## Explain a proof or theoretical result

- Restate the result without weakening its quantifiers.
- List assumptions and identify where each enters.
- Trace dependencies on definitions, lemmas, and prior results.
- Give the proof strategy before line-level algebra.
- Explain the non-obvious step and why tempting alternatives fail.
- Check edge cases and clarify whether the result is existential, constructive, asymptotic, average-case, or worst-case.
- Separate the formal result from broader prose claims.

Do not imply that empirical evidence proves a theorem or that a theorem guarantees behavior outside its assumptions.

## Analyze experiments

For each central experiment, identify:

- the claim or question being tested;
- data, sample, task, workload, split, preprocessing, and access conditions;
- metric definition, direction, uncertainty, and practical meaning;
- whether baselines are fair in data, compute, tuning, information, and implementation quality;
- controls, ablations, randomization, seeds, statistical tests, and multiplicity where relevant;
- what the result supports and plausible alternative explanations;
- external validity, missing settings, failure cases, and deployment realism.

Read captions, axes, scales, aggregation, error bars, denominators, and omitted rows. Recalculate simple deltas when they determine the interpretation.

## Match the paper type

- For theoretical work, prioritize definitions, assumptions, theorem dependencies, proof ideas, edge cases, and complexity.
- For empirical or user research, prioritize sampling, controls, measurement validity, uncertainty, alternative explanations, ethics, and external validity.
- For machine-learning work, prioritize data, objectives, training and inference, baselines, ablations, seeds, compute, metrics, contamination, and hyperparameters.
- For systems or software-engineering work, prioritize architecture, interfaces, workloads, instrumentation, resource tradeoffs, failure modes, artifacts, and deployment realism.
- For mixed papers, combine only the relevant lenses.
