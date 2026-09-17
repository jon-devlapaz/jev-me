# Jev question shapes

Send `state` plus `questions` in **one** call per step through
`audit/ask.py`. Mix Noul, Score, and Choice. Point instructions at
backticked paths. Every call uses `model="jev-1.13.0"`. Not `jev-latest`.

Jev encodes `state` once. Each question reads that state and its own
text; questions cannot read each other. Put in `state` only the fields
this call's questions need. Sqlite keeps the binder. If a later
judgment needs an earlier answer, that is a new request with the
answer copied into `state` — not another question on the same call.

`confidence` is not P(correct). For a Choice it is peak vs uniform:

`(p_max - 1/K) / (1 - 1/K)`

Three rec options with `p_max = 0.8` yield confidence `0.7`. As `K`
grows, the same confidence bar is a weaker probability, which is why
reopen thresholds `probabilities[id]`, not confidence. Score confidence
is mass around the modal level. Noul has no confidence field.

Rec `criteria` are a listwise choice set: live alternatives only, no
dummy option (it moves the odds between the real ones), `neither` last.
Put discriminating facts in `state`, not inside one option.

## Weigh pool (per candidate)

`ask_value` is a Score. Do not rank with a Noul.

```json
{
  "state": {
    "subject": "Migrate checkout sessions to Redis",
    "facts": ["Render already hosts the app"],
    "settled": ["Stays on Render", "Budget $100/mo"],
    "candidates": [{"id": "q1", "text": "Sync or async session writes?"}]
  },
  "questions": {
    "q1_ask_value": {
      "type": "score",
      "instructions": "How much does answering `candidates[0]` change the plan for `subject`, given `settled`?",
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
      "instructions": "Given `subject` and `settled`, which option leads best for `candidates[0]`?",
      "criteria": {
        "sync": "Sync: simpler crash story",
        "async": "Async: protects p99",
        "neither": "Neither fits; the question needs reframing"
      }
    }
  }
}
```

Nearest `ask_value` level is `round(score)` clipped to 0–2.

Rank survivors by that **level**, then irreversible Noul, then
`ask_value.confidence`. Do not sort on the raw score: `1.32` is not
more askable than `0.95` if both round to 1. Prune may still *threshold*
on the score (nearest level 0). Ranking may not interpolate it.

Fill the round with peaked survivors (`ask_value` confidence `≥ 0.6`)
first. If peaked is empty or the round is short, fill with ranked
uncertain survivors and flag them. Independent Noul `≤ 0.6` while
other open candidates remain is a hold, not a maybe. Fog only when
remaining items are holds. Do not re-score with another model.

`candidates` is the **open** pool only (`id` + text), so `independent`
can see siblings. Leave pruned, held, unasked children, and rec menus
out. Rec options live in `rec_pick` criteria. Do not send one candidate
per request.

## Weigh answers (per answer)

```json
{
  "state": {
    "subject": "Migrate checkout sessions to Redis",
    "facts": ["Render already hosts the app"],
    "settled": ["Stays on Render"],
    "settled_ids": ["hosting"],
    "asked": {
      "q1": {
        "text": "Sync or async session writes?",
        "rec": {"pick": "sync", "confidence": 0.82},
        "answer": "Async. p99 matters more than crash story."
      }
    }
  },
  "questions": {
    "q1_decided": {
      "type": "score",
      "instructions": "How settled is `asked.q1.answer` as a decision on `asked.q1.text`, given `settled`?",
      "criteria": [
        "Vague, hedged, or nodded along with rec without adding a constraint",
        "Answered with a reservation a stranger could still misread",
        "Settled; a stranger could defend this call from the log alone"
      ]
    },
    "q1_nods_along": {
      "type": "noul",
      "instructions": "Does `asked.q1.answer` merely agree with `asked.q1.rec` without adding a constraint or a reason?"
    },
    "q1_reopened_call": {
      "type": "choice",
      "instructions": "Which already-settled call does `asked.q1.answer` reopen?",
      "criteria": {
        "hosting": "Stays on Render",
        "none": "No earlier settled call is reopened"
      }
    }
  }
}
```

`reopened_call` criteria are settled **decision** ids plus `none`. Never facts.
Reopen when the chosen id is a decision and `probabilities[id] ≥ 0.6`.
The user's answer belongs in `asked` so every question in this call
can see this round. Do not send the rest of the pool.

## Close

One call over the settled tree and the prune list. `still_material` is a
Noul **per pruned id**. `which_assumption` criteria are pruned ids plus
`none`. Do not send candidates, recs, or `asked`.

```json
{
  "state": {
    "subject": "Migrate checkout sessions to Redis",
    "settled": ["Stays on Render", "Async writes"],
    "pruned": [{"id": "cdn", "text": "Put CloudFront in front?"}]
  },
  "questions": {
    "cdn_still_material": {
      "type": "noul",
      "instructions": "If `pruned[0]` stays unanswered, is a live path for `subject` still silently assumed?"
    },
    "diminishing_returns": {
      "type": "score",
      "instructions": "Would another round of questions change the plan for `subject`, given `settled` and `pruned`?",
      "criteria": [
        {
          "what": "Another round would reveal a material call",
          "signals": ["A live path is still assumed or a settled call is still ambiguous"]
        },
        {
          "what": "Remaining questions are polish",
          "signals": ["The plan would not change; leftover questions are local"]
        },
        {
          "what": "Further rounds cost more attention than they reveal",
          "signals": ["The person would be repeating themselves"]
        }
      ]
    },
    "which_assumption": {
      "type": "choice",
      "instructions": "Which pruned question is the strongest silent assumption?",
      "criteria": {
        "cdn": "Put CloudFront in front?",
        "none": "No pruned question is still a silent assumption"
      }
    }
  }
}
```
