# AI-Powered Workflow Story: C9 FearlessZero

This project was built for the $1,000 Bonus Prize category: Best AI-Powered Workflow Story.

## Toolchain

- JetBrains PyCharm 2025.3 Pro
- Codex Agent in the shared project workspace
- Python 3.14 virtualenv
- FastAPI, Pydantic, pytest, httpx
- Plain HTML/CSS/JavaScript served by FastAPI

## What AI Accelerated

Codex Agent was used as a hands-on engineering collaborator inside PyCharm, not as a paste-in code generator. The workflow was:

1. Inspect the existing files and backend contracts.
2. Implement tightly scoped code changes.
3. Run local pytest and API smoke checks.
4. Fix failures immediately.
5. Keep frontend styling constrained to the requested esports coaching-terminal aesthetic.

## Backend State Machine

Codex built the official 20-step pro LoL draft state machine with Best-of-5 Fearless semantics. The implementation enforces:

- Ban and pick turn order.
- Current-game duplicate rejection.
- Cross-game Fearless locks.
- Undo integrity.
- Game advancement only after a complete 20-step draft.

The agent also added tests that prove locks persist from Game 1 into Games 2 and 3.

## Alpha-Beta Pool-Pinch Solver

Codex implemented the deterministic solver in multiple passes. The first version produced valid top moves, then the workflow tightened it for coaching usefulness:

- Active-side gain scoring.
- Distinct deterministic tactical deltas.
- Player-specific reasoning.
- Exact S/A/B proficiency tier awareness.
- Role scarcity multipliers.
- Flex-steal and team-comp disruption values.

The final output reads like a coaching note, for example: denying a named player on a named role and showing the resulting pool count.

## Test-Driven Verification

PyCharm and Codex made it practical to keep tests close to the engine work. The suite verifies:

- Full draft sequence.
- Fearless lock persistence.
- Illegal locked pick rejection.
- Undo behavior.
- Comfort Collapse Index behavior.
- Solver latency under the requested threshold.
- Game 3 pinch demo state with exactly 20 prior locks.
- Distinct top-3 solver deltas with player names in tactical reasons.

## Zero-AI-Slop Frontend

The UI was built with strict constraints to avoid generic generated-dashboard patterns:

- No gradients.
- No drop shadows.
- No glassmorphism.
- No emojis.
- No marketing hero page.
- Fixed split-panel `100vh` war-room layout.
- Crisp 1px hairline borders.
- Riot Data Dragon champion portraits.
- Dense coach-facing tables and controls.

Codex respected the visual system while wiring real API calls, keyboard shortcuts, the Coach Brief modal, and the one-click Game 3 pinch demo.

## Why This Workflow Matters

The advantage was not raw code volume. The value came from keeping an AI agent inside the same engineering loop a human would use:

- Read the repo.
- Match existing contracts.
- Build incrementally.
- Verify with tests.
- Smoke-test the live app.
- Document the decisions.

That workflow turned a hackathon concept into a deterministic, testable, locally runnable coaching tool with a polished frontend and a credible tactical engine.
