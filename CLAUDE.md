# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

EduBrain AI (`ocsjs-ai-answer-service`) is a Flask service that exposes an OpenAI-backed question-answering API compatible with the [OCS (Online Course Script) AnswererWrapper](https://github.com/ocsjs/ocsjs) custom question-bank protocol. OCS calls `/api/search` with a question, and the service returns an answer in the exact shape OCS expects (`{code, question, answer}`).

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run in development (reads .env; defaults to 0.0.0.0:5000, DEBUG=True)
python app.py

# Run in production
gunicorn -w 4 -b 0.0.0.0:5000 --limit-request-line 16380 app:app

# Smoke-test a running service (health + 4 sample questions against SERVICE_URL, default localhost:5000)
python test_service.py

# Docker
docker compose up --build
# or
docker build -t ai-answer-service . && docker run -p 5000:5000 --env-file .env ai-answer-service
```

There is no unit-test framework — `test_service.py` is an integration smoke test that hits a live server over HTTP and prints results. It is not pytest.

Required env var: `OPENAI_API_KEY` (the app refuses to start without it). See `.env.example` for the full list, including `OPENAI_API_BASE` (for proxies / OpenAI-compatible endpoints), `OPENAI_MODEL`, and `ACCESS_TOKEN`.

## Architecture

Single-process Flask app — no database, no background workers, no job queue. All state lives in process memory and is lost on restart.

- **`app.py`** — all routes and request handling. Holds two module-level globals: `cache` (a `SimpleCache` instance) and `qa_records` (a list capped at `MAX_RECORDS = 100`, trimmed from the front on overflow). Instantiates the `openai.OpenAI` client once at import time using `Config.OPENAI_API_KEY` / `OPENAI_API_BASE`.
- **`config.py`** — the `Config` class reads env vars via `python-dotenv` at import time. All other modules pull settings from this class; do not re-read env vars elsewhere.
- **`utils.py`** — `SimpleCache` (dict keyed by `md5(question|type|options)` with TTL-per-entry), plus the three answer-pipeline helpers: `parse_question_and_options` (builds the prompt), `extract_answer` (post-processes the LLM reply), and `format_answer_for_ocs` (shapes the final JSON).
- **`logger.py`** — defines a rotating-file `Logger` class but **is not wired into `app.py`**, which configures logging via `logging.basicConfig`. Treat `logger.py` as currently unused; if you need file logging, wire it in rather than assuming it already works.
- **`templates/`** — `index.html` (landing page at `/`) and `dashboard.html` (at `/dashboard`, renders `qa_records` + runtime stats). `/docs` renders `api_docs.md` through the optional `markdown` package (not in `requirements.txt`); if absent it falls back to a `<pre>` dump.

### Request flow (`/api/search`)

1. `verify_access_token` — if `Config.ACCESS_TOKEN` is set, require it via `X-Access-Token` header **or** `?token=` query param. Returns 403 on mismatch.
2. Accept `title`, `type`, `options` from query string (GET), JSON body, or form body (POST).
3. Cache lookup keyed on `(question, type, options)`.
4. On miss: build a prompt with `parse_question_and_options`, call `client.chat.completions.create` with a **hardcoded Chinese system prompt** (`app.py:130`) that instructs the model to answer without explanation and to use specific formats per question type.
5. Post-process with `extract_answer` (see quirk below), cache, append to `qa_records`, return via `format_answer_for_ocs`.

### Conventions that matter for OCS compatibility

- **Multiple-choice answer format is `A#B#C`** — OCS splits on `#`. The system prompt tells the model to produce this, and `extract_answer` has a fallback that rebuilds the `#`-joined string if the model returns a comma-separated or prose answer for `type == "multiple"`. Don't change the `#` delimiter.
- **Response schema is fixed**: success → `{code: 1, question, answer}`, error → `{code: 0, msg}`. OCS's handler (`res.code === 1 ? [res.question, res.answer] : [res.msg, undefined]`) depends on both keys.
- **Question types**: `single`, `multiple`, `judgement`, `completion` — these strings come from OCS and are matched literally in `parse_question_and_options` and `extract_answer`.

### Known quirks

- Version strings are duplicated: `/api/health` and `/api/stats` return `"1.0.0"`, while `/dashboard` renders `"1.1.0"` and the module docstring says `1.1.0`. Update all call sites together if bumping.
- `app.py` has a local `start_time = time.time()` inside `search()` (line 74) that shadows the module-level `start_time` used by `/api/stats` and `/dashboard` for uptime — this is only a local variable in that function, so uptime still works, but be aware when reading the code.
- Cache entries are never proactively swept; `SimpleCache.remove_expired` exists but is not called anywhere. Expired entries are only removed lazily on `get()`.
