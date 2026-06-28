**A lightweight Django-based WebSocket chat API** built with Django, Django Channels, Redis, and background workers (Celery). This repository provides REST endpoints, WebSocket consumers for real-time chat, and background task processing for scalable chat features.

**Quick Links**
- **Settings:** [config/settings.py](config/settings.py)
- **ASGI entrypoint:** [config/asgi.py](config/asgi.py)
- **WebSocket consumer:** [modules/chat/websocket/consumers.py](modules/chat/websocket/consumers.py)
- **WebSocket routing:** [modules/chat/websocket/routing.py](modules/chat/websocket/routing.py)
- **Makefile tasks:** [Makefile](Makefile)

**Highlights**
- Real-time chat over WebSockets using Django Channels and Redis as channel layer.
- Persistent chat models: conversations, messages, reactions, statuses, pins.
- Background workers: Celery configured to use Redis.
- Authentication via Clerk middleware integrated into ASGI pipeline.

**Requirements**
- Python >= 3.13 (see `pyproject.toml`)
- PostgreSQL (configured via `config/settings.py`)
- Redis for channels & task brokers
- Optional: Supabase/S3 credentials for media storage

Installation (development)
- Create virtual environment and install dependencies (uses `uv`/hatch via `pyproject.toml`):

```bash
python -m venv .venv
source .venv/bin/activate
uv sync --extra dev
```

- Install pre-commit hooks (optional):

```bash
.venv/bin/pre-commit install
```

Environment
- Copy or create a `.env` file at the project root. Key environment variables used by the project (non-exhaustive):

- **Database:** `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
- **Redis:** `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`, `REDIS_USERNAME`, `REDIS_USE_SSL`
- **Clerk / Auth:** `CLERK_API_URL`, `CLERK_JWKS_URL`, `CLERK_SECRET_KEY`, `CLERK_ISSUER`
- **Supabase / S3:** `SUPABASE_PROJECT_URL`, `SUPABASE_S3_ENDPOINT_URL`, `SUPABASE_S3_REGION`, `SUPABASE_S3_ACCESS_KEY_ID`, `SUPABASE_S3_SECRET_ACCESS_KEY`
- **Django secret & debug:** `DJANGO_SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `ENVIRONMENT`

Development commands
- Run Django dev server (HTTP + ASGI) with automatic reload:

```bash
make run
```

- Run the WebSocket ASGI server directly with `uvicorn` (local testing):

```bash
make run-websocket
# or
uvicorn config.asgi:application --reload
```

- Run Celery:

```bash
make celery
```

Testing & quality
- Run tests: configured with `pytest` (see `pyproject.toml`):

```bash
uv run pytest
```

- Lint / format / type-check:

```bash
make lint
make format
make type-check
```

WebSocket API
- Chat WS URL pattern (see [modules/chat/websocket/routing.py](modules/chat/websocket/routing.py)):

- `ws/conversations/<conversation_id>/` - connects authenticated user to conversation group.

- Authentication: requests pass through `ClerkAuthMiddleware` defined in [config/asgi.py](config/asgi.py).
- `ChatConsumer` ([modules/chat/websocket/consumers.py](modules/chat/websocket/consumers.py)) - handles sending messages, delivery receipts, pin/unpin, reactions, and broadcast events. `UserPresenceConsumer` ([modules/user/websocket/consumers.py](modules/user/websocket/consumers.py)) - handles user presence events (online/offline).

Project structure (top-level)
- `config/` - Django configuration and ASGI/WGI entrypoints
- `modules/` - Django apps (chat, user, media, etc.)
- `base/` - shared utilities, middleware, authentication, consumers base classes
- `services/` - external services wrappers (Redis, S3, clerk, websockets helpers)
- `templates/` - error templates and helpers
- `utils/` - helper utilities

Further reading / TODOs
- Add a more detailed API reference (REST endpoints and message payload schemas).
- Document deployment steps (Docker, Fly, cloud providers) and production-ready configuration for SSL and secrets.

**Module functions and user-facing features**

Chat
- Create conversations: direct and group conversations, with initial system messages for direct chats.
- Conversation membership: add/list members, roles (owner/admin/member), and last-read tracking.
- Send messages: text/media messages with reply/quote support.
- Delivery & read receipts: mark messages as delivered/read and notify senders.
- Edit & revisions: edit messages and maintain revision history.
- Delete messages: hide for a specific user or delete for everyone (with notifications).
- Pin/unpin messages and list pinned items.
- Reactions: add/remove reactions on messages and notify participants.
- Message visibility: per-user visibility (hide/unhide) and last-visible message handling.
- User aliases: per-member nicknames inside conversations.
- Real-time events: WebSocket events for new messages, updates, delivery/read, pins, reactions, user presence.

Friends
- Friendship checks: determine whether two users are friends.
- Friend lists: retrieve friend IDs for a user.
- (Friends are stored bidirectionally when a request is accepted.)

Friend requests
- Send friend requests (create pending requests).
- Accept or reject requests (acceptance creates Friend records).
- Cancel pending requests.
- Query pending/related friend requests.

User (side/user-facing features)
- Authentication: uses Clerk middleware for authenticated WebSocket and HTTP requests.
- Profile management: user profiles include username, email, avatar, and display name.
- Presence: online/offline tracking, heartbeat, last-seen, and broadcasting presence to friends and conversation members.
- Caching: user cache clearing utilities to keep profile-related caches fresh.
- Avatar/media integration: hooks for Supabase/S3-backed media storage (configurable via environment).
