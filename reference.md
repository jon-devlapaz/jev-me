# Jev question shapes

Send `state` plus `questions` in **one** call per step. Mix Noul, Score,
and Choice. Point instructions at backticked paths.

## Weigh pool (per candidate)

`ask_value` is a Score. Do not rank with a Noul.

```json
{
  "state": {
    "subject": "Migrate checkout sessions to Redis",
    "facts": ["Render already hosts the app"],
    "settled": ["Stays on Render", "Budget $100/mo"],
    "candidates": [{"id": "q1", "text": "Sync or async session writes?"}],
    "rec_candidates": {
      "q1": {
        "sync": "Sync: simpler crash story",
        "async": "Async: protects p99",
        "neither": "Neither fits; the question needs reframing"
      }
    }
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

Nearest `ask_value` level is `round(score)` clipped to 0–2.

## Weigh answers (per answer)

```json
{
  "state": {
    "subject": "Migrate checkout sessions to Redis",
    "facts": ["Render already hosts the app"],
    "settled": ["Stays on Render"],
    "settled_ids": ["hosting"],
    "question": {"id": "q1", "text": "Sync or async session writes?"},
    "rec": {"pick": "sync", "confidence": 0.82},
    "answer": "Async. p99 matters more than crash story."
  },
  "questions": {
    "q1_decided": {
      "type": "score",
      "instructions": "How settled is `answer` as a decision on `question`, given `settled`?",
      "criteria": [
        "Vague, hedged, or nodded along with rec without adding a constraint",
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

`reopened_call` criteria are settled **decision** ids plus `none`. Never facts.

## Close

One call over the settled tree and the prune list. `still_material` is a
Noul **per pruned id**. `which_assumption` criteria are pruned ids plus
`none`.

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
