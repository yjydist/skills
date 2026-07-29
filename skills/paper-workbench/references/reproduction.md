# Reproduction Work

Use this reference when assessing feasibility, reading an implementation, setting up an environment, executing or debugging experiments, or comparing results.

## Choose an evidence-producing target

Translate the user's goal or a central paper claim into a concrete target with:

- an artifact to run or implement;
- the input, configuration, and expected output;
- a comparison or acceptance rule;
- the evidence to retain.

Prefer the cheapest target that resolves the question. Depending on the paper, this may be a proof check, algorithm test, build and benchmark, simulation, artifact evaluation, data reanalysis, qualitative coding check, or reduced model experiment—not necessarily model training.

## Inspect feasibility

Locate first-party code, releases or commits, containers, dependencies, data, weights, supplements, evaluation scripts, corrections, licenses, and access instructions. Record blockers such as:

- unavailable or private data;
- commercial APIs, credentials, paid services, or expired endpoints;
- incompatible runtimes or undeclared versions;
- hardware, storage, time, memory, or energy demands;
- missing preprocessing, seeds, prompts, hyperparameters, workloads, or study protocols;
- ambiguity between paper, documentation, configuration, and code.

Estimate what the current environment can support. Reduce scope explicitly when full reproduction is impractical. Ask before incurring meaningful cost, downloading unusually large artifacts, using credentials, or changing external systems.

## Read the implementation

Trace the executed path from entry point to result:

1. Identify environment and installation definitions.
2. Identify the canonical demo, training, evaluation, benchmark, or analysis command.
3. Follow data ingestion, preprocessing, core method, output generation, and metric calculation.
4. Map paper concepts and equations to files, functions, modules, parameters, or scripts.
5. Compare paper settings with repository defaults and released checkpoints.
6. Inspect hidden assumptions in scripts, environment variables, paths, cached artifacts, and hardware branches.

Record meaningful paper–code mismatches with exact paper and code locators. Do not assume a newer repository revision represents the paper version.

## Execute incrementally

Use a contained, repeatable environment appropriate to the project. Preserve the original official source and pin its revision. Keep local patches minimal and explain their necessity; prefer wrapper scripts, separate configurations, or a small patch over unrelated refactoring.

Progress through the smallest useful checks:

- verify toolchain and imports;
- validate a tiny input or dry run;
- run the official minimal example;
- run the target evaluation or reduced experiment;
- scale only when earlier evidence justifies it.

Capture commands, working directory, environment and dependency versions, hardware, data and model versions, configuration, seed, code revision and patches, timestamps when relevant, stdout or logs, outputs, and metric computation. Retain failed runs when they teach something, while excluding secrets and disposable bulk.

Never mark a result reproduced based only on successful installation, code inspection, or a process exit code. Verify that the produced artifact and metric correspond to the intended claim.

## Debug systematically

Preserve the first complete error and a minimal reproducer. Classify the failure before changing code:

- acquisition or permissions;
- environment or dependency;
- build or platform;
- data schema or preprocessing;
- configuration or checkpoint;
- resource exhaustion;
- numerical or stochastic behavior;
- metric or evaluation mismatch;
- paper–code inconsistency;
- missing methodological detail.

Change one explanatory factor at a time when practical. Retest the smallest case, record the observation, and revert speculative changes that do not help. Distinguish a workaround that makes code run from a correction that restores the paper's intended behavior.

## Compare results

Align dataset and split, preprocessing, model or system version, checkpoint, workload, metric implementation, aggregation, seed count, hardware, and resource budget before computing a gap.

Report:

- paper value and locator;
- reproduced value with uncertainty or run count;
- absolute and relative difference when meaningful;
- controlled differences in setup;
- plausible explanations ranked by evidence;
- diagnostic experiments that could discriminate among explanations.

Avoid attributing a gap to randomness without seed evidence. Avoid calling values equivalent when uncertainty, rounding, or practical tolerance has not been considered.

## Preserve a usable record

Let `reproduce/` grow from actual work. A simple effort may need only one readable file containing target, environment, commands, outcome, and blockers. Add `official/`, `scripts/`, `configs/`, `experiments/`, or `results/` only when artifacts warrant them.

Summarize what was actually completed, what succeeded, what failed, which claims are confirmed, which remain untested, and the highest-value next action. Keep raw logs or large outputs linked from the readable summary rather than pasting them indiscriminately.
