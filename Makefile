# Help command
help:
	@echo "Available commands:"
	@echo "  make git-stash          Stash all changes except the Makefile and ruff.toml"
	@echo "  make git-unstash        Unstash all changes"
	@echo "  make install            Install dependencies"
	@echo "  make dev-install        Install development dependencies and set up pre-commit hooks"
	@echo "  make lint               Run ruff linter"
	@echo "  make format             Format code using ruff"
	@echo "  make type-check         Run mypy for type checking"
	@echo "  make pre-commit         Run pre-commit hooks on all files"
	@echo "  make clean              Clean up temporary files and caches"
	@echo "  make django-check       Run Django system checks"
	@echo "  make makemigrations     Create new migrations based on the changes detected to your models"
	@echo "  make migrate            Apply migrations to the database"
	@echo "  make shell              Open Django shell"
	@echo "  make run                Run Django development server"
	@echo "  make run-websocket      Run WebSocket server with Uvicorn"
	@echo "  make celery             Start Celery worker"
	@echo "  make celery-beat        Start Celery beat scheduler"
	@echo "  make flower             Start Flower for monitoring Celery tasks"
	@echo "  make help               Show this help menu"

# Git commands
git-stash:
	# Exit immediately if a command exits with a non-zero status.
	set -e

	git add . ":!Makefile" ":!ruff.toml"
	git stash --staged -m "local"
	git status

git-unstash:
	# Exit immediately if a command exits with a non-zero status.
	set -e

	git stash pop stash@{0}
	git restore --staged .
	git status

# Dependency management
install:
	uv sync

dev-install:
	uv sync --extra dev
	.venv/bin/pre-commit install

# Linting and formatting
lint:
	uv run ruff check .

format:
	uv run ruff format .
	uv run ruff check --fix .

type-check:
	uv run mypy .

pre-commit:
	uv run pre-commit run --all-files

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf htmlcov/ .coverage

# Django commands
django-check:
	uv run python manage.py check

makemigrations:
	uv run python manage.py makemigrations

migrate:
	uv run python manage.py migrate

shell:
	uv run python manage.py shell

run:
	uv run python manage.py runserver

run-websocket:
	uvicorn config.asgi:application --host 127.0.0.1 --port 8000 --reload

# Celery commands
celery:
	uv run celery -A config worker --loglevel=INFO

celery-beat:
	uv run celery -A config beat --loglevel=INFO

flower:
	uv run celery -A config flower --port=5000
