---
name: jev-me
description: >
  Interviews the user about a plan or a design. Jev scores what to
  ask and what to recommend. Decisions are written to a sqlite audit
  in this skill folder.
  Use when the user types /jev-me or asks to grill a plan.
disable-model-invocation: true
---

# Jev-Me

The person types `/jev-me`. The agent interviews them. **Jev** scores.
Sqlite records. The person decides. A confirmed log is not a license
to implement.

Messy intent is enough to start. Alternatives and lean are outputs
of the interview, not the ticket in.

**Requires:** `TYPESAFE_API_KEY` in the environment. If auth fails,
stop and tell the person to set it. Never put the key in state,
questions, chat, or sqlite.

## Call Jev

`ASK` is `scripts/ask.py`. Call it only this way. Copy question
shapes from [references/jev.md](references/jev.md) exactly. For
primitives and confidence, read
[references/typesafe-ai.md](references/typesafe-ai.md).

```
uv run --isolated --no-project --with typesafe-sdk==0.6.0 python3 /absolute/path/to/this-skill/scripts/ask.py <<'JSON'
{"state": { }, "questions": { }}
JSON
```

The script pins `model="jev-1.13.0"`. If that version is missing,
stop. Write the returned `model` into `kind=jev_call`.

Each call is a fresh `{state, questions}`. Jev remembers nothing.
Sqlite is the binder. Rebuild state from the interview, not from
docs.

- Intake: `{utterance}` only.
- Later: `intent` (the original utterance, whole), `answers` (every
  real reply, their words: `{id, question, text}`), `open_pushbacks`
  (`{id, question, reason}`), `settled` (Jev-locked lines only),
  plus `candidates` or `asked`.
- Copy question shapes from [references/jev.md](references/jev.md).
  Point backticks at those paths.

Do not put skill rules, folder maps, ADR/RFC essays, or TypeSafe
pages in state. If deleting a field would not change the score,
leave it out. If a field is in state, some instruction must name it.

One call per stage. Questions cannot read each other. Rec options
are live alternatives the person already named, `neither` last.
Do not invent a menu so Jev has something to pick.

After every Jev response, write `kind=jev_call` with the `state`,
`questions` (full shapes), `answers`, and `model` you actually sent
and received. Never omit `state`. Never shrink `questions` to
`{"type": ...}` only.

Read Jev mechanics from [references/typesafe-ai.md](references/typesafe-ai.md)
only. Do not fetch live TypeSafe URLs during an interview.

## Audit

`WRITER` is `scripts/write.py`. Absolute path. It does not call Jev
and does not apply gates.

```
python3 /absolute/path/to/this-skill/scripts/write.py start --subject "<subject>"
python3 /absolute/path/to/this-skill/scripts/write.py list --status open
python3 /absolute/path/to/this-skill/scripts/write.py event --session <id> --phase <phase> --kind <kind> [--candidate <qid>] <<'JSON'
{...}
JSON
python3 /absolute/path/to/this-skill/scripts/write.py status --session <id> --to closed
python3 /absolute/path/to/this-skill/scripts/write.py log --session <id>
```

`phase`: `open` `weigh_pool` `ask` `weigh_answers` `close` `confirm` `abandon`.
`kind`: `jev_call` `gate` `utterance` `fact` `note`.
`gate`: `settle` `pushback` `prune` `reopen`.

Write `kind=gate` only when a threshold below fires. Write
`kind=utterance` after every person reply. Keep `session_id` and
sqlite paths off the person's screen.

## Loop

```
0 Open. loop: 1 Weigh → 2 Ask → 3 Weigh answers → 1 … → 4 Close.
```

### 0. Open

`list --status open`. If something is open: resume that, or start
a new one? Wait.

If they typed only `/jev-me`, ask this and wait:

```
What are you planning or designing? Answer in your own words.
```

If the first message already answers that, use it. That paragraph
is the utterance. `start --subject` with their words.

Intake (one Jev call). State is only `utterance`. Copy `is_decision`,
`has_alternatives`, and `session_kind` from
[references/jev.md](references/jev.md). Write `kind=jev_call`.

Route Q1 from the `session_kind` pick, even when confidence is
below 0.6. Soft explore is still explore. Only `neither` (or a
missing pick) falls through: if `is_decision` `> 0.6`, treat as
`lock_a_call`; else a wish. Noul near 0.5: unknown, same as a
wish. Default is one open question, no rec, no invented menu.

- `collect_issues`: What issues, bugs, or churn did you hit?
- `explore`: What do you need to understand first?
- `lock_a_call`: What call do we need to lock?
- wish / neither / unknown: What should we decide?

Show the intro plus that question. Write `phase=ask kind=note`.
Do not settle this Q1. Keep `session_kind` for the rest of Open
and the first weigh. Do not narrate lookups.

After they answer, write `kind=utterance`. That reply goes in
`answers` (their words). Next question follows that answer.

If the candidates would all be the same job (four flavors of
“understand X”), skip weigh. Ask one follow-up. Write the ask
note. That is Q2.

If the candidates are different jobs (understand vs constrain vs
lock vs risk), weigh. Write the weigh `jev_call` and any prune
gates **first**, then the ask note. Never write the ask note
before the weigh call.

Seed only those in-kind candidates — not a fixed eight-axis list,
not ADR/RFC essays, not a change-path menu they did not name.

- `explore` / wish: questions about what they need to understand.
  No “what do we lock first,” no “what would you not reverse.”
- `collect_issues`: what they hit, where it broke, what churned.
  No design-fork menu.
- `lock_a_call`: then sequencing and irreversible are allowed.
  Multiple choice only when they already named the alternatives.

A fact you can read in this skill folder or
[references/typesafe-ai.md](references/typesafe-ai.md) is not
asked. Log it `kind=fact` if you need the audit. Do not copy it
into Jev state.

The next user-visible message is Q2 only.

Done when: a session exists, intake is written, Q1 is asked, and
after they answer either Q2 is asked from their last words or a
distinct-job pool is weighed then asked, in that order.

### 1. Weigh (one Jev call)

Per open candidate: `ask_value`. Add `rec_pick` only when that
candidate already has live alternatives. Skip lock-first and
hardest-to-undo candidates while `session_kind` is `explore` or
`collect_issues`.

- Prune: ask_value rounds to 0 **and** confidence ≥ 0.8. Write
  `gate=prune`. Drop it from the pool.
- A `neither` pick: rewrite that candidate as an open question.
  Do not ask it this turn.
- Everything else is askable. Rank by ask_value level (round, clip
  0–2), then higher confidence. Write no gate for ranked rows.

Done when: every candidate is pruned, rewritten, or ranked.

### 2. Ask

Ask the top 1. Number Q1, Q2, … across the interview. **Pipe** the
candidate `text`. Write `phase=ask kind=note` with that id **after**
the weigh `jev_call` for this turn (unless weigh was skipped).

```
❓ **Qn** - **<candidate text>**
➡️ <rec line>
```

- Rec confidence ≥ 0.6: the pick and its confidence.
- Rec confidence < 0.6: `uncertain: {top} {p} / {second} {p}`.
- No rec this turn: `Answer in your own words.`

Done when: chat, the `jev_call`, and the ask note share the same
id, text, and ➡️ line.

### 3. Weigh answers (one Jev call)

Write the reply as `kind=utterance` with that candidate. Per answer:
`decided` + `nods_along`. State is `intent`, `answers`,
`open_pushbacks`, `settled`, and this turn's `asked` (text, rec,
answer).

- Settle: decided ≥ 1.5 **and** confidence ≥ 0.8 **and** nods_along
  < 0.6. Write `gate=settle`. At most 2 follow-up candidates from
  the answer, open, for the next weigh.
- Else push back in ordinary words, numbers in parentheses. Write
  `gate=pushback`. After 2 pushbacks, leave it open and move on.
- "Looks good" (agree with no constraint): weigh it. Settle nothing.
- If the answer contradicts a settled call: `gate=reopen` that call
  and re-ask it next turn. No Jev needed.

Done when: the answer has one real gate, and the pool matches.

### 4. Close

When nothing askable remains, paste `log --session <id>` as-is, then:
**Does this match what you decided? Confirming is not a license to
implement.** End on confirm: `status --to closed` plus
`phase=confirm kind=note`. If they stop: `status --to abandoned`.
Unsettled stays unsettled.

Done when: the log is delivered and confirm or abandon is recorded.

## What the person sees

The person sees the resume prompt, the bare-`/jev-me` planning
question, or the intro plus one numbered question. No recon notes,
no lookup narration, no session ids.

I'll ask one question at a time about what changes the plan. Answer
in your own words — "looks good" is not an answer.
