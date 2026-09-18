---
name: jev-me
description: Grill-me with Jev optional each turn.
license: MIT
disable-model-invocation: true
---

Call the Skill tool with "grilling".

Jev is off until the user asks that turn (`jev Q2`, `jev this round`).

When they ask, use the options already in that ❓ (agent-authored counts). If there are 2–8, add `neither` and POST once:

```
POST https://api.typesafe.ai/v1/systemone
Authorization: Bearer $TYPESAFE_API_KEY
{
  "model": "jev-latest",
  "state": "<goal plus those option lines only>",
  "questions": {
    "pick": {
      "type": "choice",
      "instructions": "<that ❓>",
      "criteria": { "<opt>": "<line>", "neither": "none of these" }
    }
  }
}
```

Put `neither` last in `criteria`. Annotate `choice` and `probabilities` beside that question's `➡️` in place — not as the `➡️`, not a new round. Keep grilling.

If there are not 2–8 options: skip Jev, say so, keep grilling.

Missing `TYPESAFE_API_KEY`, 401, 422, 429, 529, other HTTP, or `neither`: say so, keep the round. Do not retry.
