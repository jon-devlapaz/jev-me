# Jev-Me

Jev-Me is an agent skill. The skill runs an interview about a plan or a
design. A second model named **Jev** scores each step. You type `/jev-me`
to start. The agent does not start the skill by itself.

The full rules are in [SKILL.md](SKILL.md).

## What the skill does

The agent asks you the questions that change the plan. Jev scores:

- which questions to ask now
- which recommended answer to show
- whether your answer is a decision
- when the interview can stop

The agent uses those scores. The agent does not guess the next step in
prose.

## Who it is for

The skill is for a **person**. You want a plan from an interview. You
want results that you can predict. The interview agent is often too sure
and not reliable. Jev limits that agent.

The skill is not a general tool for all LLM work. The skill is not an
autonomous planner. A confirmed log is not a license to implement.

## Quick start

1. Set `TYPESAFE_API_KEY` in the environment. Do not paste the key into
   chat.
2. Install the [`typesafe-ai`](https://github.com/typesafe-ai/skills)
   skill for the Jev client.
3. Type `/jev-me`.
4. Answer the numbered questions. Do not reply only with "looks good".
5. Stop when you confirm shared understanding.

## How it works

The steps in `SKILL.md` are a **loop**, not a line.

1. **Open.** The agent tests Jev with one small question. Then the agent
   writes 6–8 candidate questions about the plan.
2. **Weigh the pool.** One Jev call scores each candidate. The agent
   removes weak questions, holds dependent questions, and finds facts.
   The agent asks at most **four** questions.
3. **Ask the round.** Each question shows Jev's recommended answer and
   the confidence. If confidence is low, the agent shows the split. The
   agent does not give a winner.
4. **Weigh the answers.** One Jev call scores each answer. Agreement
   with no reason is not a decision. The question stays open.
5. **Close.** Jev checks silent assumptions. Then the agent writes a
   decision log. You confirm. That confirm does not start
   implementation.

If you stop in the middle, the agent stops. Open questions stay open.

## Words this skill uses

| Word | Meaning |
| --- | --- |
| **Jev** | The TypeSafe System One model. It returns typed scores. |
| **Pool** | The questions that you can ask now. |
| **Round** | At most four questions from the pool. |
| **Noul** | A yes/no probability from 0 to 1. A value near 0.5 means "I do not know". It does not mean "medium". |
| **Score** | A position on named levels. Use Score when the answer is a range, not yes/no. |
| **Fact** | Something the agent can find in files or tools. Do not ask the user. |
| **Decision** | Something two persons can still disagree about. Ask the user. |

## Requirements

- A Jev client. Put `TYPESAFE_API_KEY` in the environment. The skill
  checks the client. The skill does not handle the key.
- The [`typesafe-ai`](https://github.com/typesafe-ai/skills) skill for
  Jev API mechanics.

## Related work

Interview steps come from `grilling` / `grill-me`
([mattpocock/skills](https://github.com/mattpocock/skills)).

Jev mechanics come from the `typesafe-ai` skill and TypeSafe docs.

For architecture work that needs a full decision engine, use
[jev-decisions](https://github.com/jon-devlapaz/jev-decisions).
