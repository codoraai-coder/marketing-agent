
# Content Distribution Agent (MCP-style) — Python Backend (FastAPI)

This is a working backend that follows the MCP-style tool pattern described in the design doc. It exposes a small set of agent tools via HTTP, runs an async worker/scheduler, and includes a mock Instagram connector. It uses SQLite for storage and is self-contained — no external services required.

## Features in this MVP
- **MCP-like tools** (HTTP endpoints) the agent (or you) can call:
  - `repurpose_reel_to_post` — turn a "reel transcript" into a cross-platform post + hashtags.
  - `schedule_post` — persist a scheduled post and enqueue a publishing task at the given time.
  - `publish_reel` — immediately publish via a platform connector (mock Instagram here).
  - `fetch_engagement_metrics` — returns fake metrics and stores analytics.
- **Agent** — a tiny heuristic caption/hashtag generator with A/B option.
- **Scheduler & Worker** — in-process asyncio scheduler + queue; safe for single-instance demos.
- **Connectors** — base class + Instagram mock (logs instead of calling real APIs).
- **Storage** — SQLite with SQLAlchemy models for posts, schedules, analytics.
- **FastAPI** — OpenAPI docs at `/docs` for quick testing.

> Notes
> - This MVP avoids real platform APIs so it runs anywhere. Swap the mock connector with real implementations later.
> - For multi-instance production, replace the scheduler with a durable queue (Redis/Rabbit/Kafka) and a separate worker process.

## Quickstart

### 1) Local (Python 3.10+)
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000/docs to try endpoints.

### 2) Docker
```bash
docker build -t content-agent .
docker run -p 8000:8000 content-agent
```

## Key Endpoints
- `POST /tools/repurpose_reel_to_post`
- `POST /tools/schedule_post`
- `POST /tools/publish_reel`
- `GET  /tools/fetch_engagement_metrics`
- `GET  /health`

## Minimal Flow
1. Call `POST /tools/repurpose_reel_to_post` with a transcript to get platform-optimized text.
2. Call `POST /tools/schedule_post` (or `publish_reel`) with the content.
3. The in-process scheduler triggers the worker which calls the mock connector.
4. Check `/tools/fetch_engagement_metrics?post_id=...` for (fake) analytics.

## Swapping Connectors
- Implement `PlatformConnector` for platforms (Instagram, TikTok, YouTube).
- Register in `app/services/registry.py`.

## Project Layout
```
app/
  main.py                 # FastAPI app, background workers, routes
  db.py                   # SQLite engine + session
  models/                 # SQLAlchemy models
  connectors/             # Base + Instagram mock
  services/
    registry.py           # MCP-like tool registry
    scheduler.py          # Async scheduler + worker
    agent.py              # Simple caption/hashtag logic
    media.py              # (stub) media helpers
    analytics.py          # Analytics collection helpers
  utils/time.py           # helpers for timezone-aware scheduling
requirements.txt
Dockerfile
README.md
```

## License
MIT — do whatever you want, no warranty.
