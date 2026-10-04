# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-09-26

### Added

- Volunteer records can be created, edited and deactivated, holding a name and
  contact details.
- Productions can be created and edited, and hold the performances that make up
  the season.
- Performances record a date, a start time and a venue, and belong to one
  production.
- Crew assignments link a volunteer to a role for a specific performance.
- A performance roster shows filled and open positions, and the number of
  positions filled.
- A personal roster view lets a volunteer see their own assignments, with an
  explicit empty state.
- A `seed-demo` command writes fictional sample data into an empty database.

### Changed

- A volunteer may hold at most one role in any single performance. A second
  assignment for the same volunteer in the same performance is refused with an
  explanation rather than accepted.
- A role may be filled only once in a single performance.
- A volunteer with existing assignments cannot be deactivated until those
  assignments have been removed.

### Security

- Form submissions require a CSRF token; a submission without one is rejected.
- The application refuses to start in production while `SECRET_KEY` is still the
  development placeholder value.
- Secrets, database files and local working directories are excluded from
  version control.

### Known limitations

- No authentication, no role-based access control, no transport security and no
  backup.
- Demonstration data only. The application must not be used to hold real
  volunteer contact details.

[Unreleased]: https://github.com/ShiYuxuan88/tinshed-roster/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/ShiYuxuan88/tinshed-roster/releases/tag/v0.1.0
