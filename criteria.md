# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools 

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:** `search_listings` scores items by exact token overlap
between the query and the listing's title/description/category/style_tags/
brand — there's no synonym handling and no fuzzy matching. A phrasing that
doesn't share a word with the listing data (e.g. "jumper" for what the data
calls a "sweater") scores zero and the branch correctly reports no match. That
isn't a bug in the loop, it's a limit of a keyword search, so I don't expect
5 of 5 on phrasing I haven't controlled for.

---

## 2. An impossible query stops before the second tool 

Given a query that matches no listings, the agent stops before calling 
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:** This branch is a plain `if not results:` check in
`run_agent()` — no model call, no randomness, nothing that can come back
different on two runs of the same input. Criterion 1 can miss because keyword
matching is fuzzy by nature; this one can't, because an empty list is either
empty or it isn't. If this ever comes back less than 5 of 5, the bug is in the
branch itself, not in the data.

---

## 3. Something about state

Given a query that matches at least one listing, the listing `id` recorded in
`session["selected_item"]` is the same `id` that appears in the trace's
`suggest_outfit` input — in 5 of 5 tries.

**Why this target:** This isn't testing the model — it's testing that
`run_agent()` hands the same dict forward instead of re-searching, re-sorting,
or rebuilding it between steps. That's one variable assignment and one
function call, both deterministic Python, so there's no source of variation
between tries. A pass rate under 5 of 5 here would mean state is leaking
between tools — e.g. `suggest_outfit` getting results[0] fresh instead of the
`selected_item` that was actually chosen — which looks like a tool bug from
the output alone and only shows up by checking the trace against the session.

---

## 4. Something about the fit card

Given the same matching query run 5 times, each fit card is 2–4 sentences,
mentions the item's price as a dollar figure exactly once, and no two of the
five cards are word-for-word identical — in at least 4 of 5 tries.

**Why this target:** The fit-card prompt explicitly instructs the model to
mention the price once and keep to 2–4 sentences, and `TEMPERATURE = 0.9` is
set specifically so the wording isn't the same from one run to the next. The
wording is allowed — expected — to differ every time; what I'd actually be unhappy to see
is a card that drops the price, runs long, or comes back identical to the
last one (which would mean the cache is on or the temperature got reset,
not that the model is being creative). I'm not requiring 5 of 5 because at
temperature 0.9 an instruction-following model will occasionally skip a
formatting instruction even when the prompt states it plainly — that's the
cost of asking for variation rather than a fixed template.

---

## 5. Your choice 

Given a query containing "under $X", every listing in
`session["search_results"]` has `price <= X` — in 5 of 5 tries.

**Why this target:** The price ceiling in `search_listings` is a single
`item["price"] <= max_price` filter applied before any scoring happens — plain
arithmetic on data that doesn't change between runs. There's no model
involved and no ambiguity in what "under $X" should mean once it's parsed, so
I care about this being exactly right every time: a search that quietly lets
a $45 item through a "$40" filter is worse than one that returns nothing,
because it looks like it worked. If this misses, the bug is in the regex
parsing the ceiling out of the query, not in the filter.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share 
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
