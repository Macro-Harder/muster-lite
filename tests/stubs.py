"""Composition stub families, test side machinery only, under plan D-02.

One stub per composing family, each returning fixed words set by the test.
The stubs stand only inside this test suite. The shipped core will contain
no stub, and no stub in this file stands in any product path. The stub word
set carries every result word a composing family can return, and, as exit
outcomes, the usage error outcome (the words USAGE ERROR at exit code 5)
and the tool fault outcome (the words TOOL FAULT at exit code 6).
"""

WORDS = ("PASS", "FAIL", "NOT PROVEN", "UNVERIFIABLE")
LADDER = ("FAIL", "UNVERIFIABLE", "NOT PROVEN", "PASS")

COMPOSING_FAMILIES = (
    "team minimums",
    "distinctness",
    "carried seats",
    "review board minimum",
    "artefact linkage",
    "claimed freshness",
)

EXIT_OUTCOMES = (
    ("PASS", 0),
    ("FAIL", 1),
    ("NOT PROVEN", 2),
    ("UNVERIFIABLE", 3),
    ("USAGE ERROR", 5),
    ("TOOL FAULT", 6),
)


class StubFamily:
    """One stub per composing family, returning one fixed word."""

    def __init__(self, family, word):
        if word not in WORDS:
            raise ValueError("stub word outside the four word vocabulary")
        self.family = family
        self.word = word

    def result(self):
        return self.word


def stub_set(words_by_family):
    return [StubFamily(family, words_by_family[family])
            for family in COMPOSING_FAMILIES]


def uniform_stub_set(word):
    return stub_set({family: word for family in COMPOSING_FAMILIES})


def compose_stub_words(words):
    """The ladder over stub words, FAIL first, as brief section 5.6 states.

    This is a test side expectation function. It states what the product
    core must compute; it is not product code and stands in no product path.
    """
    for word in LADDER:
        if word in words:
            return word
    return "PASS"
