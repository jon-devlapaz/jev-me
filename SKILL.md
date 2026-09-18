---
name: jev-me
description: Grill a plan as a design-tree interview, using Jev ad hoc for typed judgments.
license: MIT
disable-model-invocation: true
---

# Jev-me

Every decision branches; the **frontier** is every decision whose
prerequisites are already settled. Facts are yours: look them up. A
running lookup only holds questions that depend on it. Decisions are
the user's.

## Workflow

1. Print the whole frontier in one round. You author every `❓` and
   `➡️`. List live alternatives in the body only when they are already
   named. A question that depends on another still open in this round
   belongs to the next. Then wait.

   ```
   ❓ **Q1** - **<title>**: <body>

   ➡️ <your recommended answer>

   ---

   ❓ **Q2** - **<title>**: <body>

   ➡️ <your recommended answer>
   ```

2. Their answers settle decisions and grow the frontier. Print the next
   round.

3. Stop when the frontier is empty — nothing left silently assumed —
   and they confirm. Then wait; they say when to implement.

## Jev

When a typed judgment would help, fetch
https://raw.githubusercontent.com/typesafe-ai/skills/main/skills/typesafe-ai/SKILL.md
before the first call and follow it. Keep grilling if the fetch fails
or `TYPESAFE_API_KEY` is missing. You still author `➡️`; they still
confirm.
