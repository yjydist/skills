---
name: convenient-commit
description: -|
  Analyze all uncommitted Git changes, divide them into coherent atomic commit units, and create separate commits following Conventional Commits. 
  Use when the user asks to organize, split, or commit mixed repository changes.
---

# Convenient Commit

Analyze all uncommitted changes in the current Git repository, divide them into appropriately scoped logical commit units, and commit each unit separately using Conventional Commits.

A logical commit unit is a coherent group of changes that represents one clear intent and can be independently understood, reviewed, verified, and reverted.

## Default behavior

Execute the complete workflow automatically:

1. Inspect all uncommitted changes.
2. Determine the logical commit units.
3. Stage each unit precisely.
4. Validate the staged changes.
5. Create the commits.
6. Report only the hashes and messages of the newly created commits.

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

## Commit-unit principles

Partition changes by intent, not merely by file.

Each commit must represent one coherent logical change.

Prefer commits that are:

* logically cohesive
* independently understandable
* independently reviewable
* independently revertible
* as independently verifiable as practical

Do not create arbitrary commits merely to reduce line count or file count.

Do not combine unrelated changes just because they modify the same file or module.

Do not separate tightly coupled changes merely because they occur in different files.

## Grouping rules

Normally keep the following together:

* a feature and the tests directly verifying that feature
* a bug fix and its regression test
* an API change and the immediately required caller updates
* a dependency change and its corresponding lockfile update
* an implementation change and documentation required to explain that same change

Normally keep the following separate:

* unrelated features
* unrelated bug fixes
* behavior changes and unrelated refactoring
* pure formatting and semantic changes
* mechanical renames and functional changes
* dependency upgrades and unrelated source changes
* generated artifacts and unrelated handwritten changes
* CI changes and unrelated application changes
* documentation changes unrelated to the implementation being committed

A refactoring may be committed before a dependent feature when doing so produces a cleaner and independently valid history.

Order commits according to dependency relationships. Foundational changes should precede changes that depend on them.

## Commit size

There is no fixed line-count or file-count limit.

A commit is appropriately sized when it contains the complete implementation of one clear intent and excludes unrelated intent.

Do not over-split one logical change into artificial micro-commits.

Do not create commits that contain only meaningless intermediate states.

Whenever practical, each commit should leave the repository in a buildable and testable state.

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

1. Confirm that the staged diff contains only the intended logical commit unit.
2. Confirm that all files necessary for that unit are included.
3. Confirm that unrelated hunks are not staged.
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

If validation fails because of the changes being committed, fix the issue only when the correction is clearly within the current intent.

If the failure is unrelated, pre-existing, or cannot be safely resolved, stop and report the blocker instead of creating a misleading commit.

## Commit execution

For every logical commit unit:

1. Stage only the files and hunks belonging to that unit.
2. Inspect the complete staged diff.
3. Run relevant validation.
4. Generate a precise Conventional Commit message.
5. Create the commit.
6. Verify that the commit was successfully created.
7. Continue with the remaining uncommitted changes.

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
