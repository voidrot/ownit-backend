# Django Starter Template

A production-ready, secure, and modern Django project template.

## Features

- **Modern Tooling**: Managed by `uv` for lightning-fast dependency resolution.
- **Dockerized**: Multi-stage `Dockerfile` and `compose.yml` for local development.
- **Strict Config**: `django-split-settings` and `environs` for robust configuration.
- **Authentication**: `django-allauth` pre-configured with a custom User model.
- **Testing**:
    - `pytest` for unit tests.
    - `playwright` for end-to-end tests with **Aria Snapshots** for ensuring structural integrity.
- **Monitoring**: `sentry-sdk` integration ready to go.
- **Best Practices**:
  - root-level `apps/` and `config/`.
  - `ruff` for linting and formatting.
  - Security hardening in production settings.

## Getting Started

### Prerequisites

- Docker & Docker Compose
- [mise](https://mise.jdx.dev/) (for managing environment and tasks)

### Local Development (Shell)

1. **Install Dependencies**:
   ```bash
   mise run install
   ```
   This will create a `.venv` and sync dependencies using `uv`.

2. **Run Server**:
   ```bash
   mise run serve
   ```
   This runs the Django dev server along with the Tailwind CLI in watch mode.

3. **Run Tests**:
   ```bash
   mise run test
   ```
   Runs both unit tests and Playwright E2E tests.

### Local Development (Docker)

1. **Build and Start**:
   ```bash
   mise run docker-up
   ```
   The app will be available at http://localhost:8000.

## Project Structure

- `apps/`: Django applications.
  - `core/`: Core functionality and shared utilities.
  - `pages/`: Static pages (Landing page, etc.).
  - `users/`: Custom user model and auth logic.
- `config/`: Configuration root.
  - `settings/`: Split settings (`base.py`, `development.py`, `production.py`, `components/`).
- `e2e/`: End-to-End tests using Playwright.
- `tests/`: Unit and integration tests.
- `docker-compose.yml`: Local services (Postgres, Redis).
- `pyproject.toml`: Dependencies and tool config.
- `mise.toml`: Task runner configuration.

## testing

### Snapshot Testing
We use Playwright's `to_match_aria_snapshot()` for E2E tests. This ensures the *accessibility tree* (structure) of pages remains consistent without being brittle to minor styling changes.

## Settings & Environment

Configuration is split into `base.py`, `development.py`, and `production.py`.
Environment variables are handled via `environs`.

### Key Variables
- `DATABASE_URL`: Connection string for PostgreSQL.
- `SENTRY_DSN`: Sentry Data Source Name for error tracking.
- `DJANGO_ENV`: `development` or `production`.

See `.env.example` for a full list (make sure to create `.env` from it).

## Using this Template

To use this for a new project:

1. **Clone/Use Template**.
2. **Rename Project**:
   - Update `name` in `pyproject.toml`.
   - Search and replace `django-starter-template` (if used in any specific config) with your project name.
3. **Reset Git**:
   ```bash
   rm -rg .git
   git init
   ```
4. **Install & Run**: Follow the "Getting Started" guide.
