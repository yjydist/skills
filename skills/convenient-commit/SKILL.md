---
name: convenient-commit
description: Analyze all uncommitted Git changes, divide them into the smallest meaningful and independently reviewable, verifiable, and revertible units, and create separate commits following Conventional Commits. Use when the user asks to organize, split, or commit mixed repository changes.
---

# Convenient Commit

Analyze all uncommitted changes in the current Git repository, divide them into the smallest meaningful commit units, and commit each unit separately using Conventional Commits.

A commit unit is one semantic claim: its commit message states the claim and its diff contains exactly the changes needed to make that claim true. It must be independently understandable, reviewable, verifiable, and revertible.

## Default behavior

Execute the complete workflow automatically:

1. Inspect all uncommitted changes.
2. Identify the semantic change atoms, including separate atoms inside the same file or hunk.
3. Draft a message for each candidate unit before staging it.
4. Split and audit the candidates until each is the smallest meaningful unit.
5. Stage and validate each unit precisely.
6. Create the commits in dependency order.
7. Report only the hashes and messages of the newly created commits.

Do not ask the user to approve the commit plan unless a genuine ambiguity or safety risk prevents a reliable decision.

Do not print the commit plan during normal execution. Keep the analysis internal.

## Repository inspection

Inspect all relevant repository state before making any commit:

* staged changes
* unstaged changes
* untracked files
* recent commit history
* repository-specific contribution or agent instructions
* available build, lint, formatting, and test commands

Use commands such as:

```bash
git status --short
git diff
git diff --cached
git ls-files --others --exclude-standard
git log -n 20 --format="%h %s"
```

Also inspect relevant repository instructions when present, including files such as:

```text
AGENTS.md
CLAUDE.md
CONTRIBUTING.md
README.md
```

Use recent commit history to infer the repository's preferred:

* commit-message language
* scope naming
* capitalization
* terminology
* Conventional Commit style

If the repository has no clear convention, use concise English commit messages.

## Smallest meaningful commit

Partition changes by semantic outcome, not by feature request, ticket, file, directory, or module.

A commit is the smallest meaningful unit when all of the following are true:

* its message describes one clear result
* every included change directly contributes to that result
* all changes required to complete and verify that result are included
* no proper subset could be a valid, independently meaningful commit
* removing the commit would reverse that result without reversing an independent result

Interpret smallest semantically, not numerically. Do not use line count, file count, or hunk count as the unit of meaning. Do not create mechanical micro-commits, incomplete scaffolding, or other states with no independently useful center.

Treat each independently observable behavior, fix, refactoring, configuration outcome, documentation outcome, or maintenance result as a separate change atom. Identify separate atoms even when they appear in the same file or diff hunk.

Group atoms only when a hard dependency makes separate commits incomplete, misleading, unbuildable, or unverifiable. Shared context is not a hard dependency. Belonging to the same feature, ticket, layer, module, or file is not sufficient reason to combine atoms.

## Message-first partitioning

Draft the Conventional Commit message before staging a candidate unit. Treat the message as the promise and the diff as its proof.

For each candidate:

1. Write the narrowest message that describes its observable result.
2. Select only the implementation and direct supporting evidence required by that message.
3. Apply the commit-unit audit below.
4. Split the candidate whenever the audit reveals more than one independently meaningful result.
5. Repeat until every candidate passes.

Apply these five checks:

1. **Single-center check:** Express the result as one precise imperative description. Conjunctions such as `and`, slashes, lists, or umbrella terms such as `misc`, `various`, and `cleanup` are strong signals that the candidate contains multiple centers. A conjunction is acceptable only when it describes one technically inseparable operation.
2. **Necessity check:** Confirm that every file and hunk is necessary for the message. Move any change that the message does not explain to another unit.
3. **Separability check:** Ask whether a reviewer could reasonably accept one subset and reject another. If yes, split them.
4. **Revertibility check:** Ask whether one subset could be reverted while intentionally retaining another. If yes, split them.
5. **Validity check:** Confirm that the candidate leaves the repository in a usable state and passes the validation relevant to its claim. Never create an intentionally broken intermediate commit.

The message may describe an operation whose mechanical consequences span many files. For example, `refactor(api): rename createUser to registerUser` can include the declaration, all required callers, and direct tests because those edits are consequences of the single rename.

## Split and grouping rules

Default to separate commits for:

* independently usable sub-capabilities within one larger feature
* independent fixes in the same module, file, or hunk
* a behavior-preserving preparatory refactoring and a later behavior change when each is valid alone
* formatting or mechanical renames and unrelated semantic changes
* independent configuration, documentation, CI, dependency, generated, or maintenance changes
* tests that have an independent purpose and do not directly verify another changed behavior

Keep changes together only when they jointly express one semantic claim, including:

* a behavior change and the focused tests or regression tests that directly verify it
* an API or schema change and the caller, consumer, or migration updates required for the commit to remain valid
* a dependency declaration and its corresponding lockfile update
* handwritten source and generated artifacts that are two required representations of the same change
* implementation and documentation that must change together to avoid an incorrect or unusable interface

Put an independently valid foundational refactoring before the commits that depend on it. Order all units according to their hard dependencies.

## Large-candidate review

There is no fixed line-count or file-count limit. Size is a warning signal, not a partitioning rule.

When a candidate spans many files, hunks, behaviors, or repository areas, perform a second message-first audit even if it passed once. Keep it large only when every included atom is necessary for the same claim and any further split would produce an incomplete, invalid, or misleading commit. Keep that reasoning internal.

## Splitting files and hunks

A file may belong to multiple commits when it contains changes serving different intents.

Do not stage an entire file merely because part of it belongs to the current commit.

Use precise staging techniques such as:

```bash
git add -p
git reset -p
git restore --staged
```

Inspect the staged diff before every commit:

```bash
git diff --cached
git diff --cached --stat
```

If one diff hunk contains multiple unrelated changes, split or edit the patch when it can be done safely.

Do not modify source code solely to manufacture a cleaner commit boundary unless the modification is itself necessary and behavior-preserving.

Never use destructive commands such as:

```bash
git reset --hard
git checkout -- .
git clean -fd
```

Do not discard or overwrite user changes.

## Existing staged changes

Treat existing staged changes as part of the complete uncommitted change set.

Do not assume that the current staging boundary is correct.

You may reorganize the index when necessary, provided that:

* no working-tree content is discarded
* no user change is lost
* only the staging state is altered
* the final commits follow logical boundaries

Use non-destructive index operations only.

## Untracked files

Inspect untracked files before deciding whether they belong in a commit.

Do not automatically commit:

* environment files
* editor state
* caches
* temporary files
* logs
* build outputs
* local databases
* credentials
* machine-specific configuration

Check whether an untracked file should instead be added to `.gitignore`.

Do not modify `.gitignore` unless that modification is clearly part of the intended repository change.

## Sensitive and suspicious content

Before committing, check for content that appears to contain:

* passwords
* API keys
* access tokens
* private keys
* credentials
* personal data
* local environment configuration
* accidentally generated large files

If sensitive content may be present, stop before committing it and clearly identify the blocker.

Do not expose the suspected secret value in the response.

Also stop when:

* the purpose of a significant change cannot be inferred
* the changes appear incomplete or corrupted
* an unresolved merge, rebase, cherry-pick, or bisect is active
* the repository is in an unsafe Git state
* reliable splitting would require guessing the user's intent
* committing would include obviously accidental files

## Conventional Commits

Use this format:

```text
<type>(<scope>): <description>
```

The scope is optional:

```text
<type>: <description>
```

Supported types include:

* `feat`: introduce user-visible functionality
* `fix`: correct defective behavior
* `refactor`: restructure code without intentionally changing behavior
* `perf`: improve performance
* `test`: add or revise tests without changing production behavior
* `docs`: change documentation
* `style`: make non-semantic formatting or style changes
* `build`: change dependencies or build tooling
* `ci`: change continuous-integration configuration
* `chore`: perform repository maintenance not covered by another type
* `revert`: revert a previous commit

Choose the type according to the primary intent of the commit, not merely the files modified.

Use a scope only when it identifies a stable and meaningful repository component.

Descriptions must:

* state what the commit accomplishes
* be concise and specific
* use imperative wording
* avoid a trailing period
* avoid vague descriptions

Avoid messages such as:

```text
update code
fix stuff
misc changes
make changes
code cleanup
```

Prefer messages such as:

```text
feat(auth): add refresh token rotation
fix(parser): reject unterminated string literals
refactor(storage): extract transaction retry policy
test(api): cover duplicate request handling
build(deps): upgrade grpc dependencies
```

For breaking changes, follow the repository's established Conventional Commit convention. When no convention exists, use `!` and an explanatory commit body:

```text
feat(api)!: replace legacy pagination parameters
```

## Validation

Before each commit:

1. Reapply all five commit-unit checks to the complete staged diff.
2. Confirm that the staged diff contains only the claim made by the drafted message.
3. Confirm that all files necessary to implement and verify that claim are included.
4. Check for accidental debug code, generated noise, or sensitive data.
5. Run the smallest relevant validation available.

Relevant validation may include:

* formatting checks
* static analysis
* compilation
* type checking
* unit tests
* targeted integration tests
* repository-provided verification commands

Prefer targeted validation for the current commit over repeatedly running an unnecessarily expensive full test suite.

Run broader validation after all commits when practical.

Require each commit to remain buildable and to pass the checks relevant to its claim. If two atoms can pass only when applied together, treat that as evidence of a hard dependency and keep them in one unit. Do not trade a valid history for a larger number of commits.

If validation fails because of the changes being committed, fix the issue only when the correction is clearly within the current intent.

If the failure is unrelated, pre-existing, or cannot be safely resolved, stop and report the blocker instead of creating a misleading commit.

## Commit execution

For every logical commit unit:

1. Start from the candidate's drafted Conventional Commit message.
2. Stage only the files and hunks required by that message.
3. Inspect and audit the complete staged diff against the message.
4. Run relevant validation.
5. Finalize the message without widening it to accommodate unrelated changes.
6. Create the commit.
7. Verify that the commit was successfully created.
8. Continue with the remaining uncommitted changes.

Do not:

* push commits
* amend existing commits
* rebase history
* squash existing commits
* modify remote branches
* create or switch branches
* change Git configuration
* bypass hooks with `--no-verify`
* sign commits unless signing is already configured and occurs normally

Respect repository hooks.

If a hook modifies files, inspect those modifications and determine whether they belong in the current commit before proceeding.

## Completion checks

After creating the commits:

```bash
git status --short
git log --format="%H %s" -n <number-of-new-commits>
```

Confirm that:

* every intended change was committed
* no unintended change was committed
* remaining uncommitted files, if any, are intentionally excluded
* the reported commits are exactly the commits created during this run

## Final response

When all commits are successfully created, output only the newly created commit hash and commit message.

Use one commit per line, ordered from oldest to newest:

```text
<commit-hash> <commit-message>
```

Example:

```text
71f9e17b8a32 feat(auth): add refresh token rotation
d84ca29f013e test(auth): cover expired refresh tokens
```

Use a 12-character abbreviated commit hash unless the user explicitly requests the full hash.

Do not include:

* headings
* explanations
* commit-plan details
* file lists
* diff summaries
* validation results
* bullet points
* closing remarks

If no commit was created because there were no uncommitted changes, respond with:

```text
No changes to commit
```

If execution is blocked, do not pretend that the operation succeeded. Briefly state the blocking condition and the action required to resolve it.
