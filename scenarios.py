"""
The runs your test needs. ← UNIT 4, MILESTONE 3

Each of your five criteria needs something run against it. A criterion about
the empty-search branch needs an impossible query. One about the fit card needs
the same item run more than once. Working that out is Milestone 3's first step,
and this file is where you write it down.

`run_eval.py` runs everything here five times and writes the run log — five
because your criteria are written out of five.

Three scenarios are filled in to show the shape. Add or change whatever your
own criteria need — these are a starting point, not a fixed set.
"""

SCENARIOS = [
    {
        # A query the data can match. Criterion 1.
        "name": "matching query completes",
        "query": "vintage graphic tee under $30",
        "wardrobe": "example",
        "criterion": 1,
    },
    {
        # A query nothing can match. Criterion 2 — the branch.
        "name": "impossible query stops early",
        "query": "designer ballgown size XXS under $5",
        "wardrobe": "example",
        "criterion": 2,
    },
    {
        # Any normal matching query — criterion 3 checks what ends up in the
        # session (selected_item's id vs. what suggest_outfit's trace shows),
        # not anything about this query in particular. Matches lst_005 and
        # lst_025, both under $40.
        "name": "state: selected item matches what reaches suggest_outfit",
        "query": "wide-leg pants under $40",
        "wardrobe": "example",
        "criterion": 3,
    },
    {
        # Same query every try. run_eval.py already runs each scenario 5
        # times, so one entry here gives 5 fit cards for the same item —
        # exactly what criterion 4 needs to check for shape (2-4 sentences,
        # price mentioned once) and variation (no two identical).
        "name": "fit card: same query, five tries",
        "query": "90s track jacket with navy and white stripes",
        "wardrobe": "example",
        "criterion": 4,
    }, 
    {
        # "under $25" should hold as a hard ceiling. Matches 8 listings,
        # topped by lst_003 ($22) — plenty to check, not just one.
        "name": "price ceiling respected",
        "query": "Oversized Flannel Shirt Plaid Red/Black under $25",
        "wardrobe": "example",
        "criterion": 5,
    },
    {
        # A user with nothing saved. One of unit 4's three failure modes.
        "name": "empty wardrobe",
        "query": "denim jacket under $50",
        "wardrobe": "empty",
        "criterion": None,
    },
]

WARDROBES = ("example", "empty")


def validate() -> list[str]:
    """Complain about anything malformed, before a long run rather than during."""
    problems = []
    for i, scenario in enumerate(SCENARIOS, 1):
        if not scenario.get("query", "").strip():
            problems.append(f"scenario {i} has no query")
        if scenario.get("wardrobe") not in WARDROBES:
            problems.append(
                f"scenario {i} has wardrobe {scenario.get('wardrobe')!r} — "
                f"it should be one of {WARDROBES}"
            )
    return problems
