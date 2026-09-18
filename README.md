# jev-me

This repository **replaces** the previous jev-me interview OS. Sqlite, `scripts/write.py`, gates, `session_kind`, and hill-climb leftovers are gone. Do not restore them.

`/jev-me` is [Grill-me](https://github.com/mattpocock/skills/blob/main/skills/productivity/grill-me/SKILL.md) with Jev optional each turn.

It starts a [grilling](https://github.com/mattpocock/skills/blob/main/skills/productivity/grilling/SKILL.md) session. Jev stays off until you ask that turn. If you ask and a closed 2–8 set is already on the table, one TypeSafe Choice is printed beside that question's `➡️` — not as the `➡️`.

The TypeSafe skill is an unmodified reference copy, not a rewrite: [`.agents/skills/jev-me/references/typesafe-ai/SKILL.md`](.agents/skills/jev-me/references/typesafe-ai/SKILL.md).

## Required

- `TYPESAFE_API_KEY` for Jev calls. Cloud secret or local `.env.local` — never chat, git, or Vercel. Without it, grilling still runs; Jev is skipped and said so.

## Invoke

This skill never self-fires.

- Cursor / Claude Code: `/jev-me`
- Any agent with this repo's skills loaded: use the `jev-me` skill

Ask for Jev on a turn with `jev Q2` or `jev this round`.
