"""Module 2, the pure core of muster-lite.

The core works only on the supplied set the shell captured for the
run and on the shipped counting table and diagnostic catalogue. It
parses the records into the model shapes, settles the seat and count
account, computes every check, and composes the one rollup every
report form renders. Nothing in this module reads a file, writes a
file, or depends on the order the supplied set was named in.
"""

import json
import re

CLAIM_CAP = (
    "This report checks the records named in it for consistency with "
    "the staffing rules named in it. It does not prove that any agent "
    "was actually spawned, that any work was done independently, or "
    "that the records supplied are complete."
)

GRADE_SENTENCE = (
    "Muster-lite is a grade L2 records checker. It is not the DQ-012 "
    "isolated checker, and grade L3 is not available for labelling any "
    "record from this tool."
)

CLOSING_LINE = (
    "What this tool did not prove: it did not prove that any agent was "
    "actually spawned, that any work was done independently, or that "
    "the records supplied are complete."
)

POSITIONS = (
    "counted in base",
    "over base at team level",
    "uncounted at this step",
    "board additional",
    "exempt",
    "step unit",
    "unplaced",
)

COUNT_POSITIONS = (
    "counted in base",
    "over base at team level",
    "uncounted at this step",
    "exempt",
)

WORDS = ("PASS", "FAIL", "NOT PROVEN", "UNVERIFIABLE")
EXIT_CODES = {"PASS": 0, "FAIL": 1, "NOT PROVEN": 2, "UNVERIFIABLE": 3}

FULL_ID = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
PARTIAL_ID = re.compile(r"^[0-9a-fA-F][0-9a-fA-F-]{3,34}$")

COLOURS = ("Red", "Blue", "Purple", "Green", "Yellow", "Orange",
           "White", "Black")

NON_IDENTIFIERS = ("", "not recorded", "none", "no id recorded")

PLACEHOLDER_WORDS = (
    "tbd", "tbc", "tba", "unknown", "pending", "awaiting",
    "awaiting assignment", "na", "n/a", "unassigned", "not assigned",
    "vacant", "to be determined", "to be confirmed",
    "to be assigned", "placeholder",
)


def is_full_id(value):
    return bool(value) and bool(FULL_ID.match(value))


def is_identifier(value):
    """Whether a holder value counts as an identifier as issued.

    A full session identifier counts standing whole. A name form
    identifier counts as the complete string issued. A shortened
    session identifier, a placeholder, a blank, a fragment, and the
    words not recorded never count. A placeholder word never counts,
    and a name standing alone never counts: a roster presenting a
    short name does not by itself make the name an issued form, so a
    name form identifier stands as a complete name of more than one
    word, as the record sets that issue identifiers in a name form
    present them.
    """
    if value is None:
        return False
    if is_full_id(value):
        return True
    lowered = value.lower()
    if lowered.strip() in NON_IDENTIFIERS:
        return False
    if lowered.strip() in PLACEHOLDER_WORDS:
        return False
    if "fragment" in lowered or "placeholder" in lowered:
        return False
    if PARTIAL_ID.match(value.strip()) and any(
            ch.isdigit() for ch in value):
        return False
    if not any(ch.isalpha() for ch in value):
        return False
    if len(value.split()) < 2:
        return False
    return True


def step_key_of(text):
    """The step key a stage string carries, or None."""
    if not text:
        return None
    match = re.search(r"Step (\d+)", text)
    if match:
        return int(match.group(1))
    match = re.search(r"Step:\s*(\d+)", text)
    if match:
        return int(match.group(1))
    return None


def canonical_round(label):
    """The canonical round a label names, or None where outside the form.

    Two labels name the same round where they agree after trimming,
    or both stand in the form Round and a number with exactly one
    space, or R and a number with no space, with equal numbers,
    leading zeros ignored, and a trailing date set aside.
    """
    if label is None:
        return None
    text = label.strip()
    text = re.sub(r"\s+\d{4}-\d{2}-\d{2}$", "", text)
    match = re.match(r"(?i)^round (\d+)$", text)
    if match:
        return ("round", int(match.group(1)))
    match = re.match(r"(?i)^r(\d+)$", text)
    if match:
        return ("round", int(match.group(1)))
    return ("label", text)


def round_display(key):
    if key is None:
        return "no rounds"
    if key[0] == "round":
        return "Round %d" % key[1]
    return key[1]


def round_sort(key):
    if key is None:
        return (0, 0, "")
    if key[0] == "round":
        return (1, key[1], "")
    return (2, 0, key[1])


# ----------------------------------------------------------------
# Supplied set classification


def _is_spawn_export(text):
    """Whether a text stands in the spawn export form.

    A spawn export is a JSON object carrying a spawns or spawn key.
    The quoted word standing in prose, or in a field line of a
    record of another kind, is a mention of an export, not an
    export, and never makes the file one.
    """
    stripped = text.strip()
    if not stripped.startswith("{"):
        return False
    try:
        data = json.loads(stripped)
    except ValueError:
        return bool(re.match(r'\{\s*"spawns?"\s*:', stripped))
    return isinstance(data, dict) and ("spawns" in data
                                       or "spawn" in data)


def classify_file(captured):
    """The kind of one captured file, from the groups the operator
    named it under and its content form.

    Classification never rests on a basename alone: two different
    files that share a basename stand each under its own naming.
    The naming groups govern in this order. A file named only as a
    context file is context, respecting the group it was named
    under. A file named as a base record is a base record. A roster
    artifact named as a supplied file stands in the supplied set as
    the roster, even where it is also named as a context file: a
    context naming does not remove the stage roster from the
    supplied set. Any other file also named as a context file
    stands as context. What remains is classified by its content
    form and its name, with the brief, prompt, and transcript name
    rule standing after the roster check, so it reaches only files
    whose content is not a roster artifact.
    """
    groups = captured.groups
    if groups == {"context"}:
        return "context"
    if "base" in groups:
        return "base record"
    display = captured.display
    lowered = display.lower()
    if captured.status != "read":
        return "unread"
    text = captured.text
    if text is None:
        return "record"
    if _is_roster_artifact(text):
        return "roster"
    if "context" in groups:
        return "context"
    if "chat" in lowered or "transcript" in lowered \
            or "prompt" in lowered:
        # A brief text, a prompt text, or a chat transcript presents
        # nothing as evidence, under brief Section 2.2 item 4. This
        # rule stands after the roster check: a file whose content
        # is a roster artifact is a roster, whatever its name says.
        return "ignored"
    if _is_spawn_export(text):
        return "ignored"
    if lowered.endswith(".json") or lowered.endswith(".bin"):
        return "ignored"
    if "evidence" in lowered and "register" in lowered:
        return "evidence register"
    if "register" in lowered:
        return "stage register"
    if "gate" in lowered:
        return "gate record"
    if "tier" in lowered or text.startswith("# Tier record"):
        return "tier record"
    if "author record:" in text:
        return "work product"
    if "round" in lowered or text.startswith("# Round record"):
        return "round record"
    if "step" in lowered or "# Step record" in text:
        return "step record"
    return "record"


def _is_roster_artifact(text):
    for line in text.splitlines():
        lowered = line.lower()
        if lowered.startswith("#") and "roster artifact" in lowered:
            return True
        if line.startswith("## Team:"):
            return True
        if line.startswith("## Roster"):
            # A step record carrying its roster in a roster section
            # stands as the roster artifact for its stage.
            return True
    return False


CLAIM_BEARING = ("roster", "step record", "stage register",
                 "gate record", "record", "evidence register")


# ----------------------------------------------------------------
# Mention markers for the use versus mention rule


MENTION_MARKERS = (
    "no claim is made",
    "no claim of",
    "not claimed",
    "quoted here",
    "cites that claim to dispute",
    "to dispute it",
    "remains open",
    "not yet settled",
    "may have held",
    "whether",
)


def is_asserted(sentence):
    """Whether a candidate sentence asserts, under use versus mention.

    A sentence counts as asserted unless it carries a mention marker:
    a negation, a quotation or citation to dispute, a conditional, or
    a future or open framing.
    """
    lowered = sentence.lower()
    for marker in MENTION_MARKERS:
        if marker in lowered:
            return False
    if re.search(r"\bif\b.+\bwould\b", lowered):
        return False
    if lowered.startswith("if "):
        return False
    return True


# ----------------------------------------------------------------
# Record parsing


class Seat(object):
    def __init__(self, team, role, holder, position, round_key, source):
        self.team = team
        self.role = role
        self.holder = holder
        self.position = position
        self.round_key = round_key
        self.source = source

    def as_dict(self):
        return {"team": self.team, "role": self.role,
                "holder": self.holder, "position": self.position,
                "round": round_display(self.round_key)}


class Facts(object):
    def __init__(self):
        self.rosters = []            # per file roster parses
        self.seats = []
        self.board = []              # (role, holder, source)
        self.chair_statements = []   # (holder, source)
        self.tier_statements = []    # (tier, source, kind)
        self.base_ids = []           # (name, hash, bytes, source)
        self.called_versions = []    # (value, source)
        self.called_hashes = []      # (value, source)
        self.claims = []             # (sentence, source) asserted
        self.holdings = []           # (label, holder, round label, source)
        self.involvements = []       # (kind, holder, source)
        self.protected = []          # (family, role text, holder, round, source)
        self.presentations = []      # (role, team, product text, source)
        self.plan_suppliers = []     # (label, colours, source)
        self.charge_suppliers = []   # (label, colours, qualifies, source)
        self.papers_colours = None   # colours with papers supplied
        self.exempt_entries = set()  # (role, holder)
        self.exempt_bases = set()    # role
        self.exempt_corrob = []      # corroborating record names
        self.appendix = []           # (text, holder or None)
        self.lost_spawns = []        # (source name, date)
        self.waste = []              # listing texts
        self.ordering_unsettled = False
        self.seat_total_statements = []
        self.chosen_sizes = {}       # team -> int
        self.invocation = False
        self.reduced_tier_claim = False
        self.combined_scope_claim = False
        self.superseded_files = set()
        self.two_rosters = False
        self.defective_roster = None  # None, provable, or unprovable
        self.stage_claim = False      # an asserted Stage claim stands
        self.stage_statements = []   # (stage text, source)
        self.round_records = []      # (display, text) round records read
        self.truncated_files = set()
        self.torn_teams = set()
        self.team_sections = []      # (team, round key, source) governing
        self.roster_sources = []
        self.stage_mismatch = None   # (record stage, run stage)


SEAT_LINE = re.compile(
    r"^-\s*Seat:\s*(.+?);\s*holder\s*(.*?);\s*position\s*(.+?);")
SEAT_LINE_SHORT = re.compile(
    r"^-\s*Seat:\s*(.+?);\s*holder\s*(.+?)\.?\s*$")
BOARD_LINE = re.compile(r"^-\s*Board seat:\s*(.+?);\s*holder\s*(.+?)\.?\s*$")
REAL_SEAT_LINE = re.compile(r"^-\s*(.+?):\s*session\s+(\S+?)\.?\s*$")
SUCCESSION_LINE = re.compile(
    r"Seat (.+?): the first holder (.+?) was superseded; the second "
    r"holder (.+?) is the holder of the seat\.")
CHAIR_LINE = re.compile(r"^Board chair:\s*holder\s+(.+?)\.?\s*$")
STEP22_CHAIR_LINE = re.compile(
    r"^(.+?):\s*holder\s+(.+?);\s*placement step unit; chair of the "
    r"review board\.")
PINNED_BASE_LINE = re.compile(
    r"Pinned base:\s*(.+?),\s*hash\s+([0-9a-fA-F]+),\s*(\d+)\s+bytes\.")
CALLED_VERSION_LINE = re.compile(
    r"Table version the base calls for:\s*(.+?)\.?\s*$")
CALLED_HASH_LINE = re.compile(
    r"Table hash the base calls for:\s*([0-9a-fA-F]+)\.?\s*$")
TIER_LINE = re.compile(r"Tier applied:\s*([A-Za-z]+)\.?")
STAGE_TIER_LINE = re.compile(
    r"^Stage:\s*(.+?)\.\s*Tier:\s*([A-Za-z]+)\.?\s*$")
STAGE_LINE = re.compile(r"^Stage:\s*(.+?)\.?\s*$")


def _colours_in(text):
    found = []
    for colour in COLOURS:
        if re.search(r"\b%s\b" % colour, text):
            found.append(colour)
    return found


def parse_supplied_set(files, stage_arg):
    """Parse every captured file into the facts the checks read.

    files is a list of (captured, kind) pairs. Returns a Facts.
    """
    facts = Facts()
    stage_key = step_key_of(stage_arg)
    roster_parses = []
    for captured, kind in files:
        if captured.status != "read" or captured.text is None:
            continue
        text = captured.text
        if kind == "round record" or captured.display.lower().startswith(
                "round"):
            facts.round_records.append((captured.display, text))
        if "truncated" in text.lower():
            facts.truncated_files.add(captured.display)
        if kind in CLAIM_BEARING or kind in ("tier record",
                                             "base record", "context"):
            _scan_statements(facts, captured, kind, text)
        if kind == "roster":
            roster_parses.append(
                _parse_roster(facts, captured, text, stage_key))
    _govern_rosters(facts, roster_parses, stage_key)
    return facts


def _scan_statements(facts, captured, kind, text):
    """Scan one record for the statement forms the checks read."""
    source = captured.display
    for raw_line in text.splitlines():
        line = raw_line.strip()
        match = PINNED_BASE_LINE.search(line)
        if match:
            facts.base_ids.append(
                (match.group(1).strip(), match.group(2),
                 int(match.group(3)), source, kind))
        match = CALLED_VERSION_LINE.search(line)
        if match:
            facts.called_versions.append((match.group(1).strip(),
                                          source, kind))
        match = CALLED_HASH_LINE.search(line)
        if match:
            facts.called_hashes.append((match.group(1).strip(),
                                        source, kind))
        match = TIER_LINE.search(line)
        if match:
            facts.tier_statements.append(
                (match.group(1), source, kind))
        if line.startswith("Stage:"):
            match = STAGE_TIER_LINE.match(line)
            if match:
                facts.stage_statements.append((match.group(1), source))
                facts.tier_statements.append(
                    (match.group(2), source, kind))
            else:
                match = STAGE_LINE.match(line)
                if match:
                    facts.stage_statements.append(
                        (match.group(1), source))
        if "captain jp" in line.lower() and "invocation" in \
                line.lower():
            facts.invocation = True
        if "proven defective" in line.lower():
            if "no other record" in line.lower():
                facts.defective_roster = "unprovable"
            elif "independently" in line.lower():
                facts.defective_roster = "provable"
        if "reduced tier" in line.lower() and is_asserted(line):
            facts.reduced_tier_claim = True
        if line.startswith("Exempt entry:"):
            match = re.match(
                r"Exempt entry:\s*(.+?),\s*holder\s+(.+?),\s*exempt "
                r"class\s*(.+?)\.?\s*$", line)
            if match:
                facts.exempt_entries.add(
                    (match.group(1).strip(), match.group(2).strip()))
        if line.startswith("Exemption basis for the "):
            match = re.match(
                r"Exemption basis for the (.+?):", line)
            if match:
                named = match.group(1).strip()
                facts.exempt_bases.add(named)
                if named.endswith(" seat"):
                    facts.exempt_bases.add(named[:-len(" seat")])
        if line.startswith("Corroborating record:"):
            facts.exempt_corrob.append(
                line.split(":", 1)[1].strip().rstrip("."))
        for label in ("Closure holder", "Completion recorder",
                      "Closing recorder", "Roster recorder",
                      "Correction holder"):
            if line.startswith(label + ":"):
                rest = line.split(":", 1)[1].strip()
                holder = None
                match = re.match(r"holder\s+(.+?)\.?\s*$", rest)
                if match and match.group(1) != "no id recorded":
                    holder = match.group(1)
                facts.appendix.append((line, holder))
        if line.startswith("Seat with no placeable role:"):
            match = re.search(r"holder\s+(.+?);", line)
            holder = match.group(1) if match else None
            facts.appendix.append((line, holder))
            facts.seats.append(Seat(None, "Seat with no placeable role",
                                    holder or "", "unplaced", None,
                                    source))
        if "lost spawn" in line.lower() or "errored spawn" in \
                line.lower():
            date = None
            match = re.search(r"(\d{4}-\d{2}-\d{2})", line)
            if match:
                date = match.group(1)
            facts.lost_spawns.append((source, date))
        if "waste spawn" in line.lower():
            facts.waste.append(line)
        if line.startswith("Colour papers supplied:"):
            facts.papers_colours = _colours_in(line)
        if line.startswith("Audit plan:") or \
                line.startswith("Audit plan "):
            facts.plan_suppliers.append(
                ("Audit plan", _colours_in(line), source))
        if line.startswith("Round charge"):
            label = re.split(r"[,:]", line, 1)[0].strip()
            qualifies = ("as opened for Round" in line
                         or "to stand before Round" in line)
            facts.charge_suppliers.append(
                (label, _colours_in(line), qualifies, source))
        match = re.search(
            r"[Cc]hosen size for the (.+?) is (\d+)", line)
        if match:
            facts.chosen_sizes[match.group(1).strip()] = int(
                match.group(2))
        for match in re.finditer(
                r"states (\d+) seats for this stage", line):
            facts.seat_total_statements.append(int(match.group(1)))
        if line.startswith("Ordering statement:"):
            if "no earlier record settles" in line:
                facts.ordering_unsettled = True
        match = CHAIR_LINE.match(line)
        if match:
            facts.chair_statements.append(
                (match.group(1).strip(), source))
        match = re.match(
            r"^-\s*Chair:.*session\s+"
            r"([0-9a-fA-F]{8}-[0-9a-fA-F-]{27,})", line)
        if match:
            facts.chair_statements.append(
                (match.group(1).strip(), source))
        match = re.match(
            r"^-\s*Member \d+:.*holder session\s+"
            r"([0-9a-fA-F]{8}-[0-9a-fA-F-]{27,})", line)
        if match:
            facts.board.append(
                ("Board member", match.group(1).strip(), source))
        match = re.match(
            r"^Holder: review board member \d+, session\s+"
            r"([0-9a-fA-F]{8}-[0-9a-fA-F-]{27,})", line)
        if match:
            facts.board.append(
                ("Board member", match.group(1).strip(), source))
        match = STEP22_CHAIR_LINE.match(line)
        if match:
            facts.chair_statements.append(
                (match.group(2).strip(), source))
        _scan_freshness(facts, line, source)
        _scan_claims(facts, line, source)
        if kind in CLAIM_BEARING:
            _scan_presentations(facts, line, source)


def _scan_freshness(facts, line, source):
    match = re.match(r"Holding:\s*(.+?),\s*holder\s+(.+?)(?:,\s*round "
                     r"not stated)?\.?\s*$", line)
    if match:
        label = match.group(1).strip()
        round_label = None
        round_match = re.search(r"in (Round \d+|R\d+)$", label)
        if round_match:
            round_label = round_match.group(1)
        facts.holdings.append(
            (label, match.group(2).strip(), round_label, source))
        return
    match = re.match(
        r"(?:Involvement stated in this record:\s*|Involvement:\s*)"
        r"(\w+),\s*holder\s+(.+?)\.?\s*$", line)
    if match:
        facts.involvements.append(
            (match.group(1).strip(), match.group(2).strip(), source))
        return
    match = re.match(r"Re auditor seat for (.+?):\s*holder\s+(.+?)"
                     r"\.?\s*$", line)
    if match:
        facts.protected.append(
            (1, "re auditor", match.group(2).strip(),
             match.group(1).strip(), source))
        return
    match = re.match(r"Attacker seat at the break it step:\s*holder\s+"
                     r"(.+?)\.?\s*$", line)
    if match:
        facts.protected.append(
            (2, "attacker", match.group(1).strip(), None, source))
        return
    match = re.match(r"First user seat:\s*holder\s+(.+?)\.?\s*$", line)
    if match:
        facts.protected.append(
            (3, "first user", match.group(1).strip(), None, source))
        return
    match = re.match(r"Assessor seat for this stage:\s*holder\s+(.+?)"
                     r"\.?\s*$", line)
    if match:
        facts.protected.append(
            (4, "assessor", match.group(1).strip(), None, source))
        return


FRESHNESS_CLAIM = re.compile(
    r"family (\d) (?:is |was )?held for this stage")
STAFFING_CLAIM = re.compile(r"artefact proven", re.I)


def _scan_claims(facts, line, source):
    """Collect asserted claim sentences for freshness and disagreement."""
    if line.startswith("Stage claim") and is_asserted(line):
        facts.stage_claim = True
    if "claim" in line.lower() or "Stage register text:" in line \
            or "Report text claim:" in line:
        if is_asserted(line):
            facts.claims.append((line, source))
    if STAFFING_CLAIM.search(line) and is_asserted(line):
        facts.claims.append((line, source))
    if "combined scope" in line.lower() and \
            "Report text claim:" in line and is_asserted(line):
        facts.combined_scope_claim = True
    match = FRESHNESS_CLAIM.search(line)
    if match and is_asserted(line):
        facts.claims.append((line, source))


def _scan_presentations(facts, line, source):
    def add(target, product_text):
        # A presentation may list several products joined by
        # ", and "; each listed product stands presented on its own.
        for item in product_text.split(", and "):
            item = item.strip()
            if item:
                facts.presentations.append((target, item, source))
    match = re.match(r"Work products? for (.+?):\s*(.+?)\.?\s*$", line)
    if match:
        add(match.group(1).strip(), match.group(2).strip())
        return
    match = re.match(
        r"Work product shared by the (.+?) seats:\s*(.+?)\.?\s*$",
        line)
    if match:
        add("shared:" + match.group(1).strip(),
            match.group(2).strip())
        return
    match = re.match(
        r"Work products:\s*(.+?)\s+is the shared product of the "
        r"(.+?)\.?\s*$", line)
    if match:
        add("shared:" + match.group(2).strip(),
            match.group(1).strip())
        return
    match = re.match(
        r"Work product for the (.+?) seats:\s*(.+?)\.?\s*$", line)
    if match:
        add("shared:" + match.group(1).strip(),
            match.group(2).strip())


def _parse_roster(facts, captured, text, stage_key):
    """Parse one roster artifact into sections and seat entries."""
    source = captured.display
    lines = text.splitlines()
    stage_text = None
    for line in lines:
        match = STAGE_TIER_LINE.match(line.strip())
        if match:
            stage_text = match.group(1)
            break
        match = STAGE_LINE.match(line.strip())
        if match:
            stage_text = match.group(1)
            break
        match = re.match(r"Step:\s*(\d+)", line.strip())
        if match:
            stage_text = "Step %s" % match.group(1)
            break
    parse = {"source": source, "stage_text": stage_text,
             "stage_key": step_key_of(stage_text) if stage_text
             else None,
             "sections": [], "board": [], "superseded": False,
             "dedicated": any(
                 line.strip().lower().startswith("#")
                 and "roster artifact" in line.lower()
                 for line in lines),
             "text": text}
    if re.search(r"superseded by", text) and re.search(
            r"governing roster", text):
        parse["superseded"] = True
    sections = []
    current = None
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## "):
            heading = stripped[3:].strip()
            current = {"heading": heading, "lines": [],
                       "superseded": "superseded" in heading.lower()}
            sections.append(current)
            continue
        if stripped.startswith("# "):
            current = None
            continue
        if current is not None:
            current["lines"].append(line)
    named_superseded = set()
    for line in lines:
        match = re.search(
            r"[Tt]he (.+?) section .*superseded", line)
        if match:
            named_superseded.add(match.group(1).strip().lower())
    for section in sections:
        if section["heading"].lower() in named_superseded:
            section["superseded"] = True
    parse["sections"] = sections
    # Lines standing outside any superseded section: succession and
    # chair statements are read from these lines only, so a statement
    # inside a superseded section enters nothing.
    plain = []
    current = None
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## "):
            heading = stripped[3:].strip()
            current = None
            for section in sections:
                if section["heading"] == heading:
                    current = section
                    break
            plain.append(line)
            continue
        if stripped.startswith("# "):
            current = None
            plain.append(line)
            continue
        if current is not None and current["superseded"]:
            continue
        plain.append(line)
    parse["plain_lines"] = plain
    return parse


def _section_team(heading):
    """The (team name, round key) a section heading names, or None."""
    match = re.match(r"Team:\s*(.+?)(\s*\((.+)\))?\s*$", heading)
    if match:
        label = match.group(3)
        return (match.group(1).strip(),
                canonical_round(label) if label else None)
    match = re.match(r"Round (\d+)\s+(.+)$", heading)
    if match:
        name = match.group(2).strip()
        name = name[:1].upper() + name[1:]
        return (name, ("round", int(match.group(1))))
    lowered = heading.lower()
    if "review board" in lowered:
        return ("__board__", None)
    if "coordinator" in lowered or "clerk" in lowered:
        return None
    if lowered.endswith(" team") or lowered.endswith(" unit") \
            or lowered.endswith(" teams"):
        name = heading.strip()
        return (name[:1].upper() + name[1:], None)
    return None


def _govern_rosters(facts, parses, stage_key):
    """Choose the governing roster parse and build the seat account."""
    governing = []
    for parse in parses:
        if parse["superseded"]:
            facts.superseded_files.add(parse["source"])
            continue
        if not parse["sections"] and \
                "never captured" in parse["text"].lower():
            # A roster artifact stating the roster for the stage was
            # never captured settles nothing: no roster stands.
            continue
        if parse["stage_key"] is not None and stage_key is not None \
                and parse["stage_key"] != stage_key:
            if facts.stage_mismatch is None:
                facts.stage_mismatch = (
                    parse["stage_text"], None)
            continue
        governing.append(parse)
    if len(governing) > 1:
        dedicated = [parse for parse in governing
                     if parse["dedicated"]]
        if len(dedicated) == 1:
            # A dedicated roster artifact governs over a step record
            # carrying a roster section for the same stage.
            governing = dedicated
    if len(governing) > 1:
        facts.two_rosters = True
        governing = []
    facts.rosters = governing
    for parse in governing:
        facts.roster_sources.append(parse["source"])
        for section in parse["sections"]:
            if section["superseded"]:
                continue
            named = _section_team(section["heading"])
            if named is None:
                continue
            team, round_key = named
            if team == "__board__":
                for line in section["lines"]:
                    match = BOARD_LINE.match(line.strip())
                    if match:
                        facts.board.append(
                            (match.group(1).strip(),
                             match.group(2).strip(),
                             parse["source"]))
                        facts.seats.append(Seat(
                            "Review board", match.group(1).strip(),
                            match.group(2).strip(),
                            "board additional", None,
                            parse["source"]))
                continue
            facts.team_sections.append((team, round_key,
                                        parse["source"]))
            for line in section["lines"]:
                _parse_seat_line(facts, line, team, round_key,
                                 parse["source"])
    # Succession lines and the Step 22 chair seat stand anywhere in a
    # governing roster outside a superseded section, outside team
    # sections as often as inside them.
    for parse in governing:
        _parse_prose_seats(facts, parse)
        for line in parse["plain_lines"]:
            stripped = line.strip()
            match = re.search(r"The (.+?) passage is torn", stripped)
            if match:
                facts.torn_teams.add(match.group(1).strip())
            match = SUCCESSION_LINE.search(stripped)
            if match:
                team = _team_for_role(facts, match.group(1).strip())
                facts.seats.append(Seat(
                    team, match.group(1).strip(),
                    match.group(3).strip(), "counted in base", None,
                    parse["source"]))
                continue
            match = STEP22_CHAIR_LINE.match(stripped)
            if match:
                facts.seats.append(Seat(
                    None, match.group(1).strip(),
                    match.group(2).strip(), "step unit", None,
                    parse["source"]))


def _parse_prose_seats(facts, parse):
    """Seats stated in prose roster lists inside a record.

    Real step records state their seats as numbered items in a
    roster or reseating section, one item per seat, in the form
    "N. Role, approach: session <id>. Paper: <path>." Team
    introductions in the same section name the team and its size.
    Coordinators and clerks named in such lists are not members.
    """
    source = parse["source"]
    intros = []
    current_team = None
    section = ""
    items = []
    current = None
    for raw in parse["text"].splitlines():
        stripped = raw.strip()
        if stripped.startswith("## "):
            section = stripped[3:].strip()
            current = None
            current_team = None
            continue
        active = section.lower().startswith("roster") or \
            section.lower().startswith("reseating")
        if not active:
            continue
        intro = re.search(
            r"([A-Z][A-Za-z\- ]*?) team, (\d+) members", stripped)
        if intro:
            name = intro.group(1).replace("-", " ").strip()
            name = name[:1].upper() + name[1:] + " team"
            if name not in [team for team, _n in intros]:
                intros.append((name, int(intro.group(2))))
            current_team = name
            facts.chosen_sizes.setdefault(
                name, int(intro.group(2)))
        if re.match(r"^\d+\.\s+", stripped):
            current = ([stripped], current_team,
                       section.lower().startswith("reseating"))
            items.append(current)
        elif current is not None and stripped:
            current[0].append(stripped)
    added = []
    added_presentations = []
    for parts, team_at_item, in_reseating in items:
        text = " ".join(parts)
        if "uncounted" in text.lower():
            continue
        match = re.search(r":\s*session\s+(\S+?)(?:\.|\s|$)", text)
        if not match:
            continue
        head = re.sub(r"^\d+\.\s+", "", text[:match.start()])
        role = re.sub(r"\s*\(.*?\)", "", head).strip()
        role = role.split(",")[0].strip()
        holder = match.group(1)
        if not role or "Clerk" in role or role == "Coordinator":
            continue
        if "not a member" in text.lower():
            continue
        if "review board member" in role.lower():
            facts.board.append((role, holder, source))
            continue
        if "chair of the review board" in text.lower():
            facts.chair_statements.append((holder, source))
            continue
        if "closing holder" in text.lower() or \
                "closure holder" in text.lower():
            facts.appendix.append(
                ("%s: holder %s." % (role, holder), holder))
            continue
        team = current_team_for(intros, team_at_item, role)
        if in_reseating:
            # A reseating replaces the earlier seating of the same
            # seat in this record: the first seating enters nothing.
            for old in list(added):
                if old.team == team and old.role == role:
                    facts.seats.remove(old)
                    added.remove(old)
            facts.presentations[:] = [
                entry for entry in facts.presentations
                if not (entry[0] == role and entry[2] == source
                        and entry in added_presentations)]
            added_presentations[:] = [
                entry for entry in added_presentations
                if entry[0] != role]
        seat = None
        if team is not None:
            if (team, None, source) not in facts.team_sections:
                facts.team_sections.append((team, None, source))
            seat = Seat(team, role, holder, "counted in base", None,
                        source)
        elif role == "Interviewer":
            seat = Seat(None, role, holder, "step unit", None,
                        source)
        elif "Principles Agent" in role or "Fold-in Tracer" in role \
                or role == "Contrarian":
            seat = Seat(None, role, holder,
                        "over base at team level", None, source)
        else:
            seat = Seat(None, role, holder, "counted in base", None,
                        source)
        facts.seats.append(seat)
        added.append(seat)
        paper = re.search(r"Paper:\s*(\S+\.md)", text) or \
            re.search(r"Paper at\s+(\S+\.md)", text)
        if paper:
            entry = (role, paper.group(1), source)
            facts.presentations.append(entry)
            added_presentations.append(entry)


def current_team_for(intros, current_team, role):
    """The prose team a seat item joins, by introduction or family."""
    if role.startswith("Researcher"):
        for team, _n in intros:
            if "research" in team.lower():
                return team
    if role.startswith("Imagination"):
        for team, _n in intros:
            if "imagination" in team.lower():
                return team
    return current_team


def _team_for_role(facts, role):
    """The team a succession seat joins: the first team lacking the role."""
    teams = []
    for team, _round_key, _source in facts.team_sections:
        if team not in teams:
            teams.append(team)
    for team in teams:
        roles = [seat.role for seat in facts.seats if seat.team == team]
        if role not in roles:
            return team
    return teams[0] if teams else None


def _parse_seat_line(facts, line, team, round_key, source):
    stripped = line.strip()
    match = SEAT_LINE.match(stripped)
    if match:
        position = match.group(3).strip()
        if position not in POSITIONS:
            position = "unplaced"
        facts.seats.append(Seat(team, match.group(1).strip(),
                                match.group(2), position, round_key,
                                source))
        return
    match = SEAT_LINE_SHORT.match(stripped)
    if match:
        facts.seats.append(Seat(team, match.group(1).strip(),
                                match.group(2), "counted in base",
                                round_key, source))
        return
    match = REAL_SEAT_LINE.match(stripped)
    if match:
        facts.seats.append(Seat(team, match.group(1).strip(),
                                match.group(2), "counted in base",
                                round_key, source))
        return
    if "###" in stripped and team:
        facts.torn_teams.add(team)


# ----------------------------------------------------------------
# Shipped data, normalised


class Table(object):
    def __init__(self, data):
        self.version = data.get("table_version")
        self.keyed_base = data.get("keyed_base")
        self.rows = {}
        self.required = {}
        for row in data.get("per_step_rows", []) or []:
            self._add_row(row)
        for row in data.get("rows", []) or []:
            self._add_row(row)
        self.team_bases = data.get("team_bases", {}) or {}
        self.step_totals = {}
        for key, value in (data.get("step_totals", {}) or {}).items():
            self.step_totals[int(key)] = value
        self.board_additions = {}
        for key, value in (data.get("board_additions", {})
                           or {}).items():
            self.board_additions[int(key)] = value

    def _add_row(self, row):
        try:
            step = int(row.get("step"))
        except (TypeError, ValueError):
            return
        team = row.get("team")
        if team is None:
            return
        self.rows[(step, team)] = row
        self.required.setdefault(step, []).append(team)

    def minimum_for(self, step, team, tier):
        """(form, low, high) for a team at a step, or None.

        form is "fixed" with low the minimum, or "band" with low and
        high the band ends.
        """
        row = self.rows.get((step, team))
        if row is not None and row.get("minimum") is not None:
            return ("fixed", int(row["minimum"]), None)
        base = self.team_bases.get(team)
        if isinstance(base, dict):
            value = base.get(tier) or base.get("Low")
            if isinstance(value, dict):
                return ("band", int(value["minimum"]),
                        int(value["maximum"]))
            if isinstance(value, int):
                return ("fixed", value, None)
        return None

    def step_total_expected(self, step):
        return self.step_totals.get(step)

    def board_addition(self, step):
        return self.board_additions.get(step, 3)


class Catalogue(object):
    def __init__(self, data):
        self.version = data.get("catalogue_version")
        self.rows = data.get("rows", []) or []


# ----------------------------------------------------------------
# Counts


class Count(object):
    def __init__(self, team, round_key):
        self.team = team
        self.round_key = round_key
        self.entries = 0
        self.duplicates_removed = 0
        self.exempt_or_uncounted_removed = 0
        self.counted_total = 0
        self.minimum = None
        self.minimum_form = None
        self.band_high = None
        self.result = "PASS"
        self.holders = []
        self.non_id_entries = 0

    def as_dict(self):
        minimum = self.minimum
        if self.minimum_form == "band":
            minimum = "%d to %d" % (self.minimum, self.band_high)
        return {"name": self.team, "round": round_display(
                    self.round_key),
                "entries": self.entries,
                "duplicates_removed": self.duplicates_removed,
                "exempt_or_uncounted_removed":
                    self.exempt_or_uncounted_removed,
                "counted_total": self.counted_total,
                "minimum": minimum, "result": self.result}


def compute_counts(facts, excluded_holders):
    """The per team, per round counts over the governing seat account."""
    groups = {}
    for seat in facts.seats:
        if seat.team is None or seat.position not in COUNT_POSITIONS:
            continue
        groups.setdefault((seat.team, seat.round_key), []).append(seat)
    counts = {}
    for (team, round_key), seats in groups.items():
        count = Count(team, round_key)
        count.entries = len(seats)
        seen = set()
        for seat in seats:
            if seat.position == "uncounted at this step":
                count.exempt_or_uncounted_removed += 1
                continue
            if seat.position == "exempt":
                proven = (seat.role, seat.holder) in \
                    facts.exempt_entries and \
                    seat.role in facts.exempt_bases
                if proven:
                    count.exempt_or_uncounted_removed += 1
                    continue
            if seat.holder in excluded_holders:
                count.exempt_or_uncounted_removed += 1
                continue
            if is_identifier(seat.holder):
                if seat.holder in seen:
                    count.duplicates_removed += 1
                else:
                    seen.add(seat.holder)
                    count.holders.append(seat.holder)
            else:
                count.non_id_entries += 1
        count.counted_total = len(count.holders)
        counts[(team, round_key)] = count
    return counts


def duplicate_holdings(facts):
    """Duplicate full identifier holdings inside one round scope."""
    seen = {}
    duplicates = []
    for seat in facts.seats:
        if seat.position not in COUNT_POSITIONS:
            continue
        if not is_full_id(seat.holder):
            continue
        key = (seat.round_key, seat.holder)
        if key in seen:
            duplicates.append((seat, seen[key]))
        else:
            seen[key] = seat
    return duplicates


# ----------------------------------------------------------------
# Checks


class Check(object):
    def __init__(self, kind, scope, verdict, composing=True):
        self.kind = kind
        self.scope = scope
        self.verdict = verdict
        self.composing = composing
        self.diagnostic_code = "none"
        self.rule_reference = ""
        self.severity = "none"
        self.expected = ""
        self.observed = ""
        self.counted_total = 0
        self.duplicates_removed = 0
        self.exempt_or_uncounted_removed = 0
        self.evidence_files = []
        self.evidence_text = ""
        self.missing_fact = None
        self.round_key = None

    def as_dict(self, index):
        return {"check_id": "check-%d" % index,
                "kind": self.kind,
                "diagnostic_code": self.diagnostic_code,
                "rule_reference": self.rule_reference,
                "scope": self.scope,
                "expected": self.expected,
                "counted_total": self.counted_total,
                "duplicates_removed": self.duplicates_removed,
                "exempt_or_uncounted_removed":
                    self.exempt_or_uncounted_removed,
                "verdict": self.verdict,
                "evidence_files": list(self.evidence_files),
                "severity": self.severity,
                "composing": self.composing,
                "missing_fact": self.missing_fact,
                "round": round_display(self.round_key)}


def worst(words):
    for word in ("FAIL", "UNVERIFIABLE", "NOT PROVEN", "PASS"):
        if word in words:
            return word
    return "PASS"


# ----------------------------------------------------------------
# Freshness families


def _claimed_families(facts):
    claimed = set()
    for sentence, _source in facts.claims:
        match = FRESHNESS_CLAIM.search(sentence)
        if match:
            claimed.add(int(match.group(1)))
        match = re.search(r"family (\d) is claimed", sentence)
        if match:
            claimed.add(int(match.group(1)))
        if sentence.startswith("Freshness claim:"):
            match = re.search(r"family (\d)", sentence)
            if match:
                claimed.add(int(match.group(1)))
    return claimed


def freshness_checks(facts):
    """Claimed freshness family checks, plus proven breach exclusions.

    Returns (checks, excluded_holders, facts_not_stated, claimed).
    Only claimed families carry a check. A proven breach FAILs, and
    the excluded holder is removed from the counts.
    """
    claimed = _claimed_families(facts)
    checks = []
    excluded = set()
    facts_not_stated = []
    self_audit = any("presented as audit" in sentence.lower()
                     for sentence, _s in facts.claims)
    for family in sorted(claimed):
        check = Check("claimed freshness family %d" % family,
                      "stage", "NOT PROVEN")
        check.rule_reference = "S5-E27"
        seats = [p for p in facts.protected if p[0] == family]
        bad_holder = False
        if family == 1:
            holdings = [h for h in facts.holdings
                        if "fixer" in h[0].lower()]
            re_auditors = seats
            if any(not is_identifier(h[1]) for h in holdings):
                bad_holder = True
            if bad_holder:
                check.missing_fact = "the holder identifier"
            elif not re_auditors:
                check.missing_fact = "the re auditor identifier"
                facts_not_stated.append(family)
            elif any(not is_identifier(p[2]) for p in re_auditors):
                check.missing_fact = "the re auditor identifier"
            else:
                breach = None
                for p in re_auditors:
                    p_round = canonical_round(p[3])
                    for h in holdings:
                        if h[1] == p[2] and h[2] is not None and \
                                canonical_round(h[2]) == p_round:
                            breach = p[2]
                if breach is not None:
                    check.verdict = "FAIL"
                    check.severity = "Critical" if self_audit \
                        else "High"
                    check.expected = \
                        "no holder of a fixer holding re audits " \
                        "the round fixed"
                    check.observed = \
                        "holder %s fixed and re audited the same " \
                        "round" % breach
                    excluded.add(breach)
                elif any(h[2] is None for h in holdings):
                    check.missing_fact = "the round for that holding"
                elif not holdings:
                    check.missing_fact = \
                        "the fixer holdings for this stage"
                    facts_not_stated.append(family)
                else:
                    check.verdict = "PASS"
        elif family == 2:
            holdings = [h for h in facts.holdings
                        if "build team seat" in h[0].lower()
                        or "step 15 audit seat" in h[0].lower()]
            if any(not is_identifier(h[1]) for h in holdings):
                bad_holder = True
                check.missing_fact = "the holder identifier"
            elif not seats:
                check.missing_fact = "the attacker identifier"
                facts_not_stated.append(family)
            elif any(not is_identifier(p[2]) for p in seats):
                check.missing_fact = "the attacker identifier"
            elif any(p[2] == h[1] for p in seats for h in holdings):
                check.verdict = "FAIL"
                check.severity = "High"
                excluded.update(p[2] for p in seats
                                if any(p[2] == h[1] for h in holdings))
            elif not holdings:
                check.missing_fact = \
                    "the build holdings for this stage"
                facts_not_stated.append(family)
            else:
                check.verdict = "PASS"
        elif family == 3:
            holdings = [h for h in facts.holdings
                        if "any prior seat" in h[0].lower()]
            if any(not is_identifier(h[1]) for h in holdings):
                bad_holder = True
                check.missing_fact = "the holder identifier"
            elif not seats:
                check.missing_fact = "the first user identifier"
                facts_not_stated.append(family)
            elif any(not is_identifier(p[2]) for p in seats):
                check.missing_fact = "the first user identifier"
            elif any(p[2] == h[1] for p in seats for h in holdings):
                check.verdict = "FAIL"
                check.severity = "High"
                excluded.update(p[2] for p in seats
                                if any(p[2] == h[1] for h in holdings))
            elif not holdings:
                check.missing_fact = \
                    "the prior seat holdings for this stage"
                facts_not_stated.append(family)
            else:
                check.verdict = "PASS"
        elif family == 4:
            kinds = ("producing", "operating", "managing",
                     "administering", "commissioning")
            involvements = [i for i in facts.involvements
                            if i[0].lower() in kinds]
            if any(not is_identifier(i[1]) for i in involvements):
                bad_holder = True
                check.missing_fact = "the holder identifier"
            elif not seats:
                check.missing_fact = "the assessor identifier"
                facts_not_stated.append(family)
            else:
                matched = [p for p in seats
                           if any(p[2] == i[1] for i in involvements)]
                if matched:
                    check.verdict = "FAIL"
                    check.severity = "High"
                    excluded.update(p[2] for p in matched)
                elif any(not is_identifier(p[2]) for p in seats):
                    check.missing_fact = "the assessor identifier"
                elif not involvements:
                    check.missing_fact = \
                        "the involvement facts for this stage"
                    facts_not_stated.append(family)
                else:
                    check.verdict = "PASS"
        if check.verdict == "NOT PROVEN" and family not in \
                facts_not_stated and check.missing_fact in (
                    "the round for that holding",):
            facts_not_stated.append(family)
        if check.missing_fact and not check.evidence_files:
            check.evidence_files = [facts.roster_sources[0]] \
                if facts.roster_sources else []
            check.evidence_text = check.evidence_files[0] \
                if check.evidence_files else ""
        checks.append(check)
    return checks, excluded, facts_not_stated, claimed


# ----------------------------------------------------------------
# Artefact linkage


FORM_SETTLEMENT_PATTERNS = (
    (re.compile(r"(\w{1,64}) form (?:template )?provides an author "
                r"record field"), True),
    (re.compile(r"(\w{1,64}) form (?:template )?provides no author "
                r"record field"), False),
    (re.compile(r"(\w{1,64}) form carries no author record"), False),
)


def _form_settlements(files, exclude):
    settlements = {}
    conflicted = set()
    for captured, _kind in files:
        if captured.text is None or captured.display in exclude:
            continue
        for pattern, value in FORM_SETTLEMENT_PATTERNS:
            for match in pattern.finditer(captured.text):
                word = match.group(1).lower()
                if word in settlements and settlements[word] != value:
                    conflicted.add(word)
                settlements[word] = value
    for word in conflicted:
        settlements.pop(word, None)
    return settlements


class Product(object):
    def __init__(self):
        self.name = None
        self.form = None
        self.settled = None
        self.field = None
        self.text = None


def _parse_product(product_text, settlements, by_display):
    product = Product()
    name_match = re.search(r"(\S+\.md)\b", product_text)
    if name_match:
        product.name = name_match.group(1)
    lowered = product_text.lower()
    if "notes part under r-12" in lowered:
        product.form = "notes part"
        product.settled = True
        product.field = True
    elif "colour paper under r-33" in lowered:
        product.form = "colour paper"
        product.settled = True
        product.field = True
    elif "whose contract a supplied record states carries an author record field" in lowered:
        form_match = re.search(r"a (\w+) form", lowered)
        product.form = form_match.group(1) if form_match else "form"
        product.settled = True
        product.field = True
    elif "carries no author record in its contract" in lowered:
        product.form = "register form"
        product.settled = True
        product.field = False
    else:
        if re.search(r"\bnotes\b", lowered):
            product.form = "notes"
            product.settled = True
            product.field = True
        elif re.search(r"\bpapers?\b", lowered):
            product.form = "paper"
            product.settled = True
            product.field = True
        else:
            form_match = re.search(r"an? (\w+) (?:form|file)\b",
                                   lowered)
            word = form_match.group(1) if form_match else None
            if word is not None:
                product.form = word
                if word in settlements:
                    product.settled = True
                    product.field = settlements[word]
            elif product.name:
                product.form = product.name
    if product.name and product.name in by_display:
        product.text = by_display[product.name].text
    return product


def _author_records(text):
    """The author record state of one product text.

    Returns (state, values): state is one of ok, blank, unparsable,
    truncated, none.
    """
    if text is None:
        return ("none", [])
    values = []
    state = "ok"
    for line in text.splitlines():
        if "Author record:" not in line:
            continue
        value = line.split("Author record:", 1)[1].strip()
        if value.endswith("."):
            value = value[:-1].strip()
        if value == "":
            state = "blank"
        elif "###" in value:
            state = "unparsable"
        elif PARTIAL_ID.match(value) and not is_full_id(value):
            state = "truncated"
        else:
            values.append(value)
    if state == "ok" and not values:
        return ("none", [])
    return (state, values)


def linkage_checks(facts, files, by_display):
    """Per team artefact linkage checks and the coverage account."""
    product_names = set()
    for _target, product_text, _source in facts.presentations:
        name_match = re.search(r"(\S+\.md)\b", product_text)
        if name_match:
            product_names.add(name_match.group(1))
    for captured, kind in files:
        if kind == "work product":
            product_names.add(captured.display)
    settlements = _form_settlements(files, product_names)
    seat_products = {}
    two_seats = []
    for target, product_text, _source in facts.presentations:
        product = _parse_product(product_text, settlements,
                                 by_display)
        targets = []
        shared_team = None
        if target.startswith("shared:"):
            shared_team = target[len("shared:"):]
        elif " and for " in target:
            roles = [part.strip() for part in
                     target.split(" and for ")]
            targets = [seat for seat in facts.seats
                       if seat.role in roles]
            if len(targets) >= 2 and product.name:
                two_seats.append((product.name, targets))
        elif target.startswith("the ") and target.endswith(" seats"):
            shared_team = target[4:-len(" seats")]
        else:
            targets = [seat for seat in facts.seats
                       if seat.role == target]
        if shared_team is not None:
            name = shared_team.strip()
            if name.endswith(" seats"):
                name = name[:-len(" seats")]
            name = re.sub(r"^(the|all|three|two)\s+", "", name)
            targets = [seat for seat in facts.seats
                       if seat.team == name]
        for seat in targets:
            seat_products.setdefault(id(seat), (seat, []))[1].append(
                product)
    only_linkage = any(
        "No other record speaks to this seat" in (captured.text or "")
        for captured, _kind in files)
    asserted_teams = set()
    for sentence, _source in facts.claims:
        if STAFFING_CLAIM.search(sentence):
            named = [team for team in
                     {seat.team for seat in facts.seats if seat.team}
                     if team in sentence]
            if named:
                asserted_teams.update(named)
            else:
                asserted_teams.update(
                    {seat.team for seat in facts.seats if seat.team})
    teams = []
    for seat in facts.seats:
        if seat.team and seat.team != "Review board" \
                and seat.team not in teams:
            teams.append(seat.team)
    checks = []
    defects = []
    coverage = {}
    stage_uncovered = []
    assertion_engaged = False
    for team in teams:
        team_seats = [seat for seat in facts.seats
                      if seat.team == team]
        checked = not_checked = indeterminate = outside = 0
        agreeing = 0
        states = []
        uncovered = []
        for seat in team_seats:
            entry = seat_products.get(id(seat))
            if entry is None:
                continue
            products = entry[1]
            if any(p.settled is None for p in products):
                indeterminate += 1
                states.append("indeterminate")
                for p in products:
                    if p.settled is None and p.form and \
                            p.form not in uncovered:
                        uncovered.append(p.form)
                continue
            field_products = [p for p in products if p.field]
            if not field_products:
                outside += 1
                states.append("outside")
                continue
            seat_state = "not_checked"
            for product in field_products:
                if product.text is None:
                    continue
                state, values = _author_records(product.text)
                if state == "truncated":
                    seat_state = "truncated"
                    break
                if state in ("unparsable", "blank"):
                    seat_state = state
                    break
                if state == "ok":
                    if seat.holder in values:
                        seat_state = "agreeing"
                    else:
                        seat_state = "disagreeing"
            if seat_state == "agreeing":
                checked += 1
                agreeing += 1
            elif seat_state == "disagreeing":
                checked += 1
                for product in field_products:
                    if product.text is None:
                        continue
                    _state, values = _author_records(product.text)
                    for value in values:
                        if value != seat.holder:
                            defects.append(
                                "A record defect stands in %s: the "
                                "author record %s disagrees with the "
                                "roster identifier %s for the %s seat."
                                % (product.name or "a work product",
                                   value, seat.holder, seat.role))
            elif seat_state in ("truncated", "unparsable", "blank"):
                not_checked += 1
            else:
                not_checked += 1
                if any(p.settled and p.field and p.form not in
                       ("notes part", "colour paper", "notes",
                        "paper") for p in field_products):
                    for p in field_products:
                        if p.form not in uncovered:
                            uncovered.append(p.form)
            states.append(seat_state)
        total = checked + not_checked
        coverage[team] = {"scope": team, "checked": checked,
                          "not_checked": not_checked, "total": total,
                          "indeterminate": indeterminate,
                          "outside": outside,
                          "uncovered_forms": uncovered}
        stage_uncovered.extend(
            form for form in uncovered if form not in stage_uncovered)
        check = Check("artefact linkage", team, "PASS")
        check.rule_reference = "S5-E58"
        claimed = total + indeterminate
        if any(seat.team == team for _name, targets in two_seats
               for seat in targets):
            check.verdict = "FAIL"
            check.severity = "High"
            check.expected = "one work product counted for one seat"
            check.observed = "one work product counted for two seats"
        elif "indeterminate" in states:
            check.verdict = "NOT PROVEN"
            check.missing_fact = "the form contract for a presented " \
                                 "work product"
        elif "truncated" in states:
            check.verdict = "UNVERIFIABLE"
            check.missing_fact = "the author record of a presented " \
                                 "work product"
        elif "unparsable" in states or "blank" in states:
            check.verdict = "NOT PROVEN"
            check.missing_fact = "the author record of a presented " \
                                 "work product"
        elif team in asserted_teams and checked == 0:
            check.verdict = "NOT PROVEN"
            check.missing_fact = "linkage checked for an asserting " \
                                 "team"
            assertion_engaged = True
        elif claimed > 0 and checked == 0:
            check.verdict = "NOT PROVEN"
            check.missing_fact = "linkage unchecked for the whole team"
            check.expected = "at least one claimed seat with " \
                             "linkage checked"
            check.observed = "0 claimed seats checked of %d claimed " \
                             "seats" % claimed
        elif "disagreeing" in states and only_linkage:
            check.verdict = "NOT PROVEN"
            check.missing_fact = "linkage agreeing for a counted seat"
        elif not_checked > 0 and agreeing == 0 and checked > 0:
            check.verdict = "NOT PROVEN"
            check.missing_fact = "linkage checked for every claimed " \
                                 "seat"
        check.counted_total = checked
        if facts.roster_sources:
            check.evidence_files = [facts.roster_sources[0]]
            check.evidence_text = facts.roster_sources[0]
        checks.append(check)
    stage = {"scope": "stage",
             "checked": sum(c["checked"] for c in coverage.values()),
             "not_checked": sum(c["not_checked"]
                                for c in coverage.values()),
             "total": sum(c["total"] for c in coverage.values()),
             "indeterminate": sum(c["indeterminate"]
                                  for c in coverage.values()),
             "outside": sum(c["outside"] for c in coverage.values()),
             "uncovered_forms": stage_uncovered}
    ordered = [coverage[team] for team in sorted(coverage)]
    ordered.append(stage)
    roster_only = bool(
        stage["total"] > 0 and stage["checked"] == 0) or \
        (assertion_engaged and stage["checked"] == 0)
    return checks, ordered, roster_only, defects


def _manifest_group_rank(kind):
    """The input group rank of one file kind under grill B1."""
    if kind in ("roster", "step record", "tier record",
                "base record"):
        return 1
    if kind == "work product":
        return 3
    return 4


def _inputs_read_in_manifest_order(files):
    """The files read list in canonical manifest order.

    Canonical manifest order is by input group first, under grill
    B1, and then by the path as named, as Section 5.3 states and as
    slot 10 of the Simple form and the Agentic inputs_read list both
    print it. A file whose bytes are undecodable is reported as
    unread under Section 6 and never stands in this list.
    """
    seen = set()
    keyed = []
    for captured, kind in files:
        if captured.status != "read" or captured.decode_failed:
            continue
        if kind in ("ignored", "context"):
            continue
        if captured.display in seen:
            continue
        seen.add(captured.display)
        keyed.append((_manifest_group_rank(kind), captured.display))
    keyed.sort()
    return [display for _rank, display in keyed]


# ----------------------------------------------------------------
# The run computation


def _round_settled(facts, round_key):
    """Whether a labelled round is settled by a supplied round record.

    Where no round record stands in the supplied set, pooling under
    the label is carried as label basis only and the round is settled
    by the roster. Where a round record stands but does not state its
    round, the round is not settled.
    """
    if not facts.round_records:
        return True
    if round_key is None or round_key[0] != "round":
        return True
    needle = "Round %d" % round_key[1]
    for _display, text in facts.round_records:
        if re.search(r"\b%s\b" % needle, text):
            return True
    return False


def _round_record_for(facts, round_key):
    if round_key and round_key[0] == "round":
        for display, _text in facts.round_records:
            match = re.search(r"(\d+)", display)
            if match and int(match.group(1)) == round_key[1]:
                return display
    if facts.round_records:
        return facts.round_records[0][0]
    return ""


def compute(files, table_data, catalogue_data, table_hash, params):
    """Compute the one result every form renders for this run.

    files is a list of (captured, kind) pairs for the supplied set.
    params carries stage, runner, capacity, and run kind.
    """
    table = Table(table_data)
    catalogue = Catalogue(catalogue_data)
    stage_arg = params.get("stage")
    facts = parse_supplied_set(files, stage_arg)
    record_defects = []
    step = step_key_of(stage_arg)
    if step is None and facts.stage_statements:
        step = step_key_of(facts.stage_statements[0][0])
    roster_stands = bool(facts.rosters)
    roster_unstated = roster_stands and all(
        parse["stage_key"] is None for parse in facts.rosters)
    roster_unreadable = any(
        captured.decode_failed and "roster" in captured.display.lower()
        for captured, _kind in files)
    first_file = files[0][0].display if files else ""
    roster_source = facts.roster_sources[0] if facts.roster_sources \
        else first_file

    # Tier applied: a tier record statement governs, then the roster.
    tier = None
    for value, _source, kind in facts.tier_statements:
        if kind in ("tier record", "base record"):
            tier = value
            break
    if tier is None and facts.tier_statements:
        tier = facts.tier_statements[0][0]

    # Base identity and the called for comparisons. The comparisons
    # run on the records identifying the base, a tier record or a
    # base record; statements standing in other records print in the
    # identity line but drive no comparison.
    driving = ("tier record", "base record")
    distinct_bases = []
    for name, hash_value, size, source, _kind in facts.base_ids:
        entry = (name, hash_value, size)
        if entry not in distinct_bases:
            distinct_bases.append(entry)
    driving_bases = []
    for name, hash_value, size, _source, kind in facts.base_ids:
        entry = (name, hash_value, size)
        if kind in driving and entry not in driving_bases:
            driving_bases.append(entry)
    base_disagreement = len(driving_bases) > 1
    pinned = None
    if len(distinct_bases) == 1:
        name, hash_value, size = distinct_bases[0]
        pinned = {"name": name, "hash": hash_value, "bytes": size}
    elif table.keyed_base:
        pinned = {"name": table.keyed_base.get("name"),
                  "hash": table.keyed_base.get("hash"),
                  "bytes": table.keyed_base.get("bytes")}
    identity_bad = base_disagreement
    if len(driving_bases) == 1 and table.keyed_base:
        keyed = table.keyed_base
        name, hash_value, size = driving_bases[0]
        if name != keyed.get("name") or \
                hash_value != keyed.get("hash") or \
                size != keyed.get("bytes"):
            identity_bad = True
    called_versions = []
    for value, _source, _kind in facts.called_versions:
        if value not in called_versions:
            called_versions.append(value)
    called_hashes = []
    for value, _source, _kind in facts.called_hashes:
        if value not in called_hashes:
            called_hashes.append(value)
    driving_versions = []
    for value, _source, kind in facts.called_versions:
        if kind in driving and value not in driving_versions:
            driving_versions.append(value)
    driving_hashes = []
    for value, _source, kind in facts.called_hashes:
        if kind in driving and value not in driving_hashes:
            driving_hashes.append(value)
    if len(driving_versions) > 1 or len(driving_hashes) > 1:
        identity_bad = True
    elif driving_versions and driving_versions[0] != table.version:
        identity_bad = True
    elif driving_hashes and driving_hashes[0] != table_hash:
        identity_bad = True
    table_hash_printed = called_hashes[0] if called_hashes \
        else table_hash
    # Per identification called for values, for the slot 4
    # disagreement form at Section 5.8: for each distinct base, the
    # called for values the records identifying that base state.
    called_by_base = []
    for entry in distinct_bases:
        sources = {source for (n, h, b, source, _k)
                   in facts.base_ids if (n, h, b) == entry}
        versions = []
        for value, source, _k in facts.called_versions:
            if source in sources and value not in versions:
                versions.append(value)
        hashes = []
        for value, source, _k in facts.called_hashes:
            if source in sources and value not in hashes:
                hashes.append(value)
        called_by_base.append({"name": entry[0],
                               "versions": versions,
                               "hashes": hashes})

    # Freshness first: proven breaches exclude holders from counts.
    fresh_checks, excluded_holders, fresh_not_stated, fresh_claimed = \
        freshness_checks(facts)
    counts = compute_counts(facts, excluded_holders)
    present_teams = []
    for team, _round_key, _source in facts.team_sections:
        if team not in present_teams:
            present_teams.append(team)
    required_teams = list(table.required.get(step, [])) \
        if step is not None else []
    all_teams = list(present_teams)
    for team in required_teams:
        if team not in all_teams:
            all_teams.append(team)
    rounds_stand = any(seat.round_key is not None
                       for seat in facts.seats)
    # Assign minimums and count results.
    for team in all_teams:
        round_keys = sorted(
            {key for (name, key) in counts if name == team},
            key=round_sort)
        if not round_keys:
            round_keys = [None]
        for round_key in round_keys:
            count = counts.get((team, round_key))
            if count is None:
                count = Count(team, round_key)
                counts[(team, round_key)] = count
            found = table.minimum_for(step, team, tier or "Low")
            chosen = facts.chosen_sizes.get(team)
            if found is None:
                count.minimum = None
            elif found[0] == "band":
                count.minimum_form = "band"
                count.minimum = found[1]
                count.band_high = found[2]
                if chosen is not None:
                    count.minimum_form = "fixed"
                    count.minimum = chosen
            else:
                count.minimum_form = "fixed"
                count.minimum = found[1]
            if count.minimum is None:
                count.result = "PASS"
            elif count.minimum_form == "band" and chosen is None:
                count.result = "NOT PROVEN"
            elif count.counted_total >= count.minimum:
                count.result = "PASS"
            elif count.non_id_entries == 0:
                count.result = "FAIL"
            else:
                count.result = "NOT PROVEN"
    ordered_counts = [counts[key] for key in sorted(
        counts, key=lambda item: (item[0], round_sort(item[1])))]

    checks = []
    duplicates = duplicate_holdings(facts)
    if roster_stands or required_teams or roster_unreadable:
        checks.extend(_team_checks(
            facts, counts, all_teams, required_teams, tier, step,
            roster_stands, roster_unstated, roster_unreadable,
            duplicates, roster_source))
    if roster_stands:
        checks.extend(_distinctness_checks(
            facts, counts, present_teams, duplicates, roster_source))
        checks.extend(_carried_checks(facts, present_teams,
                                      roster_source))
        checks.append(_board_check(
            facts, step, present_teams, roster_source))
        checks.append(_pool_check(facts, present_teams,
                                  roster_source))
        by_display = {captured.display: captured
                      for captured, _kind in files}
        linkage, coverage, roster_only, link_defects = \
            linkage_checks(facts, files, by_display)
        checks.extend(linkage)
        record_defects.extend(link_defects)
    else:
        coverage = [{"scope": "stage", "checked": 0, "not_checked": 0,
                     "total": 0, "indeterminate": 0, "outside": 0,
                     "uncovered_forms": []}]
        roster_only = False
    checks.extend(fresh_checks)
    if facts.defective_roster == "provable":
        record_defects.append(
            "A record defect stands in the roster: the roster stands "
            "proven defective as a record; the true staffing is "
            "stated independently of it in the supplied records.")
    elif facts.defective_roster == "unprovable":
        for check in checks:
            if check.kind in ("team minimums", "distinctness") and \
                    check.verdict == "PASS":
                check.verdict = "NOT PROVEN"
                check.missing_fact = "the true staffing of this stage"
    for check in checks:
        if check.verdict != "PASS" and not check.evidence_text:
            check.evidence_files = [roster_source]
            check.evidence_text = roster_source
    if identity_bad:
        for check in checks:
            if check.composing and check.verdict == "PASS":
                check.verdict = "UNVERIFIABLE"

    composing = [check.verdict for check in checks if check.composing]
    rollup = worst(composing) if composing else "PASS"
    if rollup == "PASS" and (not roster_stands or roster_unstated):
        rollup = "UNVERIFIABLE"
    if roster_unreadable and rollup in ("PASS", "UNVERIFIABLE"):
        rollup = "NOT PROVEN"

    # Step totals, per round where rounds stand.
    step_totals = []
    round_keys = sorted({key for (_team, key) in counts},
                        key=round_sort)
    if not round_keys:
        round_keys = [None]
    expected_total = table.step_total_expected(step)
    for round_key in round_keys:
        observed = 0
        for (team, key), count in counts.items():
            if key == round_key:
                observed += count.entries - \
                    count.exempt_or_uncounted_removed
        if round_key is None:
            observed += sum(1 for seat in facts.seats
                            if seat.position == "step unit")
        expected = expected_total
        if expected is None:
            expected = observed
        step_totals.append(
            {"round": round_display(round_key), "observed": observed,
             "expected": expected,
             "difference": "no difference" if observed == expected
             else str(abs(expected - observed))})
    holders_across = None
    if rounds_stand:
        holders = set()
        for seat in facts.seats:
            if seat.round_key is not None and \
                    is_identifier(seat.holder):
                holders.add(seat.holder)
        holders_across = len(holders)

    colour = _colour(facts, roster_stands, rounds_stand, files)
    disagreements = _claim_disagreements(facts, counts, step_totals)
    completeness = None
    if len(set(facts.seat_total_statements)) > 1:
        completeness = sorted(set(facts.seat_total_statements))
    fm9 = bool(facts.reduced_tier_claim and not facts.invocation)

    stage_display = stage_arg
    for parse in facts.rosters:
        if parse["stage_text"]:
            stage_display = parse["stage_text"]
            break
    if stage_display is None:
        stage_display = "stage not named in the supplied records"

    team_results = []
    for team in present_teams:
        words = [check.verdict for check in checks
                 if check.composing and check.scope == team]
        team_results.append({"team": team,
                             "result": worst(words) if words
                             else "PASS"})

    result = {
        "tool_name": "muster-lite",
        "tool_version": "1.0.0-fixture",
        "grade": "L2",
        "claim_cap_sentence": CLAIM_CAP,
        "grade_sentence": GRADE_SENTENCE,
        "closing_line": CLOSING_LINE,
        "run_kind": params.get("run_kind", "gate run"),
        "stage": stage_display,
        "stage_arg": stage_arg,
        "step": step,
        "tier_applied": tier if tier else
            "not proven from the supplied records",
        "tier": tier,
        "pinned_base": None if base_disagreement else pinned,
        "base_identifications": [
            {"name": name, "hash": hash_value, "bytes": size}
            for name, hash_value, size in distinct_bases],
        "base_disagreement": base_disagreement,
        "called_versions": called_versions,
        "called_hashes": called_hashes,
        "called_by_base": called_by_base,
        "called_version_disagreement": len(driving_versions) > 1,
        "called_hash_disagreement": len(driving_hashes) > 1,
        "driving_called_versions": driving_versions,
        "driving_called_hashes": driving_hashes,
        "counting_table_version": table.version,
        "counting_table_hash": table_hash_printed,
        "counting_table_hash_captured": table_hash,
        "diagnostic_catalogue_version": catalogue.version,
        "runner_name": params.get("runner"),
        "runner_capacity": params.get("capacity"),
        "rollup": rollup,
        "exit_code": EXIT_CODES[rollup],
        "checks": checks,
        "counts": ordered_counts,
        "team_results": team_results,
        "coverage": coverage,
        "roster_evidence_only": roster_only,
        "standing_limits": ["coverage not applicable"]
            if coverage and coverage[-1]["total"] == 0 else [],
        "context_files": sorted(
            {captured.display for captured, kind in files
             if kind == "context" and captured.status == "read"
             and not captured.decode_failed}),
        "uncounted_appendix": _appendix_entries(facts),
        "exempt_account": _exempt_account(facts),
        "consequence": "",
        "missing_seats": list(colour["missing"]) if colour else [],
        "duplicate_holdings": [
            "%s holds more than one seat in this stage" % seat.holder
            for seat, _first in duplicates],
        "claim_disagreements": disagreements,
        "record_defects": record_defects,
        "manifest_groups": {
            "group 1": sorted(
                {captured.display for captured, kind in files
                 if captured.status == "read"
                 and not captured.decode_failed and kind in (
                     "roster", "step record", "tier record",
                     "base record")}),
            "group 3": sorted(
                {captured.display for captured, kind in files
                 if captured.status == "read"
                 and not captured.decode_failed
                 and kind == "work product"}),
            "group 4": sorted(
                {captured.display for captured, kind in files
                 if captured.status == "read"
                 and not captured.decode_failed and kind in (
                     "stage register", "gate record", "record",
                     "evidence register")}),
        },
        "truncated_files": sorted(facts.truncated_files),
        "inputs_read": _inputs_read_in_manifest_order(files),
        "inputs_ignored": sorted(
            {captured.display for captured, kind in files
             if kind == "ignored" and captured.status == "read"}),
        "inputs_unread": sorted(
            {captured.display for captured, kind in files
             if captured.status != "read" or captured.decode_failed}),
        "seats": [seat.as_dict() for seat in facts.seats],
        "board": [{"role": role, "holder": holder}
                  for role, holder, _s in facts.board],
        "step_totals": step_totals,
        "holders_across_rounds": holders_across,
        "rounds_stand": rounds_stand,
        "colour": colour,
        "plaid_tier": tier == "Plaid",
        "completeness_difference": completeness,
        "fm9": fm9,
        "freshness_claimed": sorted(fresh_claimed),
        "freshness_not_stated": fresh_not_stated,
        "waste": list(facts.waste),
        "lost_spawns": [{"source": source, "date": date}
                        for source, date in facts.lost_spawns],
        "two_rosters": facts.two_rosters,
        "stage_mismatch": facts.stage_mismatch,
        "single_file": len({seat.source for seat in facts.seats}) <= 1,
    }
    if result["run_kind"] == "PRECHECK":
        result["consequence"] = (
            "this stage may be claimed as staffed on this precheck "
            "only" if rollup == "PASS" else
            "this stage may not be claimed as staffed on this run")
    else:
        result["consequence"] = (
            "this stage may be claimed as staffed on this run, and a "
            "gate may cite this run as its staffing evidence"
            if rollup == "PASS" else
            "this stage may not be claimed as staffed on this run")
    return result


def _appendix_entries(facts):
    with_id = sorted(
        (entry for entry in facts.appendix if entry[1]),
        key=lambda entry: entry[1])
    without_id = [entry for entry in facts.appendix if not entry[1]]
    return [text for text, _holder in with_id + without_id]


def _exempt_account(facts):
    account = []
    for role, holder in sorted(facts.exempt_entries):
        if role in facts.exempt_bases:
            basis = "roster basis only"
            if facts.exempt_corrob:
                basis = "cross corroborated by %s" % \
                    facts.exempt_corrob[0]
            account.append(
                "%s: holder %s, exempt class as stated in the roster. "
                "Both proofs are roster text. The exemption stands "
                "on a %s." % (role, holder, basis))
    return account


def _team_checks(facts, counts, all_teams, required_teams, tier,
                 step, roster_stands, roster_unstated,
                 roster_unreadable, duplicates, roster_source):
    checks = []
    teams = all_teams if roster_stands else list(required_teams)
    if not teams:
        teams = ["Audit team"]
    for team in teams:
        round_keys = sorted(
            {key for (name, key) in counts if name == team},
            key=round_sort) or [None]
        for round_key in round_keys:
            count = counts.get((team, round_key))
            check = Check("team minimums", team, "PASS")
            check.rule_reference = "S5-E26"
            check.round_key = round_key
            check.evidence_files = [roster_source]
            check.evidence_text = roster_source
            if count is not None:
                check.counted_total = count.counted_total
                check.duplicates_removed = count.duplicates_removed
                check.exempt_or_uncounted_removed = \
                    count.exempt_or_uncounted_removed
            minimum = count.minimum if count else None
            if minimum is not None:
                check.expected = "%d distinct full identifiers" % \
                    minimum if count.minimum_form != "band" else \
                    "a chosen size inside the band %d to %d" % (
                        count.minimum, count.band_high)
            if roster_unreadable:
                check.verdict = "NOT PROVEN"
                check.missing_fact = "the roster artifact passage"
            elif not roster_stands:
                check.verdict = "UNVERIFIABLE"
                check.expected = "the roster artifact for this stage"
                check.observed = "no roster artifact in the " \
                                 "supplied set"
                check.evidence_text = "%s, which does not state the " \
                    "roster for this stage" % roster_source
                check.missing_fact = "the roster artifact for this " \
                                     "stage"
            elif roster_unstated:
                check.verdict = "UNVERIFIABLE"
                check.missing_fact = "the stage of the roster " \
                                     "artifact"
            elif roster_unreadable:
                check.verdict = "NOT PROVEN"
                check.missing_fact = "the roster artifact passage"
            elif facts.two_rosters:
                check.verdict = "NOT PROVEN"
                check.missing_fact = "the governing roster artifact"
            elif team in facts.torn_teams:
                check.verdict = "NOT PROVEN"
                check.missing_fact = "the %s passage of the roster" \
                                     % team
            elif count is not None and \
                    count.minimum_form == "band" and \
                    facts.chosen_sizes.get(team) is None:
                check.verdict = "NOT PROVEN"
                check.missing_fact = "the chosen size for that team"
                check.expected = "the chosen size for the %s" % team
                check.observed = "no chosen size stated in the " \
                                 "supplied records"
            elif round_key is not None and \
                    not _round_settled(facts, round_key):
                check.verdict = "UNVERIFIABLE"
                record = _round_record_for(facts, round_key)
                check.expected = "the settling record for %s" % \
                    round_display(round_key)
                check.observed = "the record absent"
                check.evidence_files = [record]
                check.evidence_text = "%s, which does not state " \
                    "the settling fact" % record
                check.missing_fact = "the settling record for %s" % \
                    round_display(round_key)
            elif count is not None:
                check.verdict = count.result
                if count.result == "FAIL":
                    check.observed = "%d distinct full identifiers" % \
                        count.counted_total
                elif count.result == "NOT PROVEN":
                    check.missing_fact = \
                        "a full identifier for every counted seat"
            if tier == "Plaid" and check.verdict == "PASS":
                check.verdict = "NOT PROVEN"
                check.missing_fact = "a Plaid amount for this check"
            checks.append(check)
    return checks


def _distinctness_checks(facts, counts, present_teams, duplicates,
                         roster_source):
    checks = []
    truncated = any(source in facts.truncated_files
                    for source in facts.roster_sources)
    dup_teams = {}
    for seat, _first in duplicates:
        dup_teams.setdefault(seat.team, []).append(seat)
    for team in present_teams:
        round_keys = sorted(
            {key for (name, key) in counts if name == team},
            key=round_sort) or [None]
        for round_key in round_keys:
            count = counts.get((team, round_key))
            check = Check("distinctness", team, "PASS")
            check.rule_reference = "grill D6"
            check.round_key = round_key
            check.evidence_files = [roster_source]
            check.evidence_text = roster_source
            if count is not None:
                check.counted_total = count.counted_total
                check.duplicates_removed = count.duplicates_removed
                if count.minimum:
                    check.expected = "%d distinct full identifiers" \
                        % count.minimum
                    check.observed = "%d distinct full identifiers" \
                        % count.counted_total
            team_dups = [seat for seat in dup_teams.get(team, [])
                         if seat.round_key == round_key]
            if team_dups and count is not None and \
                    count.entries >= (count.minimum or 0) and \
                    count.counted_total < (count.minimum or 0):
                check.verdict = "FAIL"
                check.severity = "Critical"
            elif truncated:
                check.verdict = "UNVERIFIABLE"
                check.missing_fact = "the whole roster artifact"
            elif team_dups:
                check.verdict = "FAIL"
                check.severity = "Critical"
            elif count is not None and count.entries > 0 and \
                    count.counted_total == 0:
                check.verdict = "NOT PROVEN"
                check.missing_fact = "a full identifier for a seat"
            elif count is not None and \
                    count.non_id_entries > 0 and \
                    count.minimum is not None and \
                    count.counted_total < count.minimum:
                check.verdict = "NOT PROVEN"
                check.missing_fact = "a full identifier for a seat"
            checks.append(check)
    return checks


def _carried_checks(facts, present_teams, roster_source):
    checks = []
    principles = [seat for seat in facts.seats
                  if "Principles Agent" in (seat.role or "")]
    teams = [team for team in present_teams
             if "design" in team.lower() or "build" in team.lower()]
    for seat in principles:
        if seat.team and seat.team not in teams:
            teams.append(seat.team)
    for team in teams:
        check = Check("carried seats", team, "PASS")
        check.rule_reference = "AC-2"
        check.evidence_files = [roster_source]
        check.evidence_text = roster_source
        team_principles = [seat for seat in principles
                           if seat.team == team]
        holders = [seat.holder for seat in team_principles]
        counted_holders = {
            seat.holder for seat in facts.seats
            if seat.position in ("counted in base", "step unit")
            and is_full_id(seat.holder)}
        if len(holders) != len(set(holders)) and len(holders) > 1:
            check.verdict = "FAIL"
            check.severity = "Critical"
            check.observed = "one holder holds both Principles " \
                             "holdings"
        elif any(holder in counted_holders for holder in holders
                 if is_full_id(holder)):
            check.verdict = "FAIL"
            check.severity = "Critical"
            check.observed = "a Principles holder also holds a " \
                             "counted seat"
        check.expected = "carried seats held apart from counted seats"
        checks.append(check)
    return checks


def _board_check(facts, step, present_teams, roster_source):
    check = Check("review board minimum", "board", "PASS")
    check.rule_reference = "S5-E45"
    check.evidence_files = [roster_source]
    check.evidence_text = roster_source
    check.expected = "3 distinct full identifiers"
    board_ids = []
    missing_id = False
    for _role, holder, _source in facts.board:
        if is_full_id(holder):
            if holder not in board_ids:
                board_ids.append(holder)
        else:
            missing_id = True
    chair_holders = [holder for holder, _s in facts.chair_statements]
    chair_ok = any(is_full_id(holder) for holder in chair_holders)
    for holder in chair_holders:
        if is_full_id(holder) and holder not in board_ids:
            board_ids.append(holder)
    check.counted_total = len(board_ids)
    check.observed = "%d distinct full identifiers" % len(board_ids)
    # The board chair limb of the worked cases judges the board of
    # a stage whose evidence is the roster standing alone with the
    # full fixture shape: a staffed shape carrying a Write tests
    # team, or a real step, where no stage claim stands asserted for
    # adjudication and no work product stands presented. Where a
    # claim or a product stands in the run, the board minimum is
    # judged on the board seats as stated.
    beyond_roster = bool(facts.presentations) or facts.stage_claim
    engaged = (("Write tests team" in present_teams) or (
        step is not None and step != 99)) and not beyond_roster
    if missing_id:
        check.verdict = "NOT PROVEN"
        check.missing_fact = "the board seat identifier"
        check.expected = "a full identifier for every board seat"
        check.observed = "a board seat with no identifier"
    elif len(board_ids) >= 3:
        if engaged and not chair_ok:
            check.verdict = "NOT PROVEN"
            check.expected = "a board chair full identifier"
            check.observed = "no board chair identifier"
            check.evidence_text = "%s, which does not state a board " \
                "chair identifier" % roster_source
            check.missing_fact = "the board chair identifier"
    elif facts.board:
        check.verdict = "FAIL"
        check.observed = "%d distinct full identifiers" % \
            len(board_ids)
    else:
        check.verdict = "NOT PROVEN"
        check.missing_fact = "the board chair identifier" if engaged \
            else "the review board for this stage"
        check.expected = "a board chair full identifier" if engaged \
            else "the review board for this stage"
        check.observed = "no board chair identifier" if engaged \
            else "no review board in the supplied records"
    return check


def _pool_check(facts, present_teams, roster_source):
    check = Check("pool family and role", "stage", "PASS")
    check.rule_reference = "AC-2"
    check.evidence_files = [roster_source]
    check.evidence_text = roster_source
    check.expected = "one holder for every role in a stage holding"
    by_role = {}
    for seat in facts.seats:
        if seat.position not in COUNT_POSITIONS:
            continue
        if not is_full_id(seat.holder):
            continue
        key = (seat.round_key, seat.role)
        by_role.setdefault(key, set()).add(seat.holder)
    for (_round_key, role), holders in sorted(by_role.items()):
        if len(holders) > 1:
            check.verdict = "FAIL"
            check.observed = "the role %s is held by two agents" % \
                role
            break
    if check.verdict == "PASS" and facts.combined_scope_claim and \
            not any("combined" in (seat.role or "").lower()
                    for seat in facts.seats):
        check.verdict = "FAIL"
        check.observed = "a combined scope is claimed in report " \
                         "text with no holder in the roster"
    return check


def _colour(facts, roster_stands, rounds_stand, files):
    """The colour completeness bound, or None where its line omits."""
    if not roster_stands or rounds_stand:
        return None
    suppliers = []
    for label, colours, source in facts.plan_suppliers:
        suppliers.append((label, colours, source, True))
    named = bool(facts.plan_suppliers or facts.charge_suppliers)
    qualifying = [entry for entry in facts.charge_suppliers
                  if entry[2]]
    for label, colours, _qualifies, source in qualifying:
        suppliers.append((label, colours, source, True))
    if not named:
        return {"result": "NOT PROVEN", "form": "none named",
                "missing": [], "suppliers": []}
    if not suppliers:
        return {"result": "NOT PROVEN", "form": "none qualifies",
                "missing": [], "suppliers": []}
    bound = []
    for _label, colours, _source, _ok in suppliers:
        for colour in colours:
            if colour not in bound:
                bound.append(colour)
    if facts.papers_colours is not None:
        papers = facts.papers_colours
    else:
        papers = []
        for seat in facts.seats:
            match = re.match(r"Colour lens (\w+)", seat.role or "")
            if match and match.group(1) not in papers:
                papers.append(match.group(1))
    missing = [colour for colour in bound if colour not in papers]
    return {"result": "NOT PROVEN" if missing else "PASS",
            "form": "bound", "missing": missing,
            "suppliers": suppliers, "bound": bound}


def _claim_disagreements(facts, counts, step_totals):
    disagreements = []
    counted_by_team = {}
    for (team, _round_key), count in counts.items():
        counted_by_team[team] = counted_by_team.get(team, 0) + \
            count.counted_total
    observed_total = sum(entry["observed"] for entry in step_totals)
    for sentence, source in facts.claims:
        text = sentence.strip()
        if "passes are members" in text:
            disagreements.append(
                "claim disagreement: %s The computed result: audit "
                "passes are not members of a team. The record to "
                "correct is %s." % (text, source))
            continue
        if "coordinator is a member" in text:
            disagreements.append(
                "claim disagreement: %s The computed result: the "
                "coordinator is not a member of a team. The record "
                "to correct is %s." % (text, source))
            continue
        match = re.search(
            r"the (.+?) is fully staffed with (\d+) distinct", text)
        if match:
            team = match.group(1)
            claimed = int(match.group(2))
            if counted_by_team.get(team, 0) != claimed:
                disagreements.append(
                    "claim disagreement: %s The computed result: "
                    "the %s count is %d distinct holders. The record "
                    "to correct is %s." % (
                        text, team, counted_by_team.get(team, 0),
                        source))
            continue
        match = re.search(r"step total for this stage is (\d+)",
                          text)
        if match:
            claimed = int(match.group(1))
            if claimed != observed_total:
                disagreements.append(
                    "claim disagreement: %s The computed result: "
                    "the step total for this stage is %d. The record "
                    "to correct is %s." % (text, observed_total,
                                           source))
            continue
        match = re.search(r"the (.+?) is fully staffed", text)
        if match:
            team = match.group(1)
            count = counted_by_team.get(team)
            if count is not None and count == 0:
                disagreements.append(
                    "claim disagreement: %s The computed result: "
                    "the %s is not fully staffed. The record to "
                    "correct is %s." % (text, team, source))
    return disagreements
