---
name: reproduce-paper
description: Plan, execute, debug, or compare an explicitly requested reproduction, rerun, claim-level validation, or independent implementation of one academic paper. Use only when the user clearly asks for reproduction or implementation work; merely explaining a paper or inspecting official code read-only does not qualify. Before planning or acting, require a clear fidelity mode, target, allowed deviations, resource boundary, and success evidence, and ask the user when any of these choices are materially ambiguous.
---

# Reproduce Paper

Reproduce only the target the user has deliberately defined. Never silently convert paper study into an experiment or one reproduction meaning into another.

## Enforce the fidelity gate

Before planning, writing files, preparing an environment, downloading substantial artifacts, or running commands, establish all of the following:

- the exact paper and version;
- the target claim, result, mechanism, table, figure, theorem, or artifact;
- one fidelity mode;
- what may and may not change;
- the resource, time, storage, hardware, access, and monetary limits;
- the output and evidence that count as success.

Ask the user when a material choice is missing or ambiguous. Do not infer permission to substitute data, code, models, APIs, metrics, hardware, or methodology.

Use exactly one starting mode:

1. **Exact rerun:** pin the paper-era official code, data, configuration, environment, model, and evaluation path. Treat an unavailable fidelity-critical component as a blocker; do not silently modernize it.
2. **Claim-targeted reproduction:** name the exact claim and locator, permitted substitutions, controlled differences, and acceptance rule. Limit conclusions to that target.
3. **Independent idea implementation:** define the core mechanism or invariants to preserve and the components allowed to change. Call the result an implementation, adaptation, or validation—not reproduction of the paper's reported result.

If the user's request mixes modes, separate the targets and obtain confirmation for each.

## Minimize default side effects

- For a planning-only request, answer in the conversation unless the user explicitly asks to save the plan.
- Create or modify files only when the user asks to save a plan or authorizes execution.
- When execution is authorized, create the smallest useful workspace and record; do not impose a full directory tree or mandatory `REPRODUCT.md`.
- Inspect existing files before editing and preserve human-authored plans, results, and failed-run evidence.
- Ask before meaningful cost, unusually large downloads, credentials, paid services, or changes to external systems.

## Establish versions and feasibility

Read [references/fidelity-and-execution.md](references/fidelity-and-execution.md) before feasibility analysis, environment setup, execution, debugging, or result comparison.

Prefer first-party paper, code, release, data, model, container, configuration, errata, and evaluation sources. Record:

- paper identity and version;
- source URLs and access date;
- code revision or release;
- data, model, dependency, and environment versions;
- current date and hardware;
- every patch, wrapper, substitution, and deviation.

Do not assume the latest repository revision represents the paper version. Surface expired endpoints, unavailable artifacts, incompatible runtimes, missing parameters, and resource limits before execution.

## Execute against evidence

Translate the target into an artifact or procedure, input and configuration, expected output, comparison rule, and evidence to retain.

Progress from the smallest diagnostic that can falsify the setup:

1. verify acquisition and toolchain;
2. validate a tiny input or deterministic check;
3. run the smallest official or paper-faithful path relevant to the target;
4. run the target evaluation or independent implementation;
5. scale only when earlier evidence justifies it.

Never call installation, code inspection, a successful exit code, or a smoke test reproduction of a paper result. Verify the intended artifact and metric.

## Report without overclaiming

Keep these categories explicit:

- **Paper:** reported or proved by the selected paper version.
- **Official code:** observed in the pinned official artifact.
- **Current run:** directly measured now.
- **Deviation:** a controlled difference from the selected mode.
- **Adaptation:** an intentional modern or independent implementation choice.
- **Interpretation:** an explanation consistent with the evidence.
- **Unknown:** unresolved because evidence is missing or conflicting.

For exact or claim-targeted comparisons, report the paper value and locator, current value and run count or uncertainty, absolute or relative gap when meaningful, controlled setup differences, and plausible explanations ranked by evidence.

For independent implementations, report which invariants were preserved, which components changed, what was validated, and why the result is not evidence that the paper's reported numbers were reproduced.

Finish with what was actually completed, what succeeded or failed, retained evidence, unresolved blockers, and the highest-value next diagnostic. List only files actually created or modified.
