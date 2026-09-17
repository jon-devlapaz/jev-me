# Jev-Me

A grilling interview with Jev weighing in at every step: which questions
earn a round, which recommendation leads each question, whether each answer
settles its branch, and when the session ends.

An agent skill. You invoke it by typing `/jev-me`; the agent never fires it
on its own. The skill is [SKILL.md](SKILL.md).

## How it runs

1. **Open** — verifies a working Jev client, then frames your subject as a
   design tree: decisions with decisions hanging off them.
2. **Weigh the frontier** (one Jev call) — every candidate question is
   scored for load-bearing-ness and independence; low-value branches are
   pruned (and stay listed so you can resurrect them); each survivor gets a
   Jev-picked recommendation.
3. **Ask the round** — the whole frontier at once in ❓/➡️ shape, each
   recommendation carrying its confidence in plain sight. Low confidence is
   flagged, inviting your pushback instead of your nod.
4. **Weigh the answers** (one Jev call) — each answer is scored for
   decided-ness; mushy answers come back as pushback quoting the score
   ("Jev scores that 0.3 decided — what would make it a 1.0?").
5. **Close** — a final weigh-in checks nothing is silently assumed and the
   session has converged, then delivers a decision log: settled calls with
   confidences, pushbacks and how they resolved, pruned branches, and what
   would reopen each call. Ends only on your confirmed shared understanding.

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
forcing), and Bayesian adaptive querying (ask for expected information
gain). Pairs with [jev-decisions](https://github.com/jon-devlapaz/jev-decisions)
for architecture calls that want the full decision engine.
