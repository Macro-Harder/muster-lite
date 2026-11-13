# Muster-lite

Muster-lite is a grade L2 records checker. It is not the DQ-012
isolated checker, and grade L3 is not available for labelling any
record from this tool.

Muster-lite checks the records of one stage of a build against the
staffing rules those records name: whether the teams a stage calls
for stand staffed by distinct agents, whether the review board
meets its minimum, whether work products link back to the seats
that claim them, and whether the freshness exclusions a stage
claims actually hold on the records supplied. It reads only the
files it is given, in the order it is given them, and it prints one
result in three forms: a Simple form, an Advanced form, and an
Agentic form that carries the same result as JSON.

The tool proves nothing about the world outside the records. A
passing result means the records supplied are consistent with the
rules they name. It does not prove that any agent was actually
spawned, that any work was done independently, or that the records
supplied are complete.

## Running it

Python 3.11 or later is required. The tool uses only the Python
standard library, works offline, and writes nothing to the records
it checks.

```sh
python3 muster_lite.py --stage "Step 4" --runner "A. Auditor" \
    --capacity Auditor roster.md step-record.md
```

Positional arguments name the supplied records, in order. The
options are:

- `--stage`: the stage to judge, as the records name it.
- `--runner`: the name of the agent running the check.
- `--capacity`: the capacity that agent runs in. A coordinator
  running in a coordinator capacity produces a precheck, which no
  gate may cite as an independent verdict.
- `--context`: a context file for the freshness checks. May be
  given more than once.
- `--base-record`: a base record identifying the pinned base. May
  be given more than once.
- `--kind`: `gate run` or `precheck`. Only this option selects the
  run kind.

Two data files stand beside the entry file and are read on every
run: `counting-table.json`, the counting table the counts are
judged against, and `diagnostic-catalogue.json`, the catalogue of
diagnostic codes a result can carry. The counting table this
release ships stands at PARTIAL: it is the table as far as swept,
not a complete sweep, and no result in any form presents it as
complete.

## Exit codes

- 0: PASS. The stage may be claimed as staffed on this run.
- 1: FAIL. The records prove a shortfall.
- 2: NOT PROVEN. Records were read but do not settle the claim.
- 3: UNVERIFIABLE. A record the run needs is absent or cannot
  settle the check.
- 4: the run cannot start, because none of its named inputs can
  be read.
- 5: USAGE ERROR. The invocation itself is malformed.
- 6: TOOL FAULT. The tool failed in a run that had started.

## Potential problem causers

Most non passing results trace back to a short list of record
problems. These are the ones that cause trouble most often:

- **No roster artifact in the set.** If the records supplied do
  not include the roster for the stage, nothing about staffing can
  be verified, and the run returns UNVERIFIABLE.
- **Fragment or placeholder identifiers.** A seat whose holder is
  recorded as a shortened id, a blank, or a placeholder does not
  count toward any minimum. Only a complete identifier, standing
  whole as issued, counts.
- **One agent holding two seats.** Where the same full identifier
  stands on two seat entries, the duplicate is removed from the
  count, and where that makes a minimum appear met when it is not,
  the result is FAIL at Critical severity.
- **A missing board chair statement.** A board seat list alone
  does not state the chair. Where a run rests on the roster alone,
  the board check needs a record that states the board chair
  identifier itself.
- **Torn or truncated passages.** A roster passage that is torn
  or cut off cannot settle the seats it names. The affected checks
  stand at NOT PROVEN or UNVERIFIABLE, and the truncation is named
  in the report.
- **Work products in unsettled forms.** A seat that presents a
  work product whose form contract is not settled by any supplied
  record stands indeterminate, and its team cannot pass on linkage
  until the contract is settled.
- **Freshness claims without facts.** A stage that claims a
  freshness family held, but supplies none of the facts the family
  turns on, takes NOT PROVEN for that family, and the missing fact
  is named.
- **Records that disagree with each other.** Two records stating
  different seat totals, or a claim the computed counts contradict,
  are printed side by side as a claim disagreement or a
  completeness difference. The tool corrects nothing; the records
  named are the ones that must change.

## Tests

The product test suite runs with one command, from the repo root:

```sh
python3 -m unittest discover -s tests -t . -v
```

## License

Copyright 2026 J.P. Picard aka Macro-Harder. Licensed under the
Apache License, Version 2.0; see the LICENSE file in this repo.
