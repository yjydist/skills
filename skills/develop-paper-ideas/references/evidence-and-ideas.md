# Evidence, Critique, and Research Ideas

Use this reference to judge claim support and turn observations into research directions.

## Build a claim-evidence view

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

Use labels in prose when a table would add ceremony.

Distinguish:

- an observation from its causal explanation;
- statistical significance from practical importance;
- improvement evidence from evidence about why it improves;
- lack of evidence from evidence of absence;
- implementation behavior from a stated method;
- a successful run from reproduction of a paper claim.

When sources conflict, preserve the conflict and identify each version. Prefer a diagnostic test over unsupported reconciliation.

## Critique proportionally

Judge the paper against its actual claim and research type. Look for the weakest dependency:

- an assumption that fails in the intended setting;
- a baseline with unequal information, tuning, compute, or implementation quality;
- an outcome measure that poorly represents the stated goal;
- a proof whose informal interpretation exceeds its formal scope;
- an evaluation missing critical workloads, populations, costs, or failures;
- an ablation that does not isolate the claimed mechanism;
- an alternative explanation consistent with the same result;
- an official artifact inconsistent with the reported setup.

State both what the evidence supports and what it cannot establish. Do not inflate an ordinary limitation into a fatal flaw.

## Reject generic ideas

Reject “use a bigger model,” “try another dataset,” “improve efficiency,” and “combine A and B” unless the paper supplies a specific mechanism and testable reason.

Prefer directions that can fail informatively, have a feasible first test, and match known user constraints.

## Preserve attribution and uncertainty

Attribute user-originated ideas to the user. Keep verified observations separate from hypotheses and candidate novelty.

Never state that a gap is new merely because the paper omits it or an initial search did not find it. Verify novelty against primary literature and record search scope and date when the conclusion matters.
