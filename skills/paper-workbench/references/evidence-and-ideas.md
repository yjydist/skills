# Evidence, Critique, and Research Ideas

Use this reference when claims from multiple sources may be confused, when judging whether evidence supports conclusions, or when turning observations into research directions.

## Build a claim–evidence view

For each consequential claim, record only the fields that help:

| Item | Question |
|---|---|
| Claim | What exactly is asserted, with scope and qualifiers intact? |
| Source | Paper, official code, current run, interpretation, user, or external work? |
| Locator | Where can it be checked? |
| Evidence | What proof, measurement, comparison, or observation supports it? |
| Strength | Direct, indirect, mixed, contradictory, or absent? |
| Boundary | Under which assumptions, data, population, workload, or configuration? |
| Unknown | What remains unresolved? |

Do not force this table into every note. Use labels in prose when simpler.

Distinguish:

- an observation from its causal explanation;
- statistical significance from practical importance;
- evidence of improvement from evidence about why it improves;
- lack of evidence from evidence of absence;
- an implementation behavior from a stated method;
- a successful run from reproduction of a paper claim.

When sources conflict, preserve the conflict and identify the version of each source. Prefer a diagnostic test over an unsupported reconciliation.

## Critique proportionally

Judge the paper against the claim it makes and the conventions of its research type. Look for the weakest dependency in the argument:

- an assumption that does not hold in the intended setting;
- a baseline with unequal information, tuning, compute, or implementation quality;
- an outcome measure that poorly represents the stated goal;
- a proof whose informal interpretation exceeds its formal scope;
- an evaluation that omits critical workloads, populations, failure modes, or costs;
- an ablation that does not isolate the claimed mechanism;
- an alternative explanation consistent with the same result;
- a repository default or released artifact inconsistent with the reported setup.

State both what the evidence supports and what it cannot establish. Do not inflate ordinary limitations into fatal flaws.

## Discover candidate ideas

Search for high-leverage observations in:

- strong assumptions and boundary conditions;
- expensive, slow, data-hungry, unstable, or non-scalable components;
- sensitivity to seeds, prompts, hyperparameters, hardware, samples, or preprocessing;
- missing baselines, controls, ablations, populations, datasets, domains, or deployment conditions;
- misleading metrics or absent uncertainty and failure analysis;
- paper–code–run mismatches and undocumented implementation choices;
- a component that can plausibly be replaced, simplified, verified, calibrated, or made adaptive;
- a method that transfers to a clearly motivated new task or combines with a complementary mechanism.

Reject ideas that are merely “use a bigger model,” “try another dataset,” “improve efficiency,” or “combine A and B” unless the paper supplies a specific mechanism and testable reason.

## Shape an idea without overclaiming

Let an early idea remain a paragraph. As it matures, clarify:

1. **Observed trigger:** the paper, code, or run evidence and locator.
2. **Interpretation:** why the observation may matter.
3. **Candidate question:** a falsifiable research question, not a presumed conclusion.
4. **Possible mechanism:** the smallest plausible change or explanatory model.
5. **First test:** a feasible experiment, proof attempt, analysis, or prototype with a baseline and decision criterion.
6. **Risks:** confounds, negative outcomes, resource limits, ethics, or dependencies.
7. **Prior-art check:** concepts, neighboring areas, authors, and queries to search; mark the search incomplete until performed.
8. **Current judgment:** promising, weak, blocked, or superseded, with a reason.

Match the idea to the user's skills and resources when known. Prefer ideas that can fail informatively and have a clear next step.

## Preserve attribution and uncertainty

Attribute user-originated ideas to the user. Label agent-generated extensions separately when authorship matters. Keep verified observations separate from hypotheses and candidate novelty.

Never state that a research gap is new merely because the paper omits it or a quick search did not find it. Verify novelty against primary literature before making that claim, and record search scope and date when the conclusion matters.
