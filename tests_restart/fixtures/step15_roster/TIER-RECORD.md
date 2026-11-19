# Tier record: muster-lite build, restart run

Product: muster-lite, the staffing verifier core. A small offline command
line tool, Python standard library only, deterministic. It reads a build's
step records and rosters and checks them mechanically against the staffing
rules of the build flow.

## Decision

Tier: Low. Tier Low stands for the restart run.

## Ground 1: Captain JP's restart order

Captain JP ordered this build restarted on 2026-11-13, as one of the Low
and Medium builds that restart under her new team size ladder. The order
restarts this build as the Low build it was. The restart is staffed at her
Low ladder, the ladder of 2026-11-13 as the flow documents now state it.
Staffing follows the Low counts in LEVEL-2 and the Low team sizes in the
flow, with a review board of 3 distinct members at every step and the
Auditor approval gate after every step.

## Ground 2: the R-4 size test basis is unchanged in substance

The prior run's tier record, at design/TIER-RECORD.md, was read as data.
Its R-4 size test basis is unchanged in substance for this run:

- Handles money: NO. The tool moves no money and reads no financial data.
- Security surface: NO. The tool is offline, holds no credentials, opens
  no network connection, and reads only local files its operator names.
  It stores nothing and transmits nothing.
- Public surface: NO. The product is a local command line tool. It runs no
  service, serves no requests, and exposes no interface to any other user.
  The build's public source repo stands under the standing distribution
  rule that applies to every build at every tier. Source publication
  under that rule is not a product surface.
- More than a few modules: NO. The product is a few modules only, a single
  small module set of at most 3 modules forming one deployable unit: one
  command.
- Low conditions: private (YES, a private tool for the operator's own
  builds, run locally, holding no account and no shared state), no money
  surface (YES), no security surface (YES), no public surface (YES), and
  tiny (YES, at most 3 modules forming one deployable unit).

No condition in the test raises the floor to Medium or High, and nothing
in the restart changes any line of that basis. The product, its surfaces,
and its size are the same product, surfaces, and size the prior run's test
was run on.

## Timing of this record

The tier was settled before Step 1 of the restart staffed beyond its
opening wave. This file is the third artefact of that wave, filed after
restart/steps/step-01-opening-record.md and restart/PATH-LEDGER.md, and
before the layouts and before any Installer work. No stage of this run
staffed on an unsettled tier.

## Record home

This file is the tier record of the restart run. Its home is the private
design repo Macro-Harder/muster-lite-design, at restart/TIER-RECORD.md,
inside the restart record home. The prior run's tier record at
design/TIER-RECORD.md stands untouched as data.
