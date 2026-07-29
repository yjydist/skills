# Fidelity and Execution

Use this reference after the reproduction mode and target are explicit.

## Define an evidence-producing target

Specify:

- the claim or mechanism and paper locator;
- the artifact to run, reconstruct, or implement;
- exact inputs and configuration;
- expected output;
- a comparison or acceptance rule fixed before the run;
- evidence to retain.

Prefer the cheapest target that resolves the question. A valid target may be a proof check, algorithm test, simulation, artifact evaluation, data reanalysis, qualitative coding check, build and benchmark, or reduced model experiment.

## Apply the selected mode

### Exact rerun

Require immutable or otherwise unambiguous identities for the official code, data, model, configuration, preprocessing, environment, and evaluation. If a critical component cannot be recovered, stop that target as blocked. Offer claim-targeted or independent work only as a separately approved mode.

### Claim-targeted reproduction

State the exact claim, permitted substitutions, why each substitution is acceptable, and how it limits the conclusion. Align metric implementation, aggregation, seeds, workload, preprocessing, and resource budget with the claim before comparing.

### Independent idea implementation

Define the mechanism, mathematical properties, interface behavior, or invariants that must remain. List modernized or substituted components. Validate the preserved mechanism on deterministic fixtures before broader experiments. Do not compare headline numbers as though the setup were paper-faithful.

## Inspect feasibility

Locate first-party code, releases, commits, containers, dependencies, data, weights, supplements, evaluation scripts, corrections, licenses, and access instructions. Record blockers such as:

- private or unavailable data;
- credentials, commercial APIs, paid services, or expired endpoints;
- incompatible runtimes or undeclared dependencies;
- hardware, storage, time, memory, or energy demands;
- missing preprocessing, seeds, prompts, parameters, workloads, or protocols;
- conflicts between paper, documentation, configuration, and code.

Estimate what the current environment can support and expose reductions in scope before execution.

## Trace the implementation

Follow the executed path:

1. environment and installation definitions;
2. canonical demo, training, evaluation, benchmark, or analysis command;
3. data ingestion and preprocessing;
4. core method;
5. output generation and metric calculation;
6. paper settings versus repository defaults and released checkpoints;
7. hidden assumptions in environment variables, paths, caches, and hardware branches.

Record paper-code mismatches with exact locators.

## Execute incrementally

Use a contained, repeatable environment. Preserve original source artifacts and keep patches minimal.

Capture commands, working directory, dependencies, hardware, data and model versions, configuration, seeds, code revision, patches, relevant timestamps, logs, outputs, and metric computation. Retain informative failed runs while excluding secrets and disposable bulk.

## Debug systematically

Preserve the first complete error and a minimal reproducer. Classify it before changing code:

- acquisition or permissions;
- environment or dependency;
- build or platform;
- data schema or preprocessing;
- configuration or checkpoint;
- resource exhaustion;
- numerical or stochastic behavior;
- metric or evaluation mismatch;
- paper-code inconsistency;
- missing methodological detail.

Change one explanatory factor at a time when practical. Distinguish a workaround that merely runs from a correction that restores the selected target.

## Compare results

Align dataset and split, preprocessing, model or system version, checkpoint, workload, metric implementation, aggregation, seed count, hardware, and resource budget.

Avoid attributing a gap to randomness without seed evidence. Avoid calling values equivalent without a defined tolerance or uncertainty analysis.

Summarize actual completion, retained evidence, confirmed and untested claims, deviations, blockers, and the next discriminating diagnostic.
