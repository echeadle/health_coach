# Health Coach Agent Implementation Plan

## Objective
Build an agent-driven workflow that uses existing `health_coach` code as tools, interviews the user for missing details, and generates:
- Weekly report markdown
- Mood intake worksheet markdown
- Session artifact for traceability/debugging

## Current Baseline
- Parser and models exist.
- Interview flow exists (meal classification, mood/energy, before-bed time).
- Report and worksheet renderers exist.
- CLI supports PDF runs, worksheet-only mode, and day filtering.

## Phase 1: Agent Contract (Foundation)
### Goals
- Define a stable input/output contract for the agent.
- Define required user questions and confirmation checkpoints.

### Deliverables
- `docs/agent_contract.md` (or equivalent section in README)
- Structured session schema (JSON-friendly) including:
  - source PDF
  - selected day(s)
  - meal classifications
  - period check-ins
  - generated output file paths

### Acceptance Criteria
- Contract clearly states required inputs, optional inputs, and outputs.
- All required interview questions are listed explicitly.

## Phase 2: Tool Wrappers Around Existing Code
### Goals
Create explicit callable tools so orchestration logic is clean and testable.

### Tool List
1. `parse_clarity_pdf(pdf_path)`
2. `choose_days(available_days, requested_days)`
3. `classify_day_meals(day_summary)`
4. `collect_day_period_checkins(day_summary, classified_meals)`
5. `assemble_session(...)`
6. `render_report(session)`
7. `render_mood_worksheet(session)`
8. `save_outputs(report_text, worksheet_text, output_dir)`

### Deliverables
- New module: `src/health_coach/tools.py`
- Unit tests for each tool boundary.

### Acceptance Criteria
- Existing CLI can call tools without behavior regression.
- Tests for tools pass in non-interactive mode.

## Phase 3: Conversation Orchestrator (Agent Loop)
### Goals
Add an orchestration layer that drives Q&A flow and tool execution.

### Core Behavior
- Ask: "What day or days do you want to work on?"
- For each selected day:
  - confirm meal classifications
  - ask before-bed time
  - ask energy and mood with 1-5 reminder
- Show per-day summary for confirmation.
- Show final weekly summary before writing files.

### Deliverables
- New module: `src/health_coach/agent.py`
- CLI entry option to run orchestrator mode.

### Acceptance Criteria
- User can complete a full run using only agent prompts.
- Agent can skip non-selected days.

## Phase 4: Pilot Week Run and Gap Fixes
### Goals
Run one real week with user and improve tools/prompts based on observed friction.

### Pilot Checklist
- [ ] Parse a real weekly PDF
- [ ] Select one day first, verify flow
- [ ] Run all days for the week
- [ ] Review generated markdown
- [ ] Log confusing prompts or wrong anchors
- [ ] Patch issues and rerun

### Acceptance Criteria
- User can complete a week without manual file edits.
- Output format matches preferred layout.

## Phase 5: Hardening and Handoff
### Goals
Make workflow resilient and easy to resume.

### Deliverables
- Session artifact file: `Reports/session_<start>_to_<end>.json`
- Resume notes in README
- Error-handling improvements (bad date input, missing PDF data)
- Regression tests for representative week

### Acceptance Criteria
- Failed/interrupted runs can be resumed from saved session data.
- README has exact commands for common workflows.

## Execution Order for Next Work Session
1. Implement `tools.py` wrappers.
2. Refactor current CLI to call wrappers.
3. Add `agent.py` orchestrator with day-question first.
4. Run one-day pilot from real PDF.
5. Run full-week pilot and patch issues.

## Commands (Current)
- Run tests:
  - `uv run pytest`
- Run with PDF:
  - `uv run python scripts/run_agent.py --pdf <path-to-clarity.pdf>`
- Run worksheet-only:
  - `uv run python scripts/run_agent.py --worksheet-only`

## Notes for Restarting After Context Reset
- This file is the source of truth for implementation sequence.
- Continue from the first incomplete phase.
- Keep changes isolated under `health_coach/`.
