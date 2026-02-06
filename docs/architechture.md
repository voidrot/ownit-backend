# Architecture & Design

This project follows a modern Django project layout, emphasizing separation of concerns and scalability.

## Directory Structure

The traditional top-level project folder is replaced with distinct `apps/` and `config/` directories.

```text
.
├── apps/               # Django applications
│   ├── core/           # Shared utilities and abstract models
│   ├── pages/          # Static/Marketing pages (e.g., Landing Page)
│   └── users/          # Custom User model and Authentication
├── config/             # Project configuration
│   ├── settings/       # Split settings
│   ├── urls.py         # Main URL routing
│   └── wsgi.py         # WSGI entry point
├── docs/               # Documentation
├── e2e/                # Playwright End-to-End tests
├── templates/          # Global templates (base.html, etc.)
├── tests/              # Unit and Integration tests
├── compose.yml         # Local Docker services
├── Dockerfile          # Multi-stage Docker build
├── mise.toml           # Task runner config
└── pyproject.toml      # Dependency management
```

## Technology Stack

- **Backend**: Django 6.0+ (Python 3.13+)
- **Database**: PostgreSQL (via `psycopg`)
- **Frontend**:
    - **Tailwind CSS**: Utility-first CSS framework.
    - **HTMX**: For dynamic interactions without heavy JS frameworks.
    - **Alpine.js**: (Optional/Ready) for lightweight client-side state.
- **Authentication**: `django-allauth` for comprehensive auth flows (social, email, etc.).
- **Task Queue**: Celery + Redis.
- **Error Tracking**: Sentry SDK.

## Configuration

Settings are managed via **`django-split-settings`** and **`environs`**.

- `config/settings/base.py`: Common settings.
- `config/settings/env/development.py`: Dev-specific overrides.
- `config/settings/env/production.py`: Production security and optimization.
- `config/settings/components/`: Modular settings (e.g., `sentry.py`, `allauth.py`, `tailwind.py`).

Configuration files primarily read from environment variables defined in `.env`.

## Key Apps

### `apps.users`
Contains the custom `User` model. ALWAYS use `get_user_model()` or `settings.AUTH_USER_MODEL` instead of referencing this directly.

### `apps.core`
Intended for base configuration, utility functions, and abstract models that are shared across other apps.

### `apps.pages`
Handles simple static views, like the Landing Page. It serves as an example of how to structure a simple app.
