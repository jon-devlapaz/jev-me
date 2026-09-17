---
name: jev-me
description: >
  Grill the user on a plan or design with Jev weighing every frontier
  question, recommendation, answer, and close. Use when the user types
  /jev-me.
disable-model-invocation: true
---

# Jev-Me

A grilling interview with Jev on the control points: which questions
earn a round, which recommendation leads, whether an answer settles its
branch, and when the session ends. You type `/jev-me` to start; the
agent never fires this on its own.

The user is a **person**. The job is **useful determinism in planning
and interviewing**, not a general LLM harness and not an autonomous
planner. The unreliable party is the interviewing LLM: overconfident
and jagged. Jev pins that interviewer — calibrated typed judgments the
LLM is not allowed to skip, round, or overwrite with vibes.

**Requires:** a working Jev client. For SDK setup, auth, and
question-shaping, use the `typesafe-ai` skill. Keep `TYPESAFE_API_KEY`
in the environment; never put it in state, questions, or the log.

Jev returns typed answers. Compose them in this skill's rules — do not
ask Jev "what should we do next" as one blob. A Noul near 0.5 is *I
don't know*, not a medium amount of anything. Use Score when the answer
is a position on named situations. Agent drafts questions and rec
options; Jev judges; the user decides. Confirmation never authorizes
implementation.

## Thresholds

| Gate | Rule |
| --- | --- |
| Prune | load-bearing Noul `< 0.3` (keep listed, marked pruned) |
| Uncertain band | Noul `0.3–0.7` — keep, flag, do not auto-act |
| Hold | independent Noul `< 0.4` |
| Fact | is_fact Noul `> 0.6` — look it up, do not ask |
| Rec lead | Choice confidence `≥ 0.6`; else show the top two probabilities, no winner |
| Reopen | `reopened_call` is a **decision** id, not a looked-up fact, **and** Choice confidence `≥ 0.6` |
| Settle | decided Score `≥ 1.5` **and** nods_along `< 0.6` |
| Assumed reopen | still_material Noul `> 0.6` |
| Deliver log | diminishing-returns Score `≥ 1.5` and no assumed reopen |
| Round cap | ask at most **4** survivors, highest rank first |
| Rank | `load_bearing` only. If two scores differ by `< 0.05`, prefer higher `irreversible` |
| Irreversible flag | show on the question when irreversible Noul `> 0.6`; never mix into rank |

Unsettled answers, pushbacks, and reframes stay on the pool. Close only
when nothing askable remains.

## Control flow

```
0 Open
loop:
  1 Weigh the pool (one Jev call)
  if no askable survivors and nothing unsettled → 4
  2 Ask the top-K round; wait
  3 Weigh answers (one Jev call); grow children; recompute pool
4 Close (one Jev call); may reopen into the loop
```

## 0. Open

Probe the client with one trivial Noul over a sentence of the subject.
If auth fails, stop and tell the user to set `TYPESAFE_API_KEY` — never
ask them to paste the key.

Frame the subject as a **design tree**. Seed **6–8** candidate questions
that span planning axes, not one pocket: objective, constraints,
alternatives, sequencing, irreversible calls, risks, what would reopen.
Multiple choice only when the live alternatives are already known
(settled state or the user's wording); otherwise open. Facts are yours
to look up. The interviewing LLM does not invent a menu to look sure.

**Done when:** the client answers and the pool has a first set of
candidates.

## 1. Weigh the pool (one Jev call)

The **pool** is every decision whose prerequisites are already settled.
Draft 2–4 rec options per question, always including a `neither` /
reframe option. Fan out every judgment below in **one** call. Point
instructions at backticked paths. Consume only what code needs.

```json
{
  "state": {
    "subject": "Migrate checkout sessions to Redis",
    "facts": ["Render already hosts the app"],
    "settled": ["Stays on Render", "Budget $100/mo"],
    "candidates": [{"id": "q1", "text": "Sync or async session writes?"}],
    "rec_candidates": {
      "q1": ["Sync: simpler crash story", "Async: protects p99"]
    }
  },
  "questions": {
    "q1_load_bearing": {
      "type": "noul",
      "instructions": "Does the answer to `candidates[0]` change what gets built, sequenced, or ruled out for `subject`, given `settled`?",
      "criteria": {
        "true": "Changing this answer changes the outcome or kills a live path",
        "false": "Local, reversible, or already implied by `settled`"
      }
    },
    "q1_independent": {
      "type": "noul",
      "instructions": "Can `candidates[0]` be answered honestly without knowing the other open candidates?"
    },
    "q1_is_fact": {
      "type": "noul",
      "instructions": "Can filesystem, repo, docs, or a lookup settle `candidates[0]` without a preference?"
    },
    "q1_irreversible": {
      "type": "noul",
      "instructions": "Would answering `candidates[0]` now lock out a live alternative that is expensive to restore?"
    },
    "q1_rec_pick": {
      "type": "choice",
      "instructions": "Given `subject` and `settled`, which recommendation in `rec_candidates.q1` leads best?",
      "criteria": {
        "sync": "Sync: simpler crash story",
        "async": "Async: protects p99",
        "neither": "Neither fits; the question needs reframing"
      }
    }
  }
}
```

Then in code, per candidate:

1. `is_fact > 0.6` → look it up or dispatch a subagent; put the result in
   `facts`, tell the user, do not ask. Facts never become reopen targets.
2. independent `< 0.4` → hold for a later round.
3. load-bearing `< 0.3` → prune (stay listed).
4. `rec_pick == neither` → reframe the question; re-weigh next loop, do
   not ask this wording.
5. Else it is a survivor. Rank it. Load-bearing in the uncertain band
   stays, flagged.

Read `choice`, `confidence`, **and** `probabilities` on every rec.
A `neither` pick is a rewrite, not a skip of the branch.

**Done when:** survivors are ranked and the round's top K are chosen, or
the pool has nothing askable.

## 2. Ask the round

Ask at most 4 survivors. Number them. Put Jev's rec on the ➡️ line.
Below 0.6 confidence, do not pretend there is a winner. Flag
irreversible Noul `> 0.6` on the question, not in the rank.

```
❓ **Q1** - **<title>**: <body, including choices>

➡️ <pick> (confidence 0.82)

---

❓ **Q2** - **<title>**: <body, including choices>

➡️ uncertain: <A> 0.52 / <B> 0.45 — flagged, pick is not a lead
```

Answer none of your own questions. Wait for answers to the numbered
questions. "Looks good", "lgtm", "sounds right", or praise of the
method is not an answer.

**Done when:** the round is asked in shape and every answer is heard.

## 3. Weigh the answers (one Jev call)

Before the tree updates:

```json
{
  "state": {
    "subject": "Migrate checkout sessions to Redis",
    "facts": ["Render already hosts the app"],
    "settled": ["Stays on Render"],
    "question": {"id": "q1", "text": "Sync or async session writes?"},
    "rec": {"pick": "sync", "confidence": 0.82},
    "answer": "Async. p99 matters more than crash story.",
    "settled_ids": ["hosting"]
  },
  "questions": {
    "q1_decided": {
      "type": "score",
      "instructions": "How settled is `answer` as a decision on `question`, given `settled`?",
      "criteria": [
        "Vague, hedged, or nodded along with `rec` without adding a constraint",
        "Answered with a reservation a stranger could still misread",
        "Settled; a stranger could defend this call from the log alone"
      ]
    },
    "q1_nods_along": {
      "type": "noul",
      "instructions": "Does `answer` merely agree with `rec` without adding a constraint or a reason?"
    },
    "q1_reopened_call": {
      "type": "choice",
      "instructions": "Which already-settled call does `answer` reopen?",
      "criteria": {
        "hosting": "Stays on Render",
        "none": "No earlier settled call is reopened"
      }
    }
  }
}
```

Fan out one triplet per answer in the same call. `reopened_call`
criteria are **settled decision ids** plus `none` — never `facts`.

A single utterance that agrees with the round without restating each
call ("looks good") is nods-along for **every** question in that round.
Weigh it; do not settle any of them.

- Decided Score `< 1.5` **or** nods_along `> 0.6` → pushback, quote the
  **level** and confidence, keep it on the pool: "Jev places that at
  nodded along (0.1, confidence 0.9) — what would make it defensible to
  a stranger?"
- `reopened_call` is a decision id **and** that Choice confidence `≥ 0.6`
  → that settled branch returns to the pool. A hit on a fact, or
  confidence `< 0.6`, is not a reopen.
- Otherwise settle, unblock what hung off it, and grow the tree: extract
  branches the **answer already named**, then invent **at most 2** extra
  candidates. Nothing newly grown is asked until it survives the next
  weigh. Do not freeze the tree at the Open seed; do not let the
  interviewing LLM smuggle unweighed questions into the round.

**Done when:** every answer is scored, the pool reflects settled,
pushed-back, reopened, and newly grown questions.

## 4. Close

The session ends on shared understanding, not an empty pool. Enter close
when nothing askable remains (no survivors, no unsettled, no unblocked
held). One fan-out over the settled tree and the prune list:

- `still_material` — Noul **per pruned id**: "Is `pruned[i]` still a
  material silent assumption given `settled`?"
- `diminishing_returns` — Score: another round would reveal a material
  call / remaining questions are polish / further rounds cost more
  attention than they reveal.
- `which_assumption` — Choice over pruned ids plus `none`.

Any `still_material > 0.6` reopens that branch into the loop. Else if
diminishing-returns `≥ 1.5`, deliver the log. Else ask whether to
continue or close.

The log: each settled call with rec pick, confidence, and probability
split if it was close; each pushback and how it resolved; pruned
branches with their load-bearing Nouls; what would reopen each call.
End only when the user confirms shared understanding.

If the user exits mid-session, stop. Unsettled stays unsettled. Do not
write a log that treats nods as calls.

**Done when:** the log is delivered and understanding is confirmed.

## Sources

Interview mechanics adapted from `grilling` / `grill-me`
(mattpocock/skills). Jev mechanics: `typesafe-ai` skill and TypeSafe
docs. Design debts: OntoAgent (what-to-ask decoupled from how-to-ask);
Mediating Assessments Protocol (independent judgments, global evaluation
delayed to the close); cognitive forcing functions (uncertainty display
plus selective forcing); Bayesian adaptive querying (ask for expected
information gain; cap the user round, weigh a larger pool).
