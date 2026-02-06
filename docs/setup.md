# Setup Guide

This guide covers how to set up the project for local development.

## Prerequisites

Ensure you have the following installed:

1.  **Docker & Docker Compose**: For running services like PostgreSQL and Redis.
2.  **[Mise](https://mise.jdx.dev/)**: A tool for managing environment variables and running tasks.
    - Install instructions: https://mise.jdx.dev/getting-started.html

The project handles Python installation automatically via `uv` (managed by `mise`).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd <project-directory>
    ```

2.  **Install dependencies**:
    ```bash
    mise run install
    ```
    This command uses `uv sync` to create a virtual environment (`.venv`) and install all required packages defined in `pyproject.toml`.

3.  **Setup Environment Variables**:
    - Copy the template:
      ```bash
      cp .env.template .env
      ```
    - Review `.env` and fill in any required values (e.g., specific secrets if needed, though defaults work for dev).

4.  **Apply Migrations**:
    ```bash
    # Ensure Docker services are running if you want to use the DB
    mise run docker-up -d
    
    # Run migrations
    uv run python manage.py migrate
    ```

## Running the Application

### Shell Mode (Fastest for Dev)

Run the development server natively on your machine:

```bash
mise run serve
```

This starts:
- Django development server (localhost:8000)
- Tailwind CLI (watch mode for CSS updates)

### Docker Mode

Run the entire application stack in Docker:

```bash
mise run docker-up
```

Access the app at `http://localhost:8000`.

## Common Commands

All tasks are defined in `mise.toml`.

- **Run Tests**: `mise run test`
- **Lint Code**: `mise run lint` (Runs `ruff` and `djlint` checkers)
- **Format Code**: `mise run format` (Applies fixes)
- **Clean Cache**: `mise run clean`
