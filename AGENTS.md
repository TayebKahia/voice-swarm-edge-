# AGENTS.md

## Agent skills

### Issue tracker

Issues and specs live as markdown files under `.scratch/<feature-slug>/` in this repo. See `docs/agents/issue-tracker.md`.

### Triage labels

The five canonical triage roles, unchanged: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `CONTEXT.md` and `docs/adr/` at the repo root, both created lazily. See `docs/agents/domain.md`.

## Commits

**One commit per coherent change, not per edit.** While iterating on a single problem ---
a debugging loop, a fix that needs three attempts --- amend rather than stacking commits.
Intermediate states that were never deployed and never depended on are not history worth
keeping, and a reader who finds six `fix(x):` entries on one file has to reconstruct the
story that one commit could have told.

Separate commits when the *subsystem* differs, not when the edit does: an `eval/` change and
a `.scratch/sprint-pfe/STATE.md` update are two commits; three attempts at the same notebook
are one.

**Why the messages are long here.** `prd.md`, `docs/project/`, `IMPLEMENTATION_ROADMAP.md`
and `START_SESSION.md` are deliberately untracked (roadmap §0.4a), so `git log` together with
`STATE.md` and `docs/adr/` is the *only* durable record of why something was done. A diagnosis
that lives only in a chat session is lost at the next context reset. Record the reasoning that
is not visible in the diff --- what failed, what was ruled out, and why this fix rather than the
obvious one. Do not pad messages with what the diff already says.

Roadmap §1.3 asks for a commit at each session exit with the session number and gate status.
That is a floor, not a licence to commit after every file write.
