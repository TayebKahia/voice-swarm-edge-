---
name: git-redate
description: >-
  Rewrite Git commit dates (author and committer) so that when pushed to GitHub
  they appear to have been made on a specific past date. Use when the user asks
  to backdate, change, or fake Git commit dates, or invokes the command with a
  date argument like "aug08", "jul15", "2024-03-20", etc.
---

# Git Redate — Rewrite Commit Dates

## Purpose

Rewrite the **author date** and **committer date** of Git commits in the
current repository so they appear to originate from a user-specified date when
pushed to GitHub.

## Usage Pattern

The user will invoke this skill with a date argument:

```
/git-redate aug08
/git-redate jul15
/git-redate 2024-03-20
```

## Date Argument Parsing

Parse the date argument using these rules (in priority order):

| Format          | Example        | Interpretation                         |
| :-------------- | :------------- | :------------------------------------- |
| `YYYY-MM-DD`    | `2024-03-20`   | Exact date: March 20, 2024             |
| `monDD`         | `aug08`        | Month + day of current year: Aug 8     |
| `mon DD`        | `aug 08`       | Same as above with space               |
| `DD mon`        | `08 aug`       | Same as above, reversed                |
| `monthDD`       | `august08`     | Full month name: Aug 8 of current year |

- Month names are **case-insensitive** (`Aug`, `aug`, `AUG` all work).
- If only month + day are given, assume **current year**.
- The resolved date should use **12:00:00 noon** in the user's local timezone
  as the base timestamp.

## Execution Steps

### Step 1 — Confirm the Target Date

After parsing the date argument, display the resolved date to the user and ask
for confirmation before proceeding. Example:

> **Resolved date:** August 8, 2025 (12:00:00)
> All commits will be rewritten to this date. Proceed?

### Step 2 — Determine Commit Scope

Ask the user which commits to redate:

- **All commits** on the current branch
- **Only the last N commits** (user specifies N)
- **A specific commit range** (e.g., `abc123..def456`)

Default to **all commits on the current branch** if the user doesn't specify.

### Step 3 — Spread Timestamps

To make the commit history look natural, **do not** assign the exact same
timestamp to every commit. Instead:

1. Start from the resolved date at **09:00 AM** local time.
2. Add a random offset of **5–45 minutes** between each successive commit.
3. This creates a realistic-looking commit timeline across the day.

### Step 4 — Rewrite Commits

Use `git filter-branch` or `git rebase` with environment variable overrides to
rewrite commits. The recommended approach uses `git filter-branch`:

```bash
git filter-branch -f --env-filter '
  export GIT_AUTHOR_DATE="<computed_timestamp>"
  export GIT_COMMITTER_DATE="<computed_timestamp>"
' --tag-name-filter cat -- --all
```

Alternatively, for a small number of commits, interactive rebase with
`--committer-date-is-author-date` works:

```bash
GIT_COMMITTER_DATE="<date>" git commit --amend --no-edit --date="<date>"
```

**Important:** On Windows (PowerShell), environment variable syntax differs.
Use the appropriate method:

```powershell
$env:GIT_COMMITTER_DATE = "<date>"
git commit --amend --no-edit --date="<date>"
```

Or use `git -c` flags, or run commands through `git bash` if available.

### Step 5 — Verify

After rewriting, run:

```bash
git log --format="%H %ai %ci %s" -10
```

Display the output to the user so they can confirm the dates look correct.

### Step 6 — Push Instructions

Inform the user that they need to **force push** to update the remote:

```bash
git push --force origin <branch>
```

> [!WARNING]
> Force pushing rewrites remote history. If others have cloned or forked the
> repo, they will need to re-clone. Only do this on repositories where you are
> the sole contributor or have coordinated with your team.

## Important Notes

- This skill **rewrites Git history**. Always create a backup branch first:
  ```bash
  git branch backup-before-redate
  ```
- The skill modifies both `GIT_AUTHOR_DATE` and `GIT_COMMITTER_DATE` so GitHub
  displays the intended date in both the commit list and contribution graph.
- GitHub's contribution graph uses the **author date** to place green squares.
