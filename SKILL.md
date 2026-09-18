---
name: jev-me
description: Grill-me with Jev optional each turn.
disable-model-invocation: true
---

Interview the user relentlessly until you reach a shared understanding. Map this as a **design tree**: every decision branches into the decisions that hang off it.

Work the tree in **rounds**. The **frontier** is every decision whose prerequisites are already settled: the questions you can ask _now_ without guessing at answers you haven't heard yet. Ask the whole frontier in one round: number each question and give your recommended answer. Then wait for the user's answers before the next round.

Format a round like so:

```
❓ **Q1** - **<question title>**: <question body, might be multiple paragraphs, including multiple choices>

➡️ <your recommended answer>

---

❓ **Q2** - **<question title>**: <question body, might be multiple paragraphs, including multiple choices>

➡️ <your recommended answer>
```

Each round the user answers reshapes the tree: settled decisions push the frontier outward and unblock questions that depended on them. Recompute the frontier and ask the next round. A question whose answer depends on another question still open in this round belongs to a _later_ round, not this one.

Finding _facts_ is your job, never the user's. When a frontier question needs a fact from the environment (filesystem, tools, etc.), dispatch a sub-agent to find it; don't ask the user for anything you could look up yourself. Don't block on it: a running exploration is an unsettled prerequisite, so only the questions downstream of it wait for the sub-agent to report; ask the rest of the frontier now. The _decisions_ are the user's: put each to them and wait.

The session is done when the frontier is empty: every branch of the design tree visited, nothing left silently assumed. Do not act on it until the user confirms you have reached a shared understanding.

Jev is off until the user asks that turn (`jev Q2`, `jev this round`).

When the user asks for a question that already has a closed 2–8 set they named or accepted:

1. TypeSafe primitive: read [references/typesafe.md](references/typesafe.md) and follow it for the call.
2. One `POST https://api.typesafe.ai/v1/systemone` (`model: jev-latest`) with one `choice`. `neither` last. `state` is the goal plus those option lines only.
3. Print `choice` and `probabilities` beside that question's `➡️`, not as the `➡️`.

When the user asks and there is no closed set: skip Jev, say so, keep grilling.

Missing `TYPESAFE_API_KEY`, 422, 429, 529, or `neither`: say so, keep the round. Do not retry.
