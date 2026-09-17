---
name: jev-me
description: Grill me, with Jev weighing in at every step.
disable-model-invocation: true
---

# Jev-Me

A grilling interview with the mechanics built in and Jev weighing in at
every step: which questions earn a round, which recommendation leads each
question, whether each answer settles its branch, and when the session
ends. You type `/jev-me` to start; the agent never fires this on its own.
The weigh-ins below are the starter set; add judgments in the same shape
wherever the interview needs signal.

**Requires:** a working Jev client. For SDK setup, auth, and
question-shaping mechanics, use the `typesafe-ai` skill; this skill covers
only the interview and its weigh-ins. Keep `TYPESAFE_API_KEY` in the
environment; state, questions, and the closing log carry decisions, never
the key.

## 0. Open

Confirm a working Jev client first: run one trivial call (a single Noul
over a sentence of the subject). If auth fails, stop and tell the user to
set `TYPESAFE_API_KEY` in their environment — never ask them to paste the
key into chat. Then frame the subject as a **design tree**: every decision
branches into the decisions that hang off it.

**Done when:** the client answers and the tree has a first frontier of
candidate questions.

## 1. Weigh the frontier (one Jev call)

The **frontier** is every decision whose prerequisites are already
settled: the only questions asked honestly yet. Before asking a round,
Jev weighs every candidate. Draft 2–4 candidate recommendations per
question first, then ask everything in one fan-out call — frontier
judgments plus speculative recommendation picks — and consume only the
survivors':

```json
{
  "state": {
    "subject": "Migrate checkout sessions to Redis",
    "settled": ["Stays on Render", "Budget $100/mo"],
    "candidates": [{"id": "q1", "text": "Sync or async session writes?"}],
    "rec_candidates": {"q1": ["Sync: simpler crash story", "Async: protects p99"]}
  },
  "questions": {
    "q1_load_bearing": {
      "type": "noul",
      "instructions": "Does the answer to `candidates[0]` change the outcome of `subject`, given `settled`?"
    },
    "q1_independent": {
      "type": "noul",
      "instructions": "Can `candidates[0]` be answered honestly without knowing the answers to the other open questions?"
    },
    "q1_rec_pick": {
      "type": "choice",
      "instructions": "Given `subject` and `settled`, which recommendation in `rec_candidates.q1` leads best?",
      "criteria": {
        "sync": "Sync: simpler crash story",
        "async": "Async: protects p99",
        "neither": "Neither fits; the question needs reframing."
      }
    }
  }
}
```

Prune candidates below 0.4 load-bearing (the branch stays listed, marked
pruned, so you can resurrect it). Hold dependent candidates for a later
round: a question that hinges on an answer still open belongs to a later
round, not this one. Order the survivors by load-bearing. A `neither`
pick reframes the question instead of asking it.

**Done when:** every question entering the round survived its load-bearing
and independence judgments with a Jev-picked recommendation.

## 2. Ask the round

Ask the whole frontier in one **round**: number each question and give
Jev's recommended answer. Format a round like so:

```
❓ **Q1** - **<question title>**: <question body, including multiple choices>

➡️ <Jev's pick and its confidence>

---

❓ **Q2** - **<question title>**: <question body, including multiple choices>

➡️ <Jev's pick and its confidence>
```

Each ➡️ line carries the pick and its confidence, plainly shown: the
confidence is what earns trust or invites pushback. Flag picks below 0.6
confidence as uncertain and say so on the line. Finding facts is your
job, never the user's: when a question needs something the environment
can settle, look it up or dispatch a subagent; ask only decisions, and
wait for the answers. Answer none of your own questions.

**Done when:** the full round is asked in shape and every answer is heard.

## 3. Weigh the answers (one Jev call)

After the answers land, Jev weighs each one before the tree updates:

- `decided`: Score from "vague, hedged, or nodded along" through
  "answered with a reservation" to "settled; defensible to a stranger".
- `reopens`: Noul — "This answer reopens an earlier settled decision."

Quote the score when you push back: "Jev scores that 0.3 decided — what
would make it a 1.0?" Reopened branches return to the frontier. Answers
scoring high settle their branch and unblock what hung off them.
Recompute the frontier; answers reshape everything downstream.

**Done when:** every answer is scored, pushbacks are queued, and the tree
reflects the settled, the pushed-back, and the reopened.

## 4. Close

The session ends on shared understanding, not an empty frontier. When the
frontier empties, run one last weigh-in over the settled tree — two
Nouls: "Something material is left silently assumed" and "Further rounds
cost more attention than they reveal." Assumed above 0.6 reopens a
frontier question; otherwise converged above 0.6 delivers the log;
anything else asks you whether to continue or close. Then deliver the
decision log in chat: each settled decision with its recommendation
confidence, each pushback and how it resolved, pruned branches with
their scores, and what would reopen each call. End only when you confirm
the understanding is shared; confirmation never authorizes implementation.

**Done when:** the log is delivered and shared understanding is confirmed.

## Sources

Interview mechanics adapted from `grilling` / `grill-me`
(mattpocock/skills). Jev mechanics: `typesafe-ai` skill and TypeSafe
docs. Design debts: OntoAgent (what-to-ask decoupled from how-to-ask);
Mediating Assessments Protocol (independent judgments, global evaluation
delayed to the close); cognitive forcing functions (uncertainty display
plus selective forcing); Bayesian adaptive querying (ask for expected
information gain).
