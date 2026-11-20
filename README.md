# Muster-lite

Muster-lite is an offline, deterministic records checker. An
Auditor runs it at a step gate to verify one stage staffing claim
of one build against the pinned flow staffing rules and the
records supplied for that stage, before the gate rules on that
claim.

One run checks one stage. The tool reads only the records named
for that run, and no other file. It counts the seats the roster
record names, checks the roster and the claims in the named claim
bearing files against the pinned counting tables shipped with the
tool, and prints one computed result in three reading forms: a
Simple form, an Advanced form, and an Agentic form that carries
the same result as structured data. Every result that is not PASS
cites its evidence file and seat, and the report states the
supplied set and its coverage, the subtraction behind every count,
and the seats that are missing or held twice.

The tool proves nothing about the world outside the records. A
passing result means the records supplied support the claim under
the rules they name. It does not prove that any agent was actually
spawned, that any work was done independently, or that the records
supplied are complete. The gate, not the tool, rules on closure.

## The shipped unit

The shipped tool is the package at `muster_restart/`:

- `muster_restart/kernel.py`: the kernel module. It reads the
  supplied set, verifies the pinned tables, counts, runs every
  check, and produces the one computed result.
- `muster_restart/presentation.py`: the presentation module. It
  renders the one computed result in the three reading forms and
  compares the forms against the result before any form prints.
- `muster_restart/run_entry.py`: the run entry, the single entry
  point of the unit. It receives one invocation, calls the kernel,
  hands the result to the presentation module, and returns the
  outcome.
- `muster_restart/__init__.py`: the package file. It is placed as
  package machinery when the tool is installed.
- `muster_restart/layer1.json`, `muster_restart/layer2.json` and
  `muster_restart/mapping.json`: the pinned counting tables,
  shipped as inspectable data in three parts kept apart: team base
  sizes by tier, per step unit counts, and unit to team form
  mapping rows.

Python 3.11 or later is required. The tool uses only the Python
standard library, works offline, and writes nothing to the records
it checks.

## Installing it

No installer program ships with the tool. Installation is the
placement of the shipped contents, unchanged, in one directory
the operator names, by ordinary file copying. Copy the shipped
contents into that directory, keeping the layout as shipped, and
run the tool from there.

Python 3.11 or later is required, and it must be in place before
the first run. The tool uses only the Python standard library, so
nothing else needs to be installed for it to run.

To uninstall the tool, delete the installed directory. The tool
keeps no state outside that directory.

## Quick start

The worked example below runs the shipped product over the
shipped staffed roster fixture of family F1. The fixture stands
at `tests_restart/fixtures/F1/shipped_staffed_roster.json`. Run
this snippet from the root of the installed or shipped tree, with
the tree on the Python path:

```python
import json
from pathlib import Path

from muster_restart.kernel import compute_result

fixture = json.loads(Path("tests_restart/fixtures/F1/shipped_staffed_roster.json").read_text(encoding="utf-8"))
result = compute_result({"roster_fixture": fixture["roster"]})
print(result["fields"]["12"])
```

Expected rollup: UNVERIFIABLE

For this fixture, UNVERIFIABLE means the run could not verify the
claim from the input given in this form, because the roster
record a full run reads was not supplied in that form, so no
verified staffing conclusion stands for this fixture from this
call.

## Running it

One invocation judges one stage, under the command name
muster-lite:

```sh
PYTHONPATH=repo python3 -m muster_restart.run_entry \
    --runner-identity "A. Auditor" \
    --runner-capacity Auditor \
    --build muster-lite \
    --stage "Step 13" \
    --tier Low \
    --supplied-file records/step-13-roster.md:"stage records" \
    --supplied-file records/step-13-roster.md:"claim bearing files" \
    --supplied-file records/step-13-record.md:"stage records" \
    --supplied-file records/step-13-record.md:"claim bearing files" \
    --supplied-file records/TIER-RECORD.md:"stage records" \
    --supplied-file records/step-13-gate-record.md:"claim bearing files"
```

The arguments state exactly the run input fields, and nothing
else:

- `--runner-identity`: the name of the agent running the check.
- `--runner-capacity`: the capacity that agent runs in, one of
  `Auditor`, `coordinator as precheck`, or `board member other
  than the stage coordinator`. A coordinator runs the tool only
  as a labelled precheck, with `--run-kind precheck`, and a
  precheck is not a gate verdict.
- `--build`: the build the stage belongs to.
- `--stage`: the one stage judged, as the records name it.
- `--tier`: the tier the target tier record states.
- `--pinned-base`: the pinned base reference the target records
  state, where one is identified. Omit it where none is.
- `--run-kind`: `precheck` for a coordinator precheck. A gate run
  states no run kind.
- `--supplied-file`: one named record per use, in the form
  `path:group`, where the group is the input group the record
  belongs to, such as `stage records` or `claim bearing files`.
  A file that stands in two groups is named once per group. The
  run reads the content of the records named, including the roster
  record, whose seats the counts rest on. A supplied file entry
  carrying no input group cannot start a run.

An invocation carrying a name or a positional argument outside
this list cannot start: the tool refuses it and names the cause,
and no part of such an invocation is silently dropped.

The outcome prints as one JSON document carrying the outcome
kind, the result record where one stands, the three printed
forms, any defect reports, any cannot start outcome, and the exit
code.

## Outcome kinds and exit codes

Every invocation ends in exactly one of five outcome kinds:

1. Completed gate run: the run produced a result record and its
   forms print. The rollup is one of PASS, FAIL, NOT PROVEN or
   UNVERIFIABLE, and only a PASS rollup may be cited as staffing
   evidence for a clean closure.
2. Open case run: the run met an open case and produced a result
   record carrying the open case state, with no rollup word. The
   stage stands unclassified on the affected checks.
3. Precheck run under the listed not run condition: a coordinator
   precheck produced a result record with its label and
   consequence line attached and no rollup word.
4. Form agreement disagreement: the run completed and a result
   record stands, but the printed forms disagreed with it, so
   defect reports print in place of the forms. A disagreement is
   a defect in the tool, not a finding about the stage.
5. Cannot start run: the invocation was malformed, or the tool
   failed before a result record stood. No result record, no
   verdict and no rollup stand for such a call, and the calling
   side records it as a call that did not run.

Exit codes:

- 0: the run produced a result record (outcome kinds 1 to 4).
- 1: cannot start, kind invocation. The invocation does not state
  a run input in the required form, for example a runner capacity
  outside the stated values, a supplied file entry carrying no
  input group, or a name or positional the call shape does not
  state.
- 2: cannot start, kind tool failure. The tool itself failed
  before a result record stood.

No exit code stands for a verdict: a code never classifies a
stage.

## Potential problem causers

- A run reads only the records named for it. Records that are not supplied are not checked, and a result says nothing about records that were not supplied.
- The pinned counting tables cover Step 13, the Low tier and the Design team only. A stage, tier or team form beyond those rows gets no team count from the tables, and its first check ends UNVERIFIABLE for want of a table row.
- A passing result means the supplied records support the claim under the pinned rules. It does not prove that any agent was actually spawned, that work was done independently, or that the records are complete.
- The install places 66 files, while the release contents list names 65 of them. The package file `muster_restart/__init__.py` is placed as package machinery and stands outside the contents list that the release contents sweep walks.
- Interpreter artefact files, for example under `__pycache__` directories, can appear in a tree the product has run in. They are artefacts of a run, not product files.
- One specimen check form named in early planning was withdrawn before release, because the specimen records it needed do not exist. No check stands for that specimen form.
- No exit code stands for a verdict. A code never classifies a stage.

## License

Copyright 2026 J.P. Picard aka Macro-Harder. Licensed under the Apache License, Version 2.0; see the LICENSE file in this repo.
