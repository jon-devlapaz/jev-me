---
name: jev-me
description: Grill a plan as a design-tree interview, using Jev ad hoc for typed judgments.
license: MIT
version: 1.1.3
disable-model-invocation: true
---

# Jev-me

Every decision branches. The **frontier** is every unlocked decision —
prerequisites settled. It is not the whole product, and not a single
`❓` if two roots are live. Constraints they already stated are
settled before round 1.

Facts are yours: look them up. Asking whether a file is fetched or
vendored is a fact. A running lookup only holds questions that depend
on it; independent `❓` still print. Decisions are the user's.

## Workflow

Skip the grill — no `❓` — when the ask is a one-line / typo fix,
non-interactive (CI, /loop, scheduled), or a pure info request. If
they typed `/jev-me` on one of those anyway: one line that this is
not a grill, then stop. Do not invent product forks.

1. Print the whole frontier in one round. You author every `❓` and
   `➡️`. Then wait.

   A `❓` **depends** if flipping another still-open `❓` would change
   its answer — park it. Smell: compatibility still open, asking
   cutover this round. Naming a topic, or "don't assume X", does not
   unlock X and does not name its alternatives.

   **Named** means uttered this session, not implied, not a menu you
   brought. List live alternatives in the body only then. `➡️` answers
   only its own `❓`. It may pick among named options; it must not
   introduce a new menu; it may use only already-settled nodes, never
   another open `❓` and never another `➡️` from this round.

   A `❓` is a product fork, not an implementation detail. Smell: an
   image pipeline smuggled into a `➡️`.

   ```
   ❓ **Q1** - **<title>**: <body>

   ➡️ <your recommended answer>
   ⚡ Choice <key> p=<n> conf=<n>

   ---

   ❓ **Q2** - **<title>**: <body>

   ➡️ <your recommended answer>
   ⚡ Noul p=<n>
   ```

   Print a `⚡` line under every Jev-informed `➡️` so they can
   see it. Omit the line when Jev did not judge that arrow. `❓`
   stays clean.

2. Their answers **settle** and grow the frontier. Print the next
   round.

   - Rec-accept ("go with `➡️`", "use your arrows", "you decide" on
     that `❓`) settles it as the `➡️`.
   - Unanswered `❓` reprints; it does not vanish.
   - An answer to a parked `❓` while its parent is open: park, don't
     settle.
   - Contradiction, or a parent settling against a child, retracts
     that child and its descendants; reprint. Do not call the
     frontier empty while parked dependents of settled nodes are
     still unasked.
   - Constraints they volunteer unasked settle or grow the frontier.
   - An implement utterance ("just fix it", "just build it",
     "implement now", "skip the questions") while `❓` remain
     batch-accepts live `➡️`s. If the frontier is then empty, that
     utterance is also implement. If not, print the remainder and do
     not implement. Do not implement while `❓` remain, even if they
     order it.

3. Stop when the frontier is empty — no unlocked product decision
   left — and they **confirm**. Before claiming empty: candidate
   labels only from the original ask and settled nodes — not a
   fresh brainstorm. Smell: session lifetime / 2FA / profile on a
   named-closed stack — do not candidate them, do not Noul them.
   One Noul per remaining candidate, one POST (see Jev).
   High yes → print that `❓`, do not confirm. Near 0.5 is not yes.
   If no label is a high yes → wait for confirm. One line they
   can see: `⚡ empty-frontier:` then each candidate `p=<n>`
   (not a `❓`). Confirm is
   "looks good" / "that's the tree", not implement, not the Noul.
   Then wait; they say when to implement ("implement", "apply it",
   "build it"). After confirm, "ok what now?" means the tree is
   confirmed and waiting to implement: do not rebuild, do not
   re-grill.

## Jev

When a typed judgment would help (Choice / Noul / Score over named
options or a described dimension — not a look-up-able fact), fetch
https://raw.githubusercontent.com/typesafe-ai/skills/main/skills/typesafe-ai/SKILL.md
before the first call and follow it.

- `TYPESAFE_API_KEY` missing: one line that Jev is skipped, tell them
  to `export TYPESAFE_API_KEY`, keep grilling. At claimed-empty:
  skip Jev, still wait for confirm.
- Fetch fails but the key exists: still call (live docs or an
  installed typesafe-ai skill).
- Fetch fails and no key: keep grilling.

Empty-frontier Nouls: state = original ask + settled nodes. Ask
what the state says, not what you would conclude. Criteria: yes =
still-silent product `❓`; no = already settled or implementation
leftover. Not "are we done" / "is the session concluded". Do not
Noul the smell labels.

You still author `➡️`; they still confirm. `❓` stays clean. A
Jev-informed `➡️` is followed by a `⚡` line they can see:
`⚡ Choice <key> p=<n> conf=<n>`, `⚡ Score p=<n> conf=<n>`,
or `⚡ Noul p=<n>`. Not tokens, model, or JSON. Hedge when
confidence is low; a coin-flip `⚡` line is not a pick.
