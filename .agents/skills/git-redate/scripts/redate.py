#!/usr/bin/env python3
"""
git-redate: Deterministic, safe Git commit timestamp rewriting.

Features:
- Pure plumbing (git commit-tree + git update-ref): safe even if the working tree is dirty.
- Supports single dates or date ranges across multiple days.
- Realistic work session distribution (morning/afternoon sessions, natural jitter).
- Monotonic timestamp assertion (t_i > t_{i-1}).
- Automatic versioned backup branch creation.
- Strict zero-diff pre-update validation.
- Dry-run preview mode.
"""

import argparse
import datetime
import os
import random
import re
import subprocess
import sys


MONTH_MAP = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "september": 9, "sept": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}


def run_git(cmd, check=True, text=True, input=None, env=None):
    """Run a git command and return its stdout."""
    res = subprocess.run(
        ["git"] + cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=text,
        input=input,
        env=env,
    )
    if check and res.returncode != 0:
        err_msg = res.stderr.strip() if text else res.stderr.decode("utf-8", errors="replace")
        raise RuntimeError(f"git {' '.join(cmd)} failed (code {res.returncode}): {err_msg}")
    return res.stdout.strip() if text else res.stdout


def parse_date(date_str, default_year=None):
    """
    Parse date from formats:
    - YYYY-MM-DD
    - monDD / monthDD (e.g. sep07, august15)
    - mon DD / DD mon (e.g. "sep 07", "07 sep")
    """
    date_str = date_str.strip().lower()
    if default_year is None:
        default_year = datetime.datetime.now().year

    # ISO format: YYYY-MM-DD
    iso_match = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", date_str)
    if iso_match:
        y, m, d = int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3))
        return datetime.date(y, m, d)

    # DD-MM-YYYY or DD/MM/YYYY
    dmy_match = re.match(r"^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$", date_str)
    if dmy_match:
        d, m, y = int(dmy_match.group(1)), int(dmy_match.group(2)), int(dmy_match.group(3))
        return datetime.date(y, m, d)

    # DD mon or DD month
    d_mon_match = re.match(r"^(\d{1,2})\s*([a-z]+)$", date_str)
    if d_mon_match:
        d = int(d_mon_match.group(1))
        mon_str = d_mon_match.group(2)
        if mon_str in MONTH_MAP:
            return datetime.date(default_year, MONTH_MAP[mon_str], d)

    # mon DD or month DD (or monDD, monthDD)
    mon_d_match = re.match(r"^([a-z]+)\s*(\d{1,2})$", date_str)
    if mon_d_match:
        mon_str = mon_d_match.group(1)
        d = int(mon_d_match.group(2))
        if mon_str in MONTH_MAP:
            return datetime.date(default_year, MONTH_MAP[mon_str], d)

    raise ValueError(f"Unable to parse date string: {date_str}")


def detect_repo_timezone():
    """Detect current repository timezone from latest commit, default to +0100."""
    try:
        tz = run_git(["log", "-1", "--format=%z"]).strip()
        if re.match(r"^[+-]\d{4}$", tz):
            return tz
    except Exception:
        pass
    return "+0100"


def get_current_branch():
    """Get active branch name or fail if detached."""
    branch = run_git(["rev-parse", "--abbrev-ref", "HEAD"])
    if branch == "HEAD":
        raise RuntimeError("Currently in detached HEAD state. Please checkout a branch first.")
    return branch


def resolve_commit_range(commit_range, count):
    """Resolve linear commit list from oldest to newest."""
    if count is not None:
        rev_arg = f"HEAD~{count}..HEAD"
    elif commit_range:
        rev_arg = commit_range
    else:
        # Default to origin/<branch>..HEAD if available
        branch = get_current_branch()
        try:
            upstream = run_git(["rev-parse", "--abbrev-ref", f"{branch}@{{upstream}}"])
            rev_arg = f"{upstream}..HEAD"
        except Exception:
            # Fallback to all commits on current branch
            rev_arg = "HEAD"

    commits = run_git(["rev-list", "--reverse", rev_arg]).splitlines()
    commits = [c.strip() for c in commits if c.strip()]
    if not commits:
        raise RuntimeError(f"No commits found for range: {rev_arg}")
    return commits, rev_arg


def generate_timestamps(commits, target_dates, tz_str, rng_seed=42):
    """
    Distribute commits monotonically across target_dates.
    Uses realistic morning and afternoon working blocks with natural jitter.
    """
    rng = random.Random(rng_seed)
    num_commits = len(commits)
    num_days = len(target_dates)

    # Distribute commit counts across days as evenly as possible
    base_per_day = num_commits // num_days
    rem = num_commits % num_days
    day_counts = [base_per_day + (1 if i < rem else 0) for i in range(num_days)]

    timestamps = []
    c_idx = 0

    for day, count in zip(target_dates, day_counts):
        if count == 0:
            continue

        # Single commit on this day: place between 14:00 and 16:00
        if count == 1:
            hour = rng.randint(14, 16)
            minute = rng.randint(10, 50)
            second = rng.randint(10, 55)
            dt_str = f"{day.strftime('%Y-%m-%d')} {hour:02d}:{minute:02d}:{second:02d} {tz_str}"
            timestamps.append(dt_str)
            c_idx += 1
            continue

        # Split day into morning session (09:30-12:30) and afternoon session (14:00-17:50)
        morning_count = count // 2
        afternoon_count = count - morning_count

        day_times = []

        # Morning slots
        if morning_count > 0:
            start_m = 9 * 60 + 30 + rng.randint(0, 15)  # ~09:30-09:45
            end_m = 12 * 60 + 15                        # ~12:15
            span = max(1, end_m - start_m)
            step = span / morning_count
            for i in range(morning_count):
                m_val = int(start_m + i * step + rng.randint(0, max(1, int(step * 0.4))))
                h = m_val // 60
                m = m_val % 60
                s = rng.randint(10, 55)
                day_times.append((h, m, s))

        # Afternoon slots
        if afternoon_count > 0:
            start_a = 14 * 60 + rng.randint(0, 20)      # ~14:00-14:20
            end_a = 17 * 60 + 45                        # ~17:45
            span = max(1, end_a - start_a)
            step = span / afternoon_count
            for i in range(afternoon_count):
                m_val = int(start_a + i * step + rng.randint(0, max(1, int(step * 0.4))))
                h = m_val // 60
                m = m_val % 60
                s = rng.randint(10, 55)
                day_times.append((h, m, s))

        # Ensure strict monotonicity within the day
        day_times.sort()
        for i in range(1, len(day_times)):
            prev_sec = day_times[i - 1][0] * 3600 + day_times[i - 1][1] * 60 + day_times[i - 1][2]
            curr_sec = day_times[i][0] * 3600 + day_times[i][1] * 60 + day_times[i][2]
            if curr_sec <= prev_sec:
                new_sec = prev_sec + rng.randint(15 * 60, 35 * 60)
                h = (new_sec // 3600) % 24
                m = (new_sec % 3600) // 60
                s = new_sec % 60
                day_times[i] = (h, m, s)

        for h, m, s in day_times:
            dt_str = f"{day.strftime('%Y-%m-%d')} {h:02d}:{m:02d}:{s:02d} {tz_str}"
            timestamps.append(dt_str)
            c_idx += 1

    return timestamps


def print_schedule(commits, timestamps, dry_run=False):
    """Format and print the commit schedule table."""
    header = "[Dry Run] Proposed Schedule:" if dry_run else "Applying Commit Redate:"
    print(f"\n{header} ({len(commits)} commits)")
    print("-" * 90)
    print(f"{'New Timestamp':<28} | {'Orig Hash':<9} | Subject")
    print("-" * 90)
    for c, ts in zip(commits, timestamps):
        subj = run_git(["log", "-1", "--format=%s", c])
        if len(subj) > 48:
            subj = subj[:45] + "..."
        print(f"{ts:<28} | {c[:7]:<9} | {subj}")
    print("-" * 90)


def create_backup_branch(tag=None):
    """Create a backup branch pointing to HEAD."""
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    branch_name = f"backup-before-redate-{tag}" if tag else f"backup-before-redate-{ts}"
    run_git(["branch", "-f", branch_name, "HEAD"])
    run_git(["branch", "-f", "backup-before-redate", "HEAD"])
    return branch_name


def rewrite_commits(commits, timestamps):
    """Rewrite commit objects using git commit-tree and update current branch."""
    # Find parent of the first commit in the chain
    first_commit = commits[0]
    parents = run_git(["rev-list", "--parents", "-1", first_commit]).split()[1:]
    if len(parents) > 1:
        raise RuntimeError(f"First commit {first_commit[:7]} is a merge commit; linear range required.")
    base_parent = parents[0] if parents else None

    current_parent = base_parent
    old_head = run_git(["rev-parse", "HEAD"])
    old_tree = run_git(["rev-parse", f"{old_head}^{{tree}}"])

    new_commits = []

    for c, ts in zip(commits, timestamps):
        tree = run_git(["rev-parse", f"{c}^{{tree}}"])
        msg = run_git(["log", "-1", "--format=%B", c])
        an = run_git(["log", "-1", "--format=%an", c])
        ae = run_git(["log", "-1", "--format=%ae", c])
        cn = run_git(["log", "-1", "--format=%cn", c])
        ce = run_git(["log", "-1", "--format=%ce", c])

        env = os.environ.copy()
        env["GIT_AUTHOR_NAME"] = an
        env["GIT_AUTHOR_EMAIL"] = ae
        env["GIT_AUTHOR_DATE"] = ts
        env["GIT_COMMITTER_NAME"] = cn
        env["GIT_COMMITTER_EMAIL"] = ce
        env["GIT_COMMITTER_DATE"] = ts

        cmd = ["commit-tree", tree]
        if current_parent:
            cmd.extend(["-p", current_parent])

        proc = subprocess.Popen(
            ["git"] + cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
        new_c, err = proc.communicate(input=msg)
        if proc.returncode != 0:
            raise RuntimeError(f"git commit-tree failed on {c[:7]}: {err.strip()}")

        new_c = new_c.strip()
        new_commits.append(new_c)
        current_parent = new_c

    new_head = current_parent
    new_tree = run_git(["rev-parse", f"{new_head}^{{tree}}"])

    # Strict Zero-Diff Assertion
    if old_tree != new_tree:
        raise RuntimeError(f"Integrity check failed: tree mismatch ({old_tree} != {new_tree})")

    diff = run_git(["diff", old_head, new_head])
    if diff:
        raise RuntimeError(f"Integrity check failed: non-empty diff between old HEAD and new HEAD:\n{diff}")

    # Update current branch ref
    branch = get_current_branch()
    run_git(["update-ref", f"refs/heads/{branch}", new_head])
    return new_head, branch


def main():
    parser = argparse.ArgumentParser(
        description="Rewrite author and committer dates for Git commits safely and deterministically.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  # Redate a range across multiple days
  %(prog)s --range origin/master..HEAD --from 2026-09-07 --to 2026-09-15

  # Redate the last 5 commits to a single date
  %(prog)s -n 5 --date 2026-09-20

  # Preview schedule without modifying commits
  %(prog)s --range origin/master..HEAD --from sep07 --to sep15 --dry-run

  # Redate across weekdays only (skipping weekends)
  %(prog)s --from 2026-09-07 --to 2026-09-18 --weekdays-only
""",
    )

    scope_group = parser.add_argument_group("Commit Scope")
    scope_group.add_argument("-r", "--range", help="Git revision range (e.g. origin/master..HEAD, HEAD~10..HEAD)")
    scope_group.add_argument("-n", "--count", type=int, help="Number of recent commits to redate")

    date_group = parser.add_argument_group("Target Date(s)")
    date_group.add_argument("-d", "--date", help="Single target date (e.g. 2026-09-20, sep20)")
    date_group.add_argument("--from", "--start", dest="start_date", help="Start date for multi-day range")
    date_group.add_argument("--to", "--end", dest="end_date", help="End date for multi-day range")
    date_group.add_argument("--weekdays-only", action="store_true", help="Skip Saturdays and Sundays in range")

    options_group = parser.add_argument_group("Options")
    options_group.add_argument("--tz", help="Timezone offset (default: auto-detected, e.g. +0100)")
    options_group.add_argument("--dry-run", action="store_true", help="Print schedule preview without modifying Git ref")
    options_group.add_argument("--no-backup", action="store_true", help="Skip creating a backup branch")
    options_group.add_argument("--backup-tag", help="Custom suffix for backup branch (e.g. sep07-sep15)")

    args = parser.parse_args()

    # Resolve timezone
    tz_str = args.tz or detect_repo_timezone()

    # Resolve target dates
    if args.date:
        d = parse_date(args.date)
        target_dates = [d]
    elif args.start_date and args.end_date:
        d_start = parse_date(args.start_date)
        d_end = parse_date(args.end_date)
        if d_start > d_end:
            raise ValueError(f"Start date ({d_start}) cannot be after end date ({d_end}).")
        num_days = (d_end - d_start).days + 1
        all_dates = [d_start + datetime.timedelta(days=i) for i in range(num_days)]
        if args.weekdays_only:
            target_dates = [d for d in all_dates if d.weekday() < 5]
            if not target_dates:
                raise ValueError("No weekdays found in the specified range.")
        else:
            target_dates = all_dates
    else:
        parser.error("Please specify either --date <DATE> or both --from <START> and --to <END>.")

    # Resolve commits
    commits, rev_arg = resolve_commit_range(args.range, args.count)

    # Generate timestamps
    timestamps = generate_timestamps(commits, target_dates, tz_str)

    # Print schedule / preview
    print_schedule(commits, timestamps, dry_run=args.dry_run)

    if args.dry_run:
        print("[Dry Run] No Git references were updated. Exiting safely.")
        return

    # Create backup branch
    if not args.no_backup:
        backup_tag = args.backup_tag
        if not backup_tag and args.start_date and args.end_date:
            backup_tag = f"{args.start_date}-{args.end_date}".replace(" ", "")
        backup_name = create_backup_branch(backup_tag)
        print(f"Created backup branch: '{backup_name}' (and 'backup-before-redate')")

    # Execute rewrite
    new_head, branch = rewrite_commits(commits, timestamps)

    print(f"\n[Success] Branch '{branch}' successfully rewritten to {new_head[:7]}!")
    print(f"Verified: 0 diff against original tree. All {len(commits)} commits preserved.")
    print(f"\nTo push your rewritten commits to remote:")
    print(f"  git push --force origin {branch}\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
