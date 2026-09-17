---
name: jev-me
description: >
  Interviews the user about a plan or a design. Jev scores each
  question, each recommended answer, each user answer, and the close.
  Decisions are written to a sqlite audit in this skill folder.
  Use when the user types /jev-me or asks to grill a plan.
disable-model-invocation: true
---

# Jev-Me

This skill runs an interview about a plan or a design. **Jev** scores
each control point. You type `/jev-me` to start. The agent does not
start the skill by itself.

The user is a **person**. The job is a plan from an interview with
results that you can predict. A confirmed log is not a license to
implement.

**Requires:** `TYPESAFE_API_KEY` in the environment, and the
`typesafe-ai` skill for how to call Jev. Do not put the key in state,
questions, chat, or the audit. If auth fails, stop and tell the user
to set `TYPESAFE_API_KEY` — never ask them to paste the key. If
`typesafe-ai` is missing, stop and tell them to install it. Call Jev
with `uv run --with typesafe-sdk python` so nothing is installed into
this skill folder or the user's project.

Three parts, one job:

| Part | Owns |
| --- | --- |
| Jev | Typed scores |
| This skill | Which questions to send Jev, and how to combine the scores |
| `audit/jev-me.sqlite` | What happened, in order |

You write the questions and recommended options. Jev scores. You apply
the table below. The user decides. **Do not skip a Jev call. Do not skip
an audit write. Do not invent a gate Jev did not return.**

`WRITER` is `audit/write.py` next to this `SKILL.md`. Always call it
with that absolute path. It finds the database from its own location.
Do not `cd`. Do not copy the script. Do not write `event.json` or any
other file into the user's project.

## What the person sees

The person never sees session ids, sqlite paths, Noul/Score names, raw
JSON, or `write.py` output except the human log at close. Keep those
for yourself.

If they typed `/jev-me` with no subject, ask **What should we decide?**
and wait. Do not probe Jev and do not seed questions until they name it.

If `list --status open` shows an unfinished interview, do **not** start
a second one. Ask, then wait:

```
You already have an unfinished interview: "<subject>". Resume that, or
start a new one?
```

Except for a missing subject, an auth failure, or a resume prompt, do
not send a user-visible message until the first numbered round is
ready. Probe, start, and weigh silently.

First user-visible turn after a named subject (one message, then wait):

```
I'll ask a few questions that change the plan. Answer in your own words —
"looks good" is not an answer. When we stop, confirming the log is not
a license to build.

❓ **Q1** - ...
```

Pushback in ordinary words, with the numbers in parentheses:

```
That still leaves the call open (0.4, confidence 0.71): the answer
agreed without adding a constraint. What would you actually lock in?
```

Do not quote Jev level names. Do not answer your own questions.
"Looks good", "lgtm", "sounds right", or praise of the method is not
an answer.

## Audit

```
python3 /absolute/path/to/this-skill/audit/write.py start --subject "<subject>"
python3 /absolute/path/to/this-skill/audit/write.py list --status open
python3 /absolute/path/to/this-skill/audit/write.py event --session <id> --phase <phase> --kind <kind> [--candidate <qid>] --json '{...}'
python3 /absolute/path/to/this-skill/audit/write.py status --session <id> --to closed
python3 /absolute/path/to/this-skill/audit/write.py log --session <id>
```

`phase`: `open` `weigh_pool` `ask` `weigh_answers` `close` `confirm` `abandon`.
`kind`: `jev_call` `gate` `utterance` `fact` `note`.

Payloads the close log reads. `write.py` does not validate them; keep
them in this shape so the log stays human.

| kind | payload |
| --- | --- |
| `jev_call` | `{state, questions, answers, model}` — stored, not shown |
| `gate` | `{id, gate, title, answer?, reason?, scores}` |
| `utterance` | `{text}` |
| `fact` | `{text}` plus optional `title` |
| `note` | `{text}` or `{asked: ["q1"]}` |

`gate` values: `prune` `hold` `fact` `survivor` `reframe` `settle`
`pushback` `reopen`.

After every Jev response, write `kind=jev_call`. After every gate, write
`kind=gate`. After every user reply, write `kind=utterance`.

## Thresholds

| Gate | Rule |
| --- | --- |
| Prune | nearest `ask_value` level is 0 **and** confidence `≥ 0.6` |
| Uncertain flag | `ask_value` confidence `< 0.6` — keep, flag, do not auto-prune |
| Hold | independent Noul `< 0.4` |
| Fact | is_fact Noul `> 0.6` — look it up, do not ask |
| Rec lead | Choice confidence `≥ 0.6`; else show the top two probabilities, no winner |
| Reopen | `reopened_call` is a **decision** id, not a looked-up fact, **and** Choice confidence `≥ 0.6` |
| Settle | decided Score `≥ 1.5` **and** decided confidence `≥ 0.6` **and** nods_along `< 0.6` |
| Assumed reopen | still_material Noul `> 0.6` |
| Deliver log | diminishing-returns Score `≥ 1.5` and no assumed reopen |
| Round cap | ask at most **4** survivors, highest `ask_value.score` first |
| Rank | `ask_value.score`. If two scores differ by `< 0.15`, prefer higher `irreversible` |
| Irreversible flag | show on the question when irreversible Noul `> 0.6`; never mix into the score |

A Noul near 0.5 means "I do not know". It is not "medium". Rank is a
Score. Uncertain on a Score is low confidence, not a mid score.

Jev request shapes: [reference.md](reference.md).

## Control flow

```
0 Open (probe Jev; start session)
loop:
  1 Weigh the pool (one Jev call)
  if nothing askable → 4
  2 Ask the top-K round; wait
  3 Weigh answers (one Jev call); grow children; recompute pool
4 Close (one Jev call); may reopen into the loop
```

## 0. Open

Probe Jev with one trivial Noul over a sentence of the subject. If auth
fails, stop.

```
python3 /absolute/path/to/this-skill/audit/write.py list --status open
python3 /absolute/path/to/this-skill/audit/write.py start --subject "<subject>"
```

Keep the `session_id` to yourself. Write the probe as `phase=open`
`kind=jev_call`.

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
reframe option. Fan out every judgment in **one** call. Point
instructions at backticked paths. Consume only what the table needs.

Per candidate: `ask_value` Score, `independent` Noul, `is_fact` Noul,
`irreversible` Noul, `rec_pick` Choice. Then:

1. `is_fact > 0.6` → look it up; write `kind=fact`; tell the user; do not
   ask. Facts never become reopen targets.
2. independent `< 0.4` → hold for a later round.
3. nearest `ask_value` level 0 and confidence `≥ 0.6` → prune (stay listed).
4. `rec_pick == neither` → reframe; re-weigh next loop; do not ask this
   wording.
5. Else it is a survivor. Rank by `ask_value.score`. Flag uncertain and
   irreversible. Write one `kind=gate` per candidate.

Read `choice`, `confidence`, **and** `probabilities` on every rec.
A `neither` pick is a rewrite, not a skip of the branch.

**Done when:** survivors are ranked and the round's top K are chosen, or
the pool has nothing askable.

## 2. Ask the round

Ask at most 4 survivors. Number them. Put Jev's rec on the ➡️ line.
Below 0.6 confidence, do not pretend there is a winner. Flag
irreversible Noul `> 0.6` on the question, not in the rank. Write
`phase=ask` `kind=note` with the question ids asked.

```
❓ **Q1** - **<title>**: <body, including choices>

➡️ <pick> (confidence 0.82)

---

❓ **Q2** - **<title>**: <body, including choices> *(hard to undo)*

➡️ uncertain: <A> 0.52 / <B> 0.45 — flagged, pick is not a lead
```

**Done when:** the round is asked in shape and every answer is heard.

## 3. Weigh the answers (one Jev call)

Write each reply as `kind=utterance`. A single utterance that agrees
with the round without restating each call ("looks good") is
nods-along for **every** question in that round. Weigh it; do not
settle any of them.

Fan out one triplet per answer: `decided` Score, `nods_along` Noul,
`reopened_call` Choice over settled decision ids plus `none`.

- Decided Score `< 1.5` **or** decided confidence `< 0.6` **or**
  nods_along `> 0.6` → pushback in ordinary words, keep it on the pool.
  Write `gate=pushback` with `reason` set to why it did not settle.
- `reopened_call` is a decision id **and** that Choice confidence `≥ 0.6`
  → that settled branch returns to the pool. A hit on a fact, or
  confidence `< 0.6`, is not a reopen.
- Otherwise settle, unblock what hung off it, and grow the tree: extract
  branches the **answer already named**, then invent **at most 2** extra
  candidates. Nothing newly grown is asked until it survives the next
  weigh. Do not freeze the tree at the Open seed; do not smuggle
  unweighed questions into the round.

Write one `kind=gate` per answer.

**Done when:** every answer is scored and the pool reflects settled,
pushed-back, reopened, and newly grown questions.

## 4. Close

The session ends on shared understanding, not an empty pool. Enter close
when nothing askable remains (no survivors, no unsettled). Held questions
that never unblock do not block close. One fan-out over the settled tree
and the prune list:

- `still_material` — Noul **per pruned id**
- `diminishing_returns` — Score with three levels: another round would
  reveal a material call / remaining questions are polish / further
  rounds cost more attention than they reveal
- `which_assumption` — Choice over pruned ids plus `none`

Any `still_material > 0.6` reopens that branch into the loop. Else if
diminishing-returns `≥ 1.5`, deliver the log from
`python3 /absolute/path/to/this-skill/audit/write.py log --session <id>`.
Else ask whether to continue or close.

Paste that log as-is. Then: **Does this match what you decided?
Confirming is not a license to implement.** End only when they confirm,
then `status --to closed` and `phase=confirm` `kind=note`. That confirm
does not authorize implementation.

If the user exits mid-session, `--to abandoned`. Unsettled stays
unsettled. Do not write a log that treats nods as calls.

**Done when:** the log is delivered and understanding is confirmed.

## Sources

Interview mechanics adapted from `grilling` / `grill-me`
(mattpocock/skills). Jev mechanics: `typesafe-ai` skill and TypeSafe
docs. Design debts: OntoAgent (what-to-ask decoupled from how-to-ask);
Mediating Assessments Protocol (independent judgments, global evaluation
delayed to the close); cognitive forcing functions (uncertainty display
plus selective forcing); Bayesian adaptive querying (ask for expected
information gain; cap the user round, weigh a larger pool).
