# REPRODUCT.md generation reference

Load this reference only after the paper model and section notes exist. The reproduction plan converts the paper's central claims into an ordered, auditable workflow. It must be specific enough that a competent reader can execute it without making hidden methodological decisions.

## What counts as reproduced

Cover every result needed to support the paper's central conclusions. A target may be a table row, figure panel, theorem, numerical analysis, qualitative coding result, system property, or other checkable artifact. Do not require every supplementary result unless the conclusion depends on it.

Use two tracks when first-party artifacts exist:

1. **Official reproduction:** run an immutable version of the authors' code, data, configuration, and evaluation path.
2. **Independent verification:** independently implement, derive, or recompute the central mechanism and compare intermediate or final results on at least one representative target.

Calling the first track a rerun keeps the evidential distinction clear. The independent track need not rebuild an entire large system, but it must exercise the mechanism that makes the central result meaningful.

Whenever the plan contains an `official-full` task, include at least one `independent-full` task. If no usable first-party execution path exists, omit `official-full`, explain the gap, and use the blocked protocol where it affects a central target.

## Establish acceptance before execution

Create one target for each central claim and assign consecutive IDs `T001`, `T002`, and so on. Each target must name:

- the claim and exact paper locator;
- the result or artifact to reproduce;
- the expected value, qualitative relation, proof obligation, or corpus property;
- the acceptance rule;
- the evidence file that will demonstrate the outcome.

Choose acceptance rules in this order:

1. Use uncertainty intervals, thresholds, tolerances, or tests reported by the paper or official repository.
2. For deterministic outputs, require exact hashes or equality through the paper's displayed precision.
3. For stochastic outputs without a reported tolerance, match the paper's seed count when known; otherwise use at least three seeds, report the reproduced interval, require the paper's reported value to fall inside it, and preserve the claimed effect direction or ranking. Label this as an analyst-defined acceptance rule.
4. For qualitative or corpus claims, predefine the inclusion, coding, agreement, comparison, and discrepancy rules.
5. For proofs, define the statement, assumptions, dependency closure, edge cases, and the independent formal, symbolic, or numerical check.

Never weaken acceptance after seeing a failed result without recording the deviation as a new protocol version.

## Pin provenance and resources

Prefer immutable identities over mutable labels:

- repository URL plus commit SHA, not `main`;
- release asset URL plus checksum, not `latest`;
- dataset release, DOI, snapshot date, split manifest, and checksum;
- container digest or lockfile plus runtime and driver versions;
- model checkpoint identity and checksum;
- exact configuration files, command-line arguments, seeds, preprocessing, and evaluation scripts.

Record licenses, credentials, agreements, or manual access steps. Mark resource numbers as `reported`, `measured`, or `estimated`; do not present an estimate as a paper fact. Include CPU/GPU type and count, accelerator memory, RAM, storage, expected wall time, and expected monetary cost when they can be established.

Every plan must quantify monetary cost. Prefer the paper's reported cost; otherwise calculate an estimate from a dated public compute/storage rate or a stated local marginal-cost assumption. Keep exactly one machine-readable marker inside the `reproduction-resources` region: `<!-- cost-estimate: reported currency: USD amount: 12.34 -->`, replacing status, ISO 4217 currency, and non-negative decimal amount. Use status `estimated` for analyst calculations. Use `not-applicable` only with amount `0.00` and only when the workflow genuinely requires no paid resource; explain why visibly.

## Make tasks atomic

Assign consecutive task IDs `R001`, `R002`, and so on. Each checkbox should perform the smallest meaningful action that produces evidence another task can consume.

- Use one primary action per task. Split "download, preprocess, train, and evaluate" into separate tasks.
- Split independent configurations and seeds so one failure does not make the task ambiguous.
- Give every configuration-seed pair its own task ID. A manifest may define the matrix, but a single task that launches or accepts a job array is not atomic; expand every manifest row into a separate checkbox even when this makes the plan long.
- Separate command execution from verification when either produces a reusable artifact.
- A long training or data-collection run may remain one task when it is a single irreducible command, but preparation, launch, monitoring, and acceptance are separate tasks.
- State exact commands when the action is executable. For manual work, give a deterministic procedure and decision rule.
- Name every input and output path relative to a reproduction workspace chosen by the document.
- Refer only to earlier task IDs in `Depends on`. Use `none` when there is no dependency.
- Refer to one or more target IDs in `Targets`, or `none` for pure setup tasks.
- Write multiple `Depends on` or `Targets` IDs as comma-separated IDs only, for example `R001, R003` or `T001, T002`.
- Label every task with exactly one `Run class`: `setup`, `blocker`, `smoke`, `official-full`, `independent-full`, `evaluation`, or `archive`. Include at least one `smoke` task that runs a reduced deterministic fixture before expensive work and at least one `official-full` or `independent-full` task that can satisfy a central target. Smoke tasks validate plumbing but never satisfy a full-result acceptance rule by themselves.
- Map every target to at least one `official-full`, `independent-full`, or `evaluation` task. A smoke task may mention a target for diagnostic context, but it cannot be that target's only coverage.

Retain the exact English field labels below so the validator can inspect the document. Write their values and all surrounding prose in the notes language.

```markdown
<!-- task: R001 -->
- [ ] **R001 - [one-action task title]**
  - **Action:** [exact command or deterministic manual procedure]
  - **Run class:** [setup, blocker, smoke, official-full, independent-full, evaluation, or archive]
  - **Inputs:** [existing files, versions, values, or none]
  - **Produces:** [specific file, directory, log, hash, or decision record]
  - **Done when:** [observable pass condition]
  - **Source:** [paper/code/data locator supporting the instruction]
  - **Depends on:** [earlier R-IDs or none]
  - **Targets:** [T-IDs or none]
```

Do not leave bracketed generator instructions in the output.

## Handle missing information honestly

Use exactly one machine-readable status comment:

- `<!-- reproduce-status: ready -->` when the document contains everything needed to execute every central target.
- `<!-- reproduce-status: blocked -->` when a fidelity-critical artifact, parameter, access right, or method detail is unavailable.

For a blocked plan:

- identify the missing fact or artifact and the exact targets it blocks;
- assign consecutive blocker IDs `B001`, `B002`, and so on, recording each inside the task region with `<!-- blocker: B001 targets: T001,T002 -->` immediately before its resolution task;
- give that resolution task `Run class: blocker`; treat its observable completion condition as the stop gate;
- create atomic tasks to search official supplements, repository history, issues, archived releases, or author channels;
- define what evidence resolves the blocker;
- make every affected `official-full`, `independent-full`, or `evaluation` task depend directly or transitively on the blocker resolution task;
- state visibly that exact reproduction is not currently guaranteed.

Do not fill gaps with plausible defaults. A documented blocker is more useful than a runnable but methodologically different recipe. Optional practical substitutes may appear in a clearly labeled exploratory section, but they cannot satisfy the blocked target.

## Adapt by paper type

Use every applicable lens for mixed papers.

### Algorithm, machine-learning, and systems papers

Lock source, code, data, models, environment, hardware topology, preprocessing, training or build configuration, seeds, inference or workload generation, and evaluation. Add a small deterministic fixture that compares the official and independent implementation at an intermediate boundary before launching the full run.

### Empirical and scientific papers

Lock the sampling frame, acquisition dates, inclusion and exclusion rules, raw-to-analysis transformations, treatment or exposure definitions, outcomes, controls, statistical model, missing-data policy, multiple-testing policy, and robustness checks. Preserve a row-count or cohort-flow ledger at every transformation.

When the central model has several free parameters, sweep every parameter that changes the claimed conclusion, including significance or error-rate parameters such as `alpha`. Do not vary the visually prominent parameters while silently fixing another free parameter at a conventional default. Name the grid and evidence artifact for every parameter.

### Theoretical and mathematical papers

Turn the dependency graph into tasks: define the formal setting, restate each required lemma with assumptions, reconstruct proof steps, check boundary cases, and independently verify the central statement using a proof assistant, symbolic algebra, exhaustive finite cases, or numerical stress tests when applicable. Do not invent an experiment merely to fit the template.

### Survey, review, position, and conceptual papers

Reproduce database selection, exact search strings, date ranges, deduplication, inclusion and exclusion, screening, coding schema, inter-rater handling, synthesis, and claim-to-source mapping. For a position paper, reconstruct the cited evidence corpus and test whether each central premise follows from it.

## Required document structure

Use the following structure. Translate visible headings and explanatory prose, but retain all HTML comments, IDs, top metadata field labels, and exact task field labels. Keep the machine-readable regions in the displayed order. Required content must remain visible Markdown; do not hide targets, tasks, or prose inside HTML comments or fenced examples.

```markdown
# REPRODUCE: [paper title]

- **Paper:** [canonical citation]
- **Paper version:** [version/date]
- **Plan version:** 1
- **Workspace:** [relative directory used by the commands]
- **Notes:** [relative link to notes/00.abstract.md]

<!-- reproduce-status: ready -->

## Reproduction status

<!-- reproduction-status -->

[State whether the plan is ready. If blocked, name the blockers and affected targets.]

<!-- /reproduction-status -->

## Definition of done

<!-- reproduction-targets -->

| ID | Central claim and source locator | Result to reproduce | Acceptance rule | Evidence artifact |
|---|---|---|---|---|
| T001 | ... | ... | ... | ... |

<!-- /reproduction-targets -->

## Provenance and required resources

<!-- reproduction-resources -->

<!-- cost-estimate: estimated currency: USD amount: 12.34 -->

[Immutable paper, code, data, model, environment, license, hardware, storage, time, and cost information.]

<!-- /reproduction-resources -->

## Task checklist

<!-- reproduction-tasks -->

[Atomic task blocks in dependency order.]

<!-- /reproduction-tasks -->

## Evidence package

<!-- reproduction-evidence -->

[Exact directory layout, manifests, logs, metrics, plots, environment capture, deviations, and final comparison report to preserve.]

<!-- /reproduction-evidence -->

## Completion report

<!-- reproduction-completion -->

[The commands or deterministic procedure for deciding target pass/fail without changing the predefined acceptance rules.]

<!-- /reproduction-completion -->
```

Replace the status value and every generator instruction. Every checkbox starts unchecked because the document is a plan for the reader, not evidence that this skill ran the experiments.

## Final quality check

Before saving, verify that:

- every central conclusion maps to at least one target and every target maps to executable or explicitly blocked tasks;
- every task has one action, all eight required fields, a unique consecutive ID, valid dependencies, and a concrete completion condition;
- every configuration-seed pair has its own task instead of being hidden inside a batch launcher;
- every target has a full or evaluation task; smoke-only coverage is invalid;
- an official-full track always has an independent-full verification track;
- commands use pinned inputs and write named artifacts instead of relying on ambient state;
- official reruns, independent checks, smoke tests, exploratory substitutes, and full reproduction runs are labeled distinctly through `Run class`;
- the resource ledger makes an expensive or inaccessible run visible before execution;
- the resource ledger includes one valid cost-estimate marker and visibly explains its reported, estimated, or not-applicable amount;
- every blocker marker is immediately followed by a blocker-class resolution task, and affected full tasks depend on that gate;
- the H1, top metadata fields, region order, target rows, and task checkboxes are present as visible Markdown rather than commented-out or example-only content;
- the evidence package can diagnose discrepancies without rerunning everything;
- no inaccessible artifact, missing parameter, expected value, or successful result has been invented;
- `notes/00.abstract.md` links to this file and this file links back to the overview.
