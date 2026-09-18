# jev-me

`/jev-me` is [Grill-me](https://github.com/mattpocock/skills/blob/main/skills/productivity/grill-me/SKILL.md) with Jev optional each turn. It starts a [grilling](https://github.com/mattpocock/skills/blob/main/skills/productivity/grilling/SKILL.md) session. Jev stays off until you ask that turn. If you ask and a closed 2–8 set is already on the table, one TypeSafe Choice is printed beside that question's `➡️` — not as the `➡️`.

Clone this repo into your agent's skills directory so `SKILL.md` is at the folder root:

```bash
git clone https://github.com/jon-devlapaz/jev-me.git ~/.agents/skills/jev-me   # Cursor
git clone https://github.com/jon-devlapaz/jev-me.git ~/.claude/skills/jev-me  # Claude Code
```

Install [grilling](https://github.com/mattpocock/skills/tree/main/skills/productivity/grilling) the same way. Then type `/jev-me`. Ask for Jev with `jev Q2` or `jev this round`.

`TYPESAFE_API_KEY` is required for Jev (Cloud secret or `.env.local` — never chat, git, or Vercel). Without it, grilling still runs; Jev is skipped.
