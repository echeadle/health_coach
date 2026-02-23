# health_coach

Agent-driven weekly Clarity report workflow.

## Quick Start

```bash
uv venv
uv sync --extra dev
uv run python scripts/run_agent.py
```

## Commands

- Interview + report generation from all PDFs in inbox (`CLARITY_INBOX_DIR`, default `Clarity_Inbox/`):

```bash
uv run python scripts/run_agent.py
```

- Interview + report generation from one specific PDF:

```bash
uv run python scripts/run_agent.py --pdf Clarity_Inbox/sample.pdf
```

- Worksheet-only mode:

```bash
uv run python scripts/run_agent.py --worksheet-only
```

After successful PDF processing:
- report + worksheet are written to `REPORTS_OUTPUT_DIR` (default `Reports/`)
- source PDF is archived to `CLARITY_ARCHIVE_DIR` (default `Clarity_Reports/`)

- Run tests:

```bash
uv run pytest
```
