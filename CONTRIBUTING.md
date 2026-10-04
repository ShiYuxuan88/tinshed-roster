# Contributing

This repository is a small teaching project. The conventions below keep the
history readable and the change log accurate.

## Branches

Work is never committed directly to `main`. Create a topic branch from an
up-to-date `main` and propose the change through a pull request.

    <type>/<short-description>

| Type | Use |
| --- | --- |
| `feature/` | A capability or a substantive change |
| `fix/` | A correction to existing behaviour |
| `docs/` | Documentation only |
| `test/` | Test-only change |
| `chore/` | Tooling, dependencies, CI configuration |

Example: `test/assignment-rule-coverage`

## Commits

Messages follow the Conventional Commits specification.

    <type>: <description>

The description is written in the imperative mood and in lower case: `add`,
`verify`, `record` — not `added`, `verifies`, `recording`. The message says what
applying the commit does.

Examples from this repository:

    feat: add theatre crew roster workflows
    test: verify roster rules and document deployment
    docs: define A2 scope and execution plan
    chore: keep local submission artifacts out of git

A commit describes one coherent change. If a working session has produced
unrelated edits, stage them separately rather than bundling them into one
commit, so that the change can be reviewed and, if necessary, reverted on its
own.

## Pull requests

Every change reaches `main` through a pull request. A reviewer is asked to
confirm that:

- the change does what its description says, and nothing else;
- the acceptance criteria for the change have been demonstrated;
- a test exists for the behaviour, including the rule that a volunteer may hold
  at most one role in any single performance, where the change touches
  assignment logic;
- configuration values are read from the environment rather than hard-coded;
- the application still runs from a clean checkout by following the README.

Pull requests are merged with merge commits, so that the branch structure
remains visible in the history after merging.

## Configuration

Never commit a `.env` file, a database file or a credential. Configuration keys
are documented in `.env.example` with placeholder values only. If a secret is
committed by accident, rotate it — do not simply delete the commit, because the
value remains recoverable in the reflog and in any clone taken in the meantime.

## Change log

`CHANGELOG.md` is updated as part of closing a release, not retrospectively.
Entries are grouped under `Added`, `Changed`, `Fixed`, `Removed` and, where
relevant, `Security` or `Known limitations`.
