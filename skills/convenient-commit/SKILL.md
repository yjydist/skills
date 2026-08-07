---
name: convenient-commit
description: Analyze all uncommitted Git changes, divide them into the smallest meaningful and independently reviewable, verifiable, and revertible units, and create separate commits following Conventional Commits. Use when the user asks to organize, split, or commit mixed repository changes.
allowed-tools: Bash
disable-model-invocation: true
---

# Convenient Commit

Split all uncommitted changes in the current repository into the smallest meaningful commit units, and commit each unit separately as a Conventional Commit.

A commit unit is one semantic claim: the message states the claim and the diff contains exactly the changes needed for it, so it can be reviewed, verified, and reverted independently. Keep the analysis internal and never print the commit plan.

## Workflow

1. Inspect the repository state and its commit conventions.
2. Partition the changes into commit units.
3. For each unit in dependency order: stage it precisely, run the commit checklist, validate it, and create the commit.
4. Run the completion checks and report only the new commits.

Do not ask the user to approve the plan unless a genuine ambiguity or safety risk prevents a reliable decision.

## Inspection

```bash
git status --short
git diff
git diff --cached
git ls-files --others --exclude-standard
git log -n 20 --format="%h %s"
```

Read repository instructions when present, such as `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, and `README.md`. Infer commit-message language, scope naming, capitalization, and style from recent history. If the repository has no convention, or no commits yet, use concise English.

## Partitioning

Partition by semantic outcome, not by file, module, ticket, or line count. Draft each unit's message before staging it: the message is the promise and the diff is the proof.

Split by default:

* independently usable sub-capabilities of a larger feature
* independent fixes, including ones inside the same file or hunk
* a behavior-preserving refactoring and a later behavior change when each is valid alone
* formatting or mechanical renames and unrelated semantic changes
* independent configuration, documentation, CI, dependency, generated, or maintenance changes
* tests with an independent purpose that do not directly verify a changed behavior

Keep together only when separation would be incomplete, unbuildable, or misleading:

* a behavior change and the tests that directly verify it
* an API or schema change and the caller or migration updates it requires
* a dependency declaration and its lockfile
* handwritten source and the generated artifacts required with it
* implementation and documentation that must change together

Commit foundations before the units that depend on them. If all changes express one claim, create one commit; do not hunt for atoms, and never create mechanical micro-commits or incomplete scaffolding.

## Staging

Treat already-staged changes as part of the change set and reorganize the index freely, but never lose working-tree content. Never use interactive commands such as `git add -p` or `git reset -p`, destructive commands such as `git reset --hard`, `git checkout -- .`, or `git clean -fd`, and never discard or overwrite user changes. Do not modify source code merely to manufacture a cleaner commit boundary.

Stage whole files with:

```bash
git add -- <path>
git restore --staged <path>
```

Stage selected hunks by passing a patch to `git apply --cached` on standard input; no temporary file is needed:

```bash
git apply --cached <<'EOF'
diff --git a/<file> b/<file>
--- a/<file>
+++ b/<file>
@@ ... @@
 <hunks belonging to the current unit only>
EOF
```

Extract the hunks from `git diff` output and keep their headers and line counts exact; a patch for a new file must retain its `new file mode` line and `--- /dev/null` header. When hunks of the same file were already staged, rewrite the context lines to match the index state rather than the working tree. Undo staging mistakes with `git restore --staged <path>`.

Register an untracked file that must be split with `git add -N <path>`, then split it like any modified file.

Before every commit, confirm the index matches the drafted message:

```bash
git diff --cached
git diff --cached --stat
```

## Commit checklist

Apply once per unit to the complete staged diff; re-check units spanning many files or areas especially carefully.

1. The message describes one result, with no umbrella terms such as `misc`, `various`, or `cleanup`.
2. Every staged hunk is explained by the message.
3. Everything needed to complete and verify the claim is staged.
4. No secrets, debug leftovers, generated noise, or accidental files are staged.
5. The repository remains usable; never create intentionally broken intermediate commits. Two atoms that pass validation only together are one unit.

## Validation

Run the smallest relevant validation available for the current claim: formatting checks, linting, compilation, type checking, targeted tests, or repository-provided commands.

Validation runs against the working tree, which still contains the atoms reserved for later commits, so ignore failures caused only by those uncommitted atoms. When strict isolation is genuinely required, verify the new commit in a throwaway worktree created with `git worktree add`, and remove it afterwards.

Run broader validation after all commits when practical. If validation fails because of the current unit's changes, correct it only when the correction clearly belongs to the unit's claim; otherwise stop and report the blocker.

## Committing

Use Conventional Commits:

```text
<type>(<scope>): <subject>
```

The scope is optional and names a stable repository component. Types: `feat`, `fix`, `refactor`, `perf`, `test`, `docs`, `style`, `build`, `ci`, `chore`, `revert`; choose by intent, not by files touched. Mark breaking changes with `!` and a `BREAKING CHANGE:` footer. Subjects are imperative, specific, at most 50 characters, and without a trailing period; body lines are at most 72 characters. Repository conventions override these defaults.

Create a commit with `git commit -m "<message>"` for a subject-only message, or with a heredoc when a body or footer is present:

```bash
git commit -F - <<'EOF'
feat(api)!: replace legacy pagination parameters

The offset parameters are replaced by a cursor-based page token.

BREAKING CHANGE: offset and limit are removed.
EOF
```

Never create an empty commit; do not use `--allow-empty`.

Respect repository hooks. If a hook modifies files, fold those modifications into the current unit. If a hook rejects the commit, fix the problem within the same unit and commit again; never bypass hooks with `--no-verify`.

Do not: push, amend, rebase, squash, modify remote branches, create or switch branches, change Git configuration, or sign commits manually.

## Untracked files

Do not automatically commit environment files, editor state, caches, temporary files, logs, build outputs, local databases, credentials, or machine-specific configuration. Consider whether such a file belongs in `.gitignore` instead, and do not edit `.gitignore` unless that edit is clearly part of the intended change.

## Stop conditions

Stop and report the blocker clearly, never exposing suspected secret values:

* the diff appears to contain passwords, keys, tokens, personal data, or unexpectedly large files
* a merge, rebase, cherry-pick, or bisect is unresolved, or the repository state is otherwise unsafe
* the intent of a significant change cannot be inferred, or the changes look incomplete or corrupted
* committing would include obviously accidental files

## Completion and response

```bash
git status --short
git log --abbrev=12 --format="%h %s" -n <number-of-new-commits>
```

Confirm that every intended change was committed, nothing unintended was committed, and any remaining files are intentionally left out.

Respond with one line per new commit, oldest first, and nothing else:

```text
71f9e17b8a32 feat(auth): add refresh token rotation
d84ca29f013e test(auth): cover expired refresh tokens
```

If there was nothing to commit, respond with `No changes to commit`. If blocked, briefly state the blocker and the action required.

## Worked example

Uncommitted changes:

* `src/auth.py`: one hunk fixes expired refresh-token handling, a separate hunk renames `session_cache` to `token_cache`
* `tests/test_auth.py`: a new test reproducing the expired-token bug
* `package.json` and `package-lock.json`: a gRPC dependency upgrade
* `scratch-notes.txt`: an untracked personal note file

The two `src/auth.py` hunks are separate atoms despite sharing a file; the fix and its regression test form one unit; the dependency files form one unit; the note file is neither committed nor deleted. The rename is committed first:

```text
a1b2c3d4e5f6 refactor(auth): rename session_cache to token_cache
b7c8d9e0f1a2 fix(auth): reject expired refresh tokens
c3d4e5f6a7b8 build(deps): upgrade grpc dependencies
```
