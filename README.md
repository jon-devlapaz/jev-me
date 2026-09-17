# Jev-Me

A grilling interview with Jev weighing in at every step: which questions
earn a round, which recommendation leads, whether each answer settles its
branch, and when the session ends.

For a person who wants more useful determinism in **planning and
interviewing** when the interviewer is an overconfident, jagged LLM.
Jev pins that interviewer. Not a general harness, not an autonomous
planner, not an implementation license.

An agent skill. You invoke it by typing `/jev-me`; the agent never fires it
on its own. The skill is [SKILL.md](SKILL.md).

## How it runs

The numbered sections in `SKILL.md` are a loop, not a straight line.

1. **Open** — verifies a working Jev client, then seeds a design tree
   (6–8 candidates across planning axes: objective, constraints,
   alternatives, sequencing, irreversible calls, risks, reopen).
2. **Weigh the pool** (one Jev call) — every candidate is judged for
   load-bearing, independence, fact-vs-decision, and irreversibility;
   each gets a rec pick. Code prunes strong-no branches, holds
   dependents, looks up facts, ranks survivors by load-bearing (sticky
   as a tiebreak only), and asks at most four.
3. **Ask the round** — top-K in ❓/➡️ shape. Rec confidence and, when
   the pick is split, the runner-up probabilities sit on the ➡️ line.
4. **Weigh the answers** (one Jev call) — Score of decided-ness, Noul
   for nodding-along, Choice for *which* settled call reopened. Mush
   stays on the pool as pushback quoting the Score level. Settled
   answers grow children from what the user named (at most two invented,
   then re-weighed); the tree does not freeze at the seed.
5. **Close** — per-prune "still material" Nouls, a diminishing-returns
   Score, and a Choice that names the assumption to reopen. Ends on
   confirmed shared understanding, never on an empty pool alone, and
   never as authorization to implement.

Noul 0.5 means I don't know, not medium. Uncertain bands are kept, not
auto-pruned. "Looks good" is nods-along, not a decision. Looked-up facts
are not reopen targets.

## Requires

- A working Jev client (`TYPESAFE_API_KEY` in the environment). The skill
  verifies it before starting and never handles the key itself.
- The [`typesafe-ai`](https://github.com/typesafe-ai/skills) skill for Jev
  API mechanics.

## Grounding

Interview mechanics adapted from `grilling` / `grill-me`
([mattpocock/skills](https://github.com/mattpocock/skills)). Design debts:
OntoAgent (what-to-ask decoupled from how-to-ask), the Mediating
Assessments Protocol (independent judgments, global evaluation delayed to
the close), cognitive forcing functions (uncertainty display plus selective
forcing), and Bayesian adaptive querying (weigh a large pool, ask a short
round). Pairs with [jev-decisions](https://github.com/jon-devlapaz/jev-decisions)
for architecture calls that want the full decision engine.
