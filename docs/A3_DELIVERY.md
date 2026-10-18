# A3 delivery guide

Canonical repository: <https://github.com/ShiYuxuan88/tinshed-roster>.

This candidate combines the existing application with the team's contributions.
It is not formal lecturer acceptance or evidence that historical Scrum events occurred.

## Contribution provenance

| Source | Included work |
| --- | --- |
| A2 tag `v0.1.0` | Original Flask/SQLite roster prototype |
| Jin, [PR #5](https://github.com/ShiYuxuan88/tinshed-roster/pull/5), `d544650` | Confirmation toggle and its regression test; already merged in canonical main `dd6c399` |
| Lu, [PR #4](https://github.com/ShiYuxuan88/tinshed-roster/pull/4), `c343d78` | Four rule tests, contribution conventions and detailed changelog; original commits retained through a merge on the delivery branch |
| Local CI source `d385560` | Container build, health and mounted-database persistence gate restored during integration |
| A3 integration | Resolve changelog conflict preserving both contributions; strengthen database assertions; fix stale confirmation on reassignment; add acceptance regressions and constrain test discovery |

Integration assistance and automated checks do not establish independent human
review. Each member should describe their actual contribution and any assistance
used in the assessment report under the course's current policy.

## Candidate and release procedure

Proposed candidate identifier: `v0.2.0-rc.1`. The minor version reflects the
confirmation capability added since `v0.1.0`. This text does not create a Git tag
or publish a release. The exact candidate is the delivery branch commit recorded
in its PR and CI run.

1. Inspect the integration diff and provenance; a team member records actual review.
2. Require both `test` and `container-smoke` Actions jobs to pass for the current PR head.
3. Follow the clean setup and demo checks below and record actual results.
4. Resolve review feedback, rerun affected checks and merge through a PR using a merge commit.
5. Tag the reviewed, validated merged commit with an available version identifier;
   release notes identify the SHA, CI run, changes, setup, limitations and rollback.
6. Record this same repository, SHA and tag in the assessment handover and test workbook.

Do not describe an open PR or candidate as a released main. Do not reuse a test
result from an earlier commit as proof of a changed candidate.

## Clean installation and local demonstration

Use Python 3.12+ and follow the README's virtual-environment commands.
Install `requirements-dev.txt`, then run `python -m pytest -q` from repository root.
The formal suite is in `tests/`; ignored temporary files are excluded by `pytest.ini`.
The Flask test client checks route/database behavior, not browser rendering.

PowerShell example after virtual-environment setup:

```powershell
$env:APP_ENV = 'development'
$env:APP_DATABASE = Join-Path $PWD 'instance/a3-demo.sqlite3'
$env:SECRET_KEY = 'replace-with-a-local-random-session-key'
.\.venv\Scripts\python.exe -m flask --app app seed-demo
.\.venv\Scripts\waitress-serve.exe --listen=127.0.0.1:8000 app:app
```

Open <http://127.0.0.1:8000>. Seed only a new demo database; the seed command
refuses a database already containing productions. Use a separate fresh database
path for another demo; do not delete a real database to reset the demonstration.

For production-style startup set `APP_ENV=production` and a locally generated
session key. No public hosting is required for this demonstration.

## Acceptance checks

| Area | Automated evidence in this candidate | Browser/demo check to record separately |
| --- | --- | --- |
| US01 core records | Original workflow fixture and route/database tests | Create and edit volunteer, production and performance; check validation and displayed data |
| US02 duplicate prevention | Lu's independent volunteer/role conflicts; database unchanged assertions | Attempt each conflict separately and observe refusal |
| US03 reassignment boundaries | Cross-performance allowance; removal frees the volunteer and the original role | Assign after removal and compare roster |
| US04 edits/personal roster | Original edit/delete workflow; conflicting edit preserves both rows | Change assignment, inspect both volunteers' personal rosters and empty state |
| US05 persistence | New application instance reads the same confirmed assignment; CI recreates a container with the same database mount | Stop/start the demonstration and check the same records |
| US06 repeatable handover | Formal test discovery and CI build/start gate | Follow this guide from a clean checkout; capture actual operator/date/version and limitations |
| Confirmation | Toggle, missing-CSRF rejection, reset on role/person change, unchanged-save preservation | Confirm, change role/person, verify Pending, confirm and clear again |

The automated checks are focused examples, not exhaustive coverage of every AC.
Record each manual check as Pass/Fail/Not Run with date, exact SHA, environment,
steps, expected/actual result, evidence and actual reviewer. Use genuine defect
and retest records; do not manufacture a failure history.

## Limitations and rollback

- No login or role permissions. Confirmation is a coordinator-maintained flag,
  not authenticated consent or a notification to a volunteer.
- No volunteer availability or overlapping-performance time-conflict checks.
- No cloud deployment, HTTPS setup, backup/restore workflow or production readiness claim.
- Fictional data only; keep the demonstration bound to localhost.
- Recreating an application/container with the same database is persistence
  verification, not backup restoration.

The candidate introduces no schema changes. If rollback is required, stop the
demo, retain its SQLite file and environment configuration, and check out a
previous known validated commit in a separate checkout. Test it against a copy
of the database before reuse. Existing confirmation flags are data, and are not
rewritten by checking out another commit. Do not force-push shared main or move
an existing published tag to simulate rollback.
