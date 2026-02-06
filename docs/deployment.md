# Deployment

This project conforms to the **Twelve-Factor App** methodology and is designed to be deployed as a Docker container.

## Production Configuration

Production settings are located in `config/settings/envs/production.py`.
They are automatically activated when `DJANGO_ENV=production`.

### Key Environment Variables

Ensure these are set in your production environment (e.g., AWS, Heroku, DigitalOcean):

- `DJANGO_ENV=production`
- `DJANGO_SECRET_KEY`: A long, random string.
- `DATABASE_URL`: Connection string for your production PostgreSQL database.
- `SENTRY_DSN`: For error monitoring.
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_STORAGE_BUCKET_NAME`: If using S3 for static/media files.

## Docker Build

The `Dockerfile` is a multi-stage build optimized for size and security.

1.  **Build the image**:
    ```bash
    docker build -t my-django-app .
    ```

2.  **Run the container**:
    ```bash
    docker run -p 8000:8000 --env-file .env.prod my-django-app
    ```

## Static Files

In production, `Whitenoise` is configured to serve compressed static files.
Run `collectstatic` during the build process or startup (handled by the entrypoint).

## Security Check

Before deploying, run the deployment check:

```bash
uv run python manage.py check --deploy
```

This ensures all security settings (SSL, cookies, HSTS) are correctly configured.
