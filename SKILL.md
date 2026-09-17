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
implement. If this skill is loaded, interview. "Don't ask", "just
implement", or "skip the questions" is not a skip. Do not look for a
repo. Do not start building. A named subject still gets Q1–Q4.

**Requires:** `TYPESAFE_API_KEY` in the environment. Do not put the key
in state, questions, chat, or the audit. If auth fails, stop and tell
the user to set `TYPESAFE_API_KEY`. Do not ask them for the secret.

Do not open the `typesafe-ai` skill. Do not fetch TypeSafe docs. Do not read `write.py`, `ask.py`, or `README.md`. If `typesafe-ai` is already
loaded, ignore it — do not follow its docs index. This file plus
[reference.md](reference.md) are enough. Do not write Python. Do not
import `typesafe_sdk`. Do not inspect the SDK.

`ASK` is `audit/ask.py` next to this `SKILL.md`. Call Jev only through
it, so nothing is installed into this skill folder or the user's
project. Question JSON shapes are in [reference.md](reference.md).

```
uv run --with typesafe-sdk python3 /absolute/path/to/this-skill/audit/ask.py <<'JSON'
{"state": { }, "questions": { }}
JSON
```

The script pins `model="jev-1.13.0"`. Do not use `jev-latest` or `jev-preview`. The table below is fitted to `jev-1.13.0`. Do not bump
the pin, and do not edit the table, unless the person says so. If that
version is missing, stop — do not fall back to an alias. Write the
`model` Jev returns into `kind=jev_call`.

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
other file into the user's project. If it returns an error, continue
the interview — do not debug the audit, inspect the SDK, or write a
helper script. Use `ask.py`. One failed `start` is enough; still
weigh and ask.

## Talking to Jev

Jev encodes `state` once. Each question reads that state and its own
instructions; questions **cannot read each other**. Treat that as a
hard boundary:

- Put in `state` only what this call's questions point at. Sqlite keeps the binder.
  Jev gets a slice. Accuracy falls when unrelated detail grows.
- Shared facts every question on this call needs: `subject`, `facts`,
  `settled`. Point instructions at backticked paths.
- Do not paste chat, the audit log, unasked candidates, held
  questions, or rec menus into `state`. Rec options live in that
  Choice's `criteria`.
- Do not hide a constraint in one question's instructions and expect
  another question to use it.
- If question B needs question A's answer, that is a **new request**
  with A's answer copied into `state`. That is why weigh-answers and
  close are separate calls, not extra questions on the pool call.
- Fan out every independent judgment for a stage in **one** call. Do
  not split one weigh into per-candidate requests. Do not send the
  same question twice.

| Stage | Extra in `state` |
| --- | --- |
| Weigh pool | Open candidates only (`id` + text). Not pruned, not held, not recs. |
| Weigh answers | This round under `asked` (text, rec, answer). Not the rest of the pool. |
| Close | `pruned` (`id` + text). Not candidates, not recs, not `asked`. |

`confidence` is not P(correct). It is a summary of how peaked the
returned distribution is (Choice: peak vs uniform; Score: mass around
the modal level). A peaked distribution can still be wrong.
Noul has no confidence field; the noul value **is** the probability.
Always read `choice` / `score` / `noul`, `confidence` when present,
**and** `probabilities`. Identical payloads can differ slightly; apply
the table once, do not retry for a prettier float. Unsure means do not
act. The person is the fallback. Do not call another model to re-score.
Do not retry Jev.

Rec options are a listwise choice set. A dummy option moves the odds
between the real ones. Draft 2–4 live alternatives, always including
`neither` **last**. Put discriminating facts in `state`, not inside
one option.

## What the person sees

The person never sees session ids, sqlite paths, Noul/Score names, raw
JSON, or `write.py` output except the human log at close. Keep those
for yourself.

If they typed `/jev-me` with no subject, ask **one** question and wait.
Do not probe Jev and do not seed until they name it. Do not ask how hard to grill or what the session is for. That is not the plan.

```
❓ **Q1** - **What should we decide?**: Name the plan in 2–5 sentences —
the live alternatives and what you're leaning toward.

➡️ Give me the call you're least sure about, and which way you're leaning.
```

If `list --status open` shows an unfinished interview, do **not** start
a second one. Ask, then wait:

```
You already have an unfinished interview: "<subject>". Resume that, or
start a new one?
```

Except for a missing subject, an auth failure, a resume prompt, or the
fog sentence below, do not send a user-visible message until the first
numbered round is ready. Probe is not a step. Start and weigh silently.
A named subject always gets Q1 on that first turn, even if every rec is
flagged uncertain. That numbered round is the **whole first message**.
No recon notes, no "still waiting" without the questions, no audit
errors. Do not mention the audit. If you looked a fact up, change the
question or stay silent — do not narrate the lookup.

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

If the person already answered numbered questions, that is
weigh-answers. Do not restart Open. Do not re-ask the same round.

## Audit

```
python3 /absolute/path/to/this-skill/audit/write.py start --subject "<subject>"
python3 /absolute/path/to/this-skill/audit/write.py list --status open
python3 /absolute/path/to/this-skill/audit/write.py event --session <id> --phase <phase> --kind <kind> [--candidate <qid>] --json '{...}'
python3 /absolute/path/to/this-skill/audit/write.py status --session <id> --to closed
python3 /absolute/path/to/this-skill/audit/write.py log --session <id>
python3 /absolute/path/to/this-skill/audit/write.py review
uv run --with typesafe-sdk python3 /absolute/path/to/this-skill/audit/ask.py
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
| Prune | nearest `ask_value` level is 0 **and** confidence `≥ 0.8` |
| Uncertain flag | `ask_value` confidence `< 0.6` — keep, flag, do not auto-prune |
| Hold | independent Noul `< 0.4`, or independent `≤ 0.6` while other open candidates remain |
| Fact | is_fact Noul `> 0.8` — look it up, do not ask |
| Rec lead | Choice confidence `≥ 0.6`; else show the top two probabilities, no winner |
| Reopen | `reopened_call` is a **decision** id, not a looked-up fact, **and** that option's probability `≥ 0.6` |
| Settle | decided Score `≥ 1.5` **and** decided confidence `≥ 0.8` **and** nods_along `< 0.6` |
| Assumed reopen | still_material Noul `> 0.6` |
| Deliver log | diminishing-returns Score `≥ 1.5` and no assumed reopen |
| Round cap | ask at most **4**. Fill with peaked survivors (`ask_value` confidence `≥ 0.6`) in rank order. If peaked is empty or the round is short, fill with ranked uncertain survivors, flagged |
| Fog | remaining items are holds, so the round would be empty. One sentence: continue, pick one, or stop. Unpeaked `ask_value` is not fog. Do not call another model. Do not retry Jev |
| Rank | nearest `ask_value` level (`round(score)` clipped to 0–2), then higher irreversible Noul, then higher `ask_value.confidence`. Do not sort on the raw score |
| Irreversible flag | show on the question when irreversible Noul `> 0.6`; never mix into the score |

A Noul near 0.5 means "I do not know". It is not "medium". Rank uses
the Score's **level**, not the leftover fraction. Uncertain on a Score
is low confidence, not a mid score.

Show-a-winner is 0.6: a rec is a nudge. Discard and lock are 0.8:
throwing a question away, skipping a question as a fact, or writing a
settled call is harder to undo. Rec lead uses Choice confidence (peak
vs uniform). Prune and settle use Score confidence (mass around the
modal level). Reopen uses the option's probability so the bar does not
drift as the settled set grows. Reopen and `still_material` stay at
0.6: missing a mind-change or a silent assumption is worse than one
extra question.

The round cap is the person's attention, not Jev's. Weigh the whole
pool in one call; ask at most 4. Fill those 4 with peaked survivors
first. If peaked is empty or the round is short, fill with ranked
uncertain survivors and flag them — that is asking the person, not
silently grilling. A Noul `≤ 0.6` is not "kind of independent": hold
it while siblings are still open. Fog only when the round would be
empty because what remains is held. Continue asks up to 4 held items
that are not hard-dependent (`< 0.4`), pruned, or a fact. Pick one
asks that id. Stop closes.

Jev request shapes: [reference.md](reference.md).

## Control flow

```
0 Open (start session; first weigh is the auth check)
loop:
  1 Weigh the pool (one Jev call)
  if any survivors (peaked or uncertain) → 2
  if only holds remain → ask person (continue / pick one / stop); wait
  if nothing askable → 4
  2 Ask the round; wait
  3 Weigh answers (one Jev call); grow children; recompute pool
4 Close (one Jev call); may reopen into the loop
```

## 0. Open

Do not probe. The first weigh is the auth check. If it fails, stop.

```
python3 /absolute/path/to/this-skill/audit/write.py list --status open
python3 /absolute/path/to/this-skill/audit/write.py review
python3 /absolute/path/to/this-skill/audit/write.py start --subject "<subject>"
```

If `review` reports reversals, one sentence to the person: pruned calls
came back, or settles unlocked. Do not edit the threshold table unless
they say so. If it says too few sessions, say nothing.

Keep the `session_id` to yourself.

Frame the subject as a **design tree**. Seed **6–8** candidate questions,
**one primary axis each**: objective, constraints, alternatives,
sequencing, irreversible calls, risks, what would reopen. Do not seed
four flavors of rollback. Multiple choice only when the live
alternatives are already known (settled state or the user's wording);
otherwise open. Facts are yours to look up, silently. The interviewing
LLM does not invent a menu to look sure.

**Done when:** the client answers and the pool has a first set of
candidates.

## 1. Weigh the pool (one Jev call)

The **pool** is every decision whose prerequisites are already settled.
Draft 2–4 rec options per question, always including a `neither` /
reframe option **last**. Live alternatives only — a dummy option moves
the odds between the real ones. Fan out every judgment in **one** call.
`candidates` in this call is the **open** pool only, so `independent`
can see siblings. Leave pruned, held, and unasked children in sqlite.
Do not send one candidate per request. Do not duplicate rec menus in
`state`. Point instructions at backticked paths. Consume only what
the table needs.

Per candidate: `ask_value` Score, `independent` Noul, `is_fact` Noul,
`irreversible` Noul, `rec_pick` Choice. Then:

1. `is_fact > 0.8` → look it up; write `kind=fact`; tell the user; do not
   ask. Facts never become reopen targets.
2. independent `< 0.4` → hold. independent `≤ 0.6` while other open
   candidates remain → hold.
3. nearest `ask_value` level 0 and confidence `≥ 0.8` → prune (stay listed).
4. `rec_pick == neither` → reframe; re-weigh next loop; do not ask this
   wording.
5. Else it is a survivor. Rank by nearest `ask_value` level, then
   irreversible, then confidence. Do not sort on the raw score. Flag
   uncertain and irreversible. Write one `kind=gate` per candidate.

Fill the round from peaked survivors (`ask_value` confidence `≥ 0.6`)
in that rank order, at most 4. If peaked is empty or the round is
short, fill with ranked uncertain survivors and flag them. Skip a
survivor whose seed axis is already in the round — take the next axis
instead. A named subject's first user-visible turn is that numbered
round — not fog. A short round of distinct axes is better than padding.

If the round would be empty because remaining items are holds, do not
jump to close. One sentence, then wait:

```
What's left is unclear: I'm not sure these still change the plan, or
that they can be answered on their own. Continue, pick one, or stop?
```

Continue: ask up to 4 held items that are not independent `< 0.4`,
pruned, or a fact. Pick one: ask that id. Stop: close. Do not call
another model. Do not retry Jev.

Read `choice`, `confidence`, **and** `probabilities` on every rec.
A `neither` pick is a rewrite, not a skip of the branch.

**Done when:** survivors are ranked and the numbered round is chosen, or
the fog sentence is asked because only holds remain, or the pool has
nothing askable.

## 2. Ask the round

Ask at most 4 survivors, peaked first. Weighing more is cheap; asking
more is not. Number them. Put Jev's rec on the ➡️ line. Below 0.6
confidence, do not pretend there is a winner. The only person-visible
flags on a question are `*(hard to undo)*` when irreversible Noul
`> 0.6`, and `*(uncertain)*` when `ask_value` confidence `< 0.6`. Write
`phase=ask` `kind=note` with the question ids asked.

```
❓ **Q1** - **<title>**: <body, including choices>

➡️ <pick> (confidence 0.82)

---

❓ **Q2** - **<title>**: <body, including choices> *(hard to undo)* *(uncertain)*

➡️ uncertain: <A> 0.52 / <B> 0.45 — flagged, pick is not a lead
```

**Done when:** the round is asked in shape and every answer is heard.

## 3. Weigh the answers (one Jev call)

Write each reply as `kind=utterance`. A single utterance that agrees
with the round without restating each call ("looks good") is
nods-along for **every** question in that round. Weigh it; do not
settle any of them.

Fan out one triplet per answer: `decided` Score, `nods_along` Noul,
`reopened_call` Choice over settled decision ids plus `none`. State
is `subject`, `facts`, `settled`, `settled_ids`, and `asked` for
**this round only** (at most 4). Do not send the rest of the pool.

- Decided Score `< 1.5` **or** decided confidence `< 0.8` **or**
  nods_along `> 0.6` → pushback in ordinary words, keep it on the pool.
  Write `gate=pushback` with `reason` set to why it did not settle.
- `reopened_call` is a decision id **and** `probabilities[id] ≥ 0.6`
  → that settled branch returns to the pool. A hit on a fact, a pick
  of `none`, or probability `< 0.6`, is not a reopen.
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
when nothing askable remains (no survivor, no held item to put to the
person, no unsettled). Fog is not close. Held questions with independent
`< 0.4` that never unblock do not block close. One fan-out over the settled tree
and the prune list. Do not send candidates, recs, or `asked`:

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
then `status --to closed` and `phase=confirm` `kind=note`. Run
`review --session <id>`. Same rule: tell them only if reversals
showed up; do not edit the table unless they say so. That confirm
does not authorize implementation.

If the user exits mid-session, `--to abandoned`. Unsettled stays
unsettled. Do not write a log that treats nods as calls.

**Done when:** the log is delivered and understanding is confirmed.
