# How to use Claude Code on FarmNex (for the team)

This repo is set up so Claude Code already knows the project, its rules, the list of problems to fix,
and how the four components plug in. You just give short commands.

## What's in the setup

| File | What it's for |
|---|---|
| `CLAUDE.md` | Project rules Claude reads every time (DB safety, security, how to explain things) |
| `backend/CLAUDE.md`, `frontend/CLAUDE.md` | Extra rules when working in each folder |
| `docs/FIX_PLAN.md` | Every known problem, in order, with how to check it's fixed |
| `docs/STATUS.md` | Progress + decisions — Claude updates it after each task |
| `docs/integration/*.md` | How Crop Rescue, AI forecaster, route optimizer and voice assistant plug in |
| `backend/migrations/` | SQL for new component tables — **you** run these in Supabase |
| `.claude/commands/` | The shortcuts below |
| `.claude/agents/security-reviewer.md` | A second Claude that checks security changes |
| `.claude/settings.json` | Stops Claude from reading `.env`/keys, force-pushing, or `rm -rf` |

## The shortcuts

| Type this | What happens |
|---|---|
| `/fix F1 payment` | Fixes one item from the fix plan (here: ownership checks for payments), tests it, ticks it off |
| `/integrate crop-rescue` | Plugs a component in, step by step, after showing you the plan |
| `/connect-screen listing` | Switches one app screen from fake data to the real backend |
| `/check` | Runs all checks and tells you in simple words what passed or failed |

Component names for `/integrate`: `crop-rescue`, `ai-forecaster`, `route-optimizer`, `voice-assistant`.

## Suggested order

1. **Security first (before any demo):**
   `/fix F1 payment` → `/fix F1 bid` → `/fix F1 bid_event` → `/fix F1 order` → … (one module each,
   order is in FIX_PLAN F1), then `/fix F2`, `/fix F3`.
2. **Clean up and make deploys reliable:** `/fix F4` … `/fix F11`.
3. **Crop Rescue** (top feature): `/integrate crop-rescue`, then `/connect-screen rescue`.
4. **AI forecaster:** `/integrate ai-forecaster`.
5. **Marketplace logic** (orders, bids, 20% advance): `/fix F12` — plan it together first.
6. **Route optimizer:** `/integrate route-optimizer`, then `/connect-screen logistics`.
7. **Voice assistant:** `/integrate voice-assistant` (needs step 1 done).
8. Remaining screens: `/connect-screen listing`, `market`, `cart`, `bidding`, `waste`, `admin`.

## Things only you can do

- Run SQL files from `backend/migrations/` in the Supabase SQL editor.
- Set environment variables on FastAPI Cloud (Claude will list exactly which).
- Deploy separate services (the forecaster, the voice assistant).
- Test on a real phone.

## Tips

- One fix or one component per session/branch keeps things easy to review.
- If Claude's explanation is too technical, say "explain simpler" — `CLAUDE.md` tells it to.
- If something looks wrong, ask Claude to run the `security-reviewer` agent on the current changes.
