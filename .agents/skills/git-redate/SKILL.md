---
name: git-redate
description: >-
  Rewrite Git commit dates (author and committer) so that when pushed to GitHub
  they appear to have been made on a specific past date or across a date range.
  Use when the user asks to backdate, change, or fake Git commit dates, or invokes
  the command with a date argument or range like "aug08", "from sep 07 to sep 15",
  "2024-03-20", etc.
---

# Git Redate — Rewrite Commit Dates

## Purpose

Rewrite the **author date** and **committer date** of Git commits in the
current repository so they appear to originate from a user-specified date or
date range when pushed to GitHub.

## Usage Patterns

The user can invoke this skill with either a single date or a multi-day range,
optionally specifying commit scope:

```bash
# Single date
/git-redate aug08
/git-redate 2026-09-20
/git-redate -n 5 sep20

# Date range with explicit scope
/git-redate all commits between origin and head from sep 07 to sep 15
/git-redate --range origin/master..HEAD --from 2026-09-07 --to 2026-09-15
/git-redate HEAD~10..HEAD sep01..sep06
```

## Date & Range Parsing

Parse date arguments using these rules (in priority order):

| Format          | Example        | Interpretation                         |
| :-------------- | :------------- | :------------------------------------- |
| `YYYY-MM-DD`    | `2026-09-20`   | Exact date: September 20, 2026         |
| `monDD`         | `aug08`        | Month + day of current year: Aug 8     |
| `mon DD`        | `aug 08`       | Same as above with space               |
| `DD mon`        | `08 aug`       | Same as above, reversed                |
| `monthDD`       | `august08`     | Full month name: Aug 8 of current year |

- Month names are **case-insensitive** (`Sep`, `sep`, `SEPTEMBER` all work).
- If only month + day are given, assume the **current year**.
- Ranges can be specified via `from <start> to <end>` or `<start>..<end>`.

## Execution Engine: `scripts/redate.py`

This skill bundles a deterministic, zero-dependency Python script located at
`scripts/redate.py` (relative to this skill directory).

### Why `scripts/redate.py` instead of `git filter-branch`?
1. **Immunity to Dirty Working Trees**: Operates purely via Git plumbing (`git commit-tree` + `git update-ref`). It never touches the index or working directory, allowing safe execution even with uncommitted or untracked changes.
2. **Automated Zero-Diff Assertion**: Checks that `git diff <old_head> <new_head>` is 100% empty before updating the branch reference, preventing any tree divergence.
3. **Realistic Work Sessions**: Automatically splits commits across morning (09:30–12:30) and afternoon (14:00–18:00) blocks with natural jitter and strict monotonicity ($t_i > t_{i-1}$).
4. **Automatic Versioned Backups**: Creates `backup-before-redate-<tag-or-timestamp>` and updates `backup-before-redate`.
5. **Dry-Run Preview**: Supports `--dry-run` to preview the proposed schedule table without writing any refs.

## Execution Steps

### Step 1 — Parse Arguments & Scope
- If the user explicitly provided the commit scope in their prompt (e.g. `all commits between origin and head`, `HEAD~5..HEAD`), use it directly.
- If scope is omitted, default to `origin/<current-branch>..HEAD` if an upstream tracking branch exists, or ask the user.
- If a date range was specified, check whether weekend commits should be included or skipped (`--weekdays-only`).

### Step 2 — Confirm Target Schedule (or Dry-Run)
Run `scripts/redate.py` with `--dry-run` to display the planned timetable and ask the user for confirmation:

```bash
python3 <skill-dir>/scripts/redate.py --range <RANGE> --from <START> --to <END> --dry-run
```

### Step 3 — Execute Redate
Run `scripts/redate.py` without `--dry-run`:

```bash
python3 <skill-dir>/scripts/redate.py --range <RANGE> --from <START> --to <END>
```

For single-date invocations:

```bash
python3 <skill-dir>/scripts/redate.py -n <COUNT> --date <DATE>
```

### Step 4 — Verify
After rewriting, display the verification log:

```bash
git log --format="%H %ai %ci %s" -10
```

### Step 5 — Push Instructions
Inform the user that they need to **force push** to update the remote:

```bash
git push --force origin <branch>
```

> [!WARNING]
> Force pushing rewrites remote history. Only do this on repositories where you are the sole contributor or have coordinated with your team.
