# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

<!-- Three or four sentences: what a user asks for, and what they get back. -->



---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:** Searches the mock listings dataset for items matching a text description, optionally filtered by size and a maximum price.
- **Inputs:** `description` (str) — free-text keywords matched against each listing's title, description, category, style tags, and brand. `size` (str | None) — a size string filtered by exact token match (not substring), or `None` to skip size filtering. `max_price` (float | None) — the highest acceptable price, inclusive, or `None` to skip price filtering.
- **Returns:** A list of listing dicts, best match first — each with `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, `platform`. Sorted by keyword-overlap score with `description`, capped at `config.SEARCH_RESULT_LIMIT`.
- **When it has nothing:** Returns an empty list — never `None`, never an exception.

### `suggest_outfit`

- **What it does:** Calls the model to suggest one or two outfits pairing a candidate thrifted item with the user's existing wardrobe.
- **Inputs:** `new_item` (dict) — a listing dict for the item being considered. `wardrobe` (dict) — a wardrobe dict with an `items` key holding a list of wardrobe item dicts (`name`, `category`, `colors`, `style_tags`).
- **Returns:** A non-empty string of outfit suggestions, naming specific wardrobe pieces by name when the wardrobe isn't empty.
- **When it has nothing:** If `wardrobe['items']` is empty, it still returns a non-empty string — general styling advice for the item instead of wardrobe-specific pairings. It never returns `""`.

### `create_fit_card`

- **What it does:** Calls the model to write a short caption for a thrifted find, based on an outfit suggestion and the item's details.
- **Inputs:** `outfit` (str) — the outfit suggestion string returned by `suggest_outfit()`. `new_item` (dict) — the listing dict for the item.
- **Returns:** A two-to-four sentence caption string that mentions the item, price, and platform exactly once each.
- **When it has nothing:** If `outfit` is empty or whitespace-only, returns a descriptive placeholder string naming the item and price and saying no outfit suggestion exists yet — it never raises.

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:** If `search_listings` returns an empty list, put a message in `session["error"]` naming what to change (broader description, higher price ceiling, different size) and stop — `suggest_outfit` and `create_fit_card` are never called. Otherwise, take the first result as `session["selected_item"]` and continue to `suggest_outfit`, then `create_fit_card`.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** Regex. `_parse_query()` in `agent.py` pulls a price ceiling from an `"under $X"` pattern and a size from a `"size X"` pattern, removes both from the string, and treats what's left as the description.

**What moves through the session:** `query` → `parsed` (`description`, `size`, `max_price`) → `search_results` → `selected_item` (first result) → `outfit_suggestion` → `fit_card`. `error` is set only on the empty-search branch, and when it is, everything after `search_results` stays `None`.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask 'vintage graphic tee under $30'

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   **Outfit 1: Y2K Streetwear**
*   **New:** Y2K Butterfly Baby Tee
*   **Bottoms:** Baggy straight-leg dark wash jeans
*   **Outerwear:** Black cropped zip hoodie (worn unzipped)
*   **Shoes:** Chunky white sneakers
*   **Accessories:** Black crossbody bag

**Outfit 2: Soft Contrast**
*   **New:** Y2K Butterfly Baby Tee
*   **Bottoms:** Wide-leg khaki trousers
*   **Belt:** Brown leather belt (threaded through the trousers)
*   **Shoes:** Chunky white sneakers
*   **Outerwear:** Vintage black denim jacket

  Fit card: Found this exact pink and purple butterfly baby tee scrolling through depop last week and I'm obsessed with the early 2000s mall-goth energy. It was only $18.0 and looks so good styled with baggy dark wash denim and chunky sneakers. Total nostalgic score for your summer rotation.
```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
[{'id': 'lst_002', 'title': 'Y2K Baby Tee — Butterfly Print', 'price': 18.0, 'platform': 'depop', ...}, {'id': 'lst_006', 'title': 'Graphic Tee — 2003 Tour Bootleg Style', 'price': 24.0, 'platform': 'depop', ...}, {'id': 'lst_017', 'title': 'Mesh Long-Sleeve Top — Black', 'price': 15.0, 'platform': 'depop', ...}, {'id': 'lst_033', 'title': 'Vintage Band Tee — Faded Grey', 'price': 19.0, 'platform': 'depop', ...}, {'id': 'lst_011', 'title': 'Low-Rise Cargo Pants — Khaki', 'price': 27.0, 'platform': 'poshmark', ...}, {'id': 'lst_015', 'title': 'Vintage Graphic Hoodie — Faded Black', 'price': 26.0, 'platform': 'depop', ...}]
```

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
**Fit 1: Off-Duty Streetwear**
*   **Top:** White ribbed tank top
*   **Outerwear:** Vintage black denim jacket
*   **Shoes:** Chunky white sneakers
*   **Accessories:** Black crossbody bag + Brown leather belt

**Fit 2: Cozy Casual**
*   **Top:** Oversized grey crewneck sweatshirt
*   **Shoes:** Black combat boots
*   **Accessories:** Brown leather belt
```

```
$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
Found these vintage Levi's 501 jeans and they have that perfectly broken-in indigo wash you can never actually replicate. They just hit Depop for $38 and are begging to be worn with crisp white sneakers and an oversized tee. Truly the ultimate lazy-day streetwear uniform.
```

**Checking the fit card actually varies** — ran `create_fit_card` three times on the same item with `AI201_CACHE=0` (caching off, so three real calls):

```
--- run 1 ---
Finally found the holy grail of vintage Levi's 501 jeans with that perfectly broken-in indigo wash. Threw them up on depop for just $38.0 so someone else can rock the ultimate streetwear staple with fresh white sneakers. The slouchy fit on these is an absolute dream and they've got so much life left.
--- run 2 ---
Still recovering from finding these vintage Levi's 501 jeans in the absolute best medium wash. They give off major off-duty model energy when you pair them with beat-up white sneakers and an oversized tee. Snagged them on depop for just $38.0 and I honestly might never wear another pair of pants again.
--- run 3 ---
Found these broken-in vintage Levi's 501s and they literally fit like a glove. Throwing them on with crisp white sneakers for that effortless 90s streetwear look. Just posted these indigo beauties to my depop for $38 before I change my mind.
```

Three different captions — `TEMPERATURE = 0.9` in `config.py` is doing its job, not returning a cached answer.

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:*
- *What came back:*
- *What I changed:*

**Moment 2**

- *What I asked for:*
- *What came back:*
- *What I changed:*

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Matching query completes | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. Impossible query stops early | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. State: selected item matches what reaches `suggest_outfit` | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit card: 2-4 sentences, price once, no duplicates | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. Price ceiling respected | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| _diagnostic — empty wardrobe (not one of the five)_ |  | PASS | PASS | PASS | PASS | PASS |  |

Full output for every try is in `results/run_2026-10-04_1632.md` (produced by
`python run_eval.py --label before`, caching off, temperature 0.9).

**Real output from one try**, pasted as text, from `agent.py::run_agent`
(criterion 1, "matching query completes", try 1):

```
$ python app.py ask 'vintage graphic tee under $30' --trace

[1] parse_query
      in:  vintage graphic tee under $30
      out: dict with keys: description, size, max_price
[2] search_listings
      in:  dict with keys: description, size, max_price
      out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
[3] suggest_outfit
      in:  Y2K Baby Tee — Butterfly Print ($18.0, depop)
      out: **Outfit 1: Y2K Off-Duty** *   **Top:** Y2K Butterfly Baby Tee *   **Bottoms:** Baggy straight-leg dark wash j…
[4] create_fit_card
      in:  **Outfit 1: Y2K Off-Duty** *   **Top:** Y2K Butterfly Baby Tee *   **Bottoms:** Baggy straight-leg dark wash j…
      out: Just scored this dreamy white, pink, and purple butterfly tee and I'm obsessed with the early 2000s energy. I’…

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop
  Outfit:   **Outfit 1: Y2K Off-Duty** ... (full text in results/run_2026-10-04_1632.md)
  Fit card: Just scored this dreamy white, pink, and purple butterfly tee and I'm obsessed with the early 2000s energy. I’m styling it with baggy dark wash denim and chunky sneakers for an effortless off-duty look. Snagged it on depop for just $18.0 and honestly, it’s my new favorite piece for spring.
```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 | Matching query completes all three tools | 4 of 5 | MET (5/5) | All 5 tries had `stopped early: no`, a non-empty `outfit_suggestion`, and a non-empty `fit_card` — read straight off `results/run_2026-10-04_1632.md`. |
| 2 | Impossible query stops before `suggest_outfit` | 5 of 5 | MET (5/5) | All 5 traces end at `[3] branch` with "no results, stopping before suggest_outfit"; no `suggest_outfit`/`create_fit_card` step ever appears. |
| 3 | State: selected item matches what reaches `suggest_outfit` | 5 of 5 | MET (5/5) | In every try, `search_listings`'s top result and `suggest_outfit`'s `in:` line both name "Corduroy Wide-Leg Pants — Rust ($32.0, depop)" — same title/price/platform every time. |
| 4 | Fit card: 2-4 sentences, price mentioned once, no duplicates | 4 of 5 | MET (5/5) | All 5 cards are 2-3 sentences, each mentions the price exactly once (`$45`/`$45.0`), and none of the 5 are word-for-word identical. |
| 5 | Price ceiling respected | 5 of 5 | MET (5/5) | All 8 results returned for "under $25" are ≤ $25 in every one of the 5 tries (cheapest $14, priciest $22). `search_listings` has no randomness, so this held identically every try. |

**Diagnoses**

No misses this round — all five criteria cleared their targets on the first real run. Two things worth flagging that aren't misses but are worth tracking:

- **Price formatting is inconsistent.** Some fit cards say `$45` and others say `$45.0` or `$18.0` — that's `str(float)` leaking through from `new_item['price']` into the prompt in `tools.py`'s `create_fit_card()`, not the model's choice. Criterion 4 only asked for "a dollar figure," which this still satisfies, but it reads oddly in a caption meant to sound like a real post.
- **Criterion 1's target (4/5) never got exercised.** Because `search_listings` has no randomness and the eval reruns the same query 5 times, the only way this run could have come in under 5/5 is a model-side hiccup in `suggest_outfit`/`create_fit_card` (now caught by the `ModelUnavailable` handling in `agent.py`). The 4/5 target was really written for phrasing variance across *different* queries, which this scenario design doesn't test. Worth a second scenario with a weaker-match query if I want to actually probe that target.

---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
