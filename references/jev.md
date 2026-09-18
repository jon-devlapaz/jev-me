# Jev question shapes

The judgments jev-me sends, with exact `instructions` and `criteria`.
Copy these strings exactly — the criteria wording **is** the scale, and
rephrasing between runs silently re-scales every score. Send `state` plus
`questions` in one call per stage through `scripts/ask.py`. For how
primitives, state, and confidence work, read
[typesafe-ai.md](typesafe-ai.md) (vendored upstream manual).

## Intake (first utterance)

State is only the person's first answer:

```json
{
  "utterance": "I want to migrate checkout sessions to Redis. Sync or async writes?"
}
```

`is_decision` — Noul.

```json
{
  "type": "noul",
  "instructions": "Does `utterance` name a decision a stranger could log, rather than a wish or a topic?"
}
```

`has_alternatives` — Noul.

```json
{
  "type": "noul",
  "instructions": "Does `utterance` name two or more live alternatives for a decision?"
}
```

`session_kind` — Choice. `neither` last.

```json
{
  "type": "choice",
  "instructions": "Given `utterance`, what kind of start is this?",
  "criteria": {
    "lock_a_call": "They want to lock a design or plan choice",
    "collect_issues": "They want bugs, issues, churn, or dogfood notes",
    "explore": "They want to understand options without locking one",
    "neither": "None of these fits; the next question should stay open"
  }
}
```

## Weigh (per candidate)

State is the interview so far, plus open candidates. `intent` is
the original utterance, copied whole every call.

```json
{
  "intent": "I want to migrate checkout sessions to Redis. Sync or async writes? Leaning async.",
  "answers": [
    {
      "id": "q1",
      "question": "What do you need to understand first?",
      "text": "Whether we can keep Render and still get p99 down."
    }
  ],
  "open_pushbacks": [],
  "settled": [],
  "candidates": [{"id": "q2", "text": "Sync or async session writes?"}]
}
```

`ask_value` — Score. Do not rank with a Noul. For each extra
candidate in the same call, point at `candidates[1]`, `candidates[2]`,
… in that question's instructions only.

```json
{
  "type": "score",
  "instructions": "How much does answering `candidates[0]` change the plan in `intent`, given `answers`, `open_pushbacks`, and `settled`?",
  "criteria": [
    {
      "what": "Local, reversible, or already implied by settled",
      "signals": ["Answering it does not change what gets built, sequenced, or ruled out"]
    },
    {
      "what": "Changes sequencing or a local design choice. Live paths remain",
      "signals": ["The plan still has the same live alternatives after this call"]
    },
    {
      "what": "Changes the outcome or kills a live path",
      "signals": ["A different answer would build something else or rule a path out"]
    }
  ]
}
```

`rec_pick` — Choice. Send it only when this candidate already has
live alternatives from the person's words or `settled`. Otherwise
weigh with `ask_value` alone. Criteria are those alternatives (2–4,
short key + display string) with `neither` **last**. No dummy
options. Discriminating content stays in `intent` / `answers`, not
inside one option.

```json
{
  "type": "choice",
  "instructions": "Given `intent`, `answers`, `open_pushbacks`, and `settled`, which option leads best for `candidates[0]`?",
  "criteria": {
    "sync": "Sync: simpler crash story",
    "async": "Async: protects p99",
    "neither": "Neither fits; the question needs reframing"
  }
}
```

## Weigh answers (per answer)

State is the interview plus this turn's `asked`.
`rec` is the shown ➡️ line (`pick` + `confidence`).

```json
{
  "intent": "I want to migrate checkout sessions to Redis. Sync or async writes? Leaning async.",
  "answers": [
    {
      "id": "q1",
      "question": "What do you need to understand first?",
      "text": "Whether we can keep Render and still get p99 down."
    }
  ],
  "open_pushbacks": [],
  "settled": ["Stays on Render"],
  "asked": {
    "q2": {
      "text": "Sync or async session writes?",
      "rec": {"pick": "async", "confidence": 0.82},
      "answer": "Async. p99 matters more than crash story."
    }
  }
}
```

`decided` — Score.

```json
{
  "type": "score",
  "instructions": "How settled is `asked.q2.answer` as a decision on `asked.q2.text`, given `intent`, `answers`, `open_pushbacks`, and `settled`?",
  "criteria": [
    "Vague, hedged, or nodded along with rec without adding a constraint",
    "Answered with a reservation a stranger could still misread",
    "Settled; a stranger could defend this call from the log alone"
  ]
}
```

`nods_along` — Noul.

```json
{
  "type": "noul",
  "instructions": "Does `asked.q2.answer` merely agree with `asked.q2.rec` without adding a constraint or a reason?"
}
```

## Reading answers

`confidence` on Choice/Score is peakedness of the returned distribution,
not P(correct). Noul has no confidence field — the value is the
probability, and near 0.5 means "I do not know", not "medium". Always
read the score/choice/noul **and** the `probabilities`. Rank and gate
on the Score's level (`round(score)` clipped to 0–2), not the leftover
fraction.
