# AGENTS.md

## Project Vision
Build an agent-driven Health & Nutrition Assistant that:
- Reads Dexcom Clarity PDF exports.
- Interviews the user to fill missing report details.
- Generates consultant-ready weekly reports.
- Produces a mood intake worksheet and final consolidated journal.
- Answers health and nutrition questions in a supportive, evidence-aware way.

## Product Goals
- Replace manual report editing with guided conversational intake.
- Keep traceability from every report row back to source Clarity events.
- Improve report quality and consistency across weeks.
- Preserve user control: agent suggests, user confirms.

## MVP Scope
- Input: one weekly Clarity PDF.
- Parse meal/activity events and timestamps.
- Interview flow:
  - For each parsed meal, ask classification: Breakfast/Lunch/Dinner/Snack.
  - For each period (`After Breaking Fast`, `Around Noon`, `After Dinner`, `Before Bed`), ask mood + energy.
  - Ask before-bed time explicitly.
- Output:
  - Weekly report markdown.
  - Mood intake worksheet markdown.
  - Optional JSON session artifact for audit/debug.

## Out of Scope (MVP)
- Medication reporting.
- Calorie tracking integrations.
- Autonomous treatment recommendations.
- Multi-user authentication.

## Agent Behavior
- Ask before assuming missing information.
- Confirm uncertain PDF extraction details.
- Ask one clear question at a time.
- Offer defaults and allow edits.
- Summarize captured inputs before report generation.

## Required Tooling
- Python runtime/deps with `uv`.
- Config/secrets loaded with `python-dotenv`.
- Deterministic parsing first; LLM reasoning second.
- Structured intermediate data model (events, day periods, responses).

## Developer Commands
- Create venv: `uv venv`
- Install deps: `uv sync`
- Run app: `uv run python scripts/run_agent.py --pdf /path/to/clarity.pdf`
- Run tests: `uv run pytest`

## Environment
- Use `.env` for local settings.
- Commit `.env.example` only.
- Never commit secrets.
