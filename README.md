# Jev-Me

Type `/jev-me` and answer a few questions about a plan. A second model
named **Jev** scores which questions change the plan and whether your
answers actually settle them. When you confirm the log, that is not a
license to implement.

You do not need a finished plan to start. Producing one is what the
session is for.

## Install

1. Clone this skill into your personal skills folder:

   ```
   git clone https://github.com/jon-devlapaz/jev-me.git ~/.agents/skills/jev-me
   ```

2. Install the [`typesafe-ai`](https://github.com/typesafe-ai/skills)
   skill so the agent can call Jev:

   ```
   npx skills add typesafe-ai/skills --skill typesafe-ai
   ```

   Pick Cursor when prompted. Add `-g` to install it globally.

3. Set `TYPESAFE_API_KEY` in the environment. Do not paste the key into
   chat. The agent also needs `python3` and `uv` on your `PATH`.

4. In a **new** Cursor chat, type `/jev-me`. If it is not offered,
   start a new chat after the clone.

The agent will not start this skill by itself. Cloning into
`~/.agents/skills/jev-me` is what makes `/jev-me` available from other
projects.

## How to answer

- Answer numbered questions in your own words. A reason beats a nod.
- "Looks good" is not an answer. The session will push back.
- "I don't know" is a real answer.
- Push back on a question that is beneath the call you actually need.
- Stop when the log matches what you decided. Confirming it does not
  start implementation.

## Inspect

Interviews are stored in this skill folder, not in your project.

```
python3 ~/.agents/skills/jev-me/audit/write.py list
python3 ~/.agents/skills/jev-me/audit/write.py log --session <id>
```

The full rules the agent follows are in [SKILL.md](SKILL.md).

## Related work

Interview steps come from `grilling` / `grill-me`
([mattpocock/skills](https://github.com/mattpocock/skills)).

Jev mechanics come from the `typesafe-ai` skill and TypeSafe docs.

For architecture work that needs a full decision engine, use
[jev-decisions](https://github.com/jon-devlapaz/jev-decisions).
