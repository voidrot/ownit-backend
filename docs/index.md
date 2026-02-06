# Django Starter Template Documentation

Welcome to the documentation for the **Django Starter Template**. This template is designed to kickstart production-ready Django applications with modern tooling and best practices.

## Overview

This project provides a robust foundation for Django web applications, featuring:

- **Security**: Hardened production settings, CSP, and secure authentication.
- **Performance**: Dockerized environment, efficient static file handling.
- **Developer Experience**: Fast tooling with `uv`, `mise` for task management, and comprehensive testing.
- **Maintainability**: Clean project structure and split settings.

## Documentation Sections

- **[Setup Guide](setup.md)**: Prerequisites, installation, and environment configuration.
- **[Architecture](architecture.md)**: Deep dive into the project layout and technology stack.
  - **[Architecture Decisions](architecture/decisions)**: ADRs for architectural decisions.
- **[Testing](testing.md)**: How to run unit and E2E tests, including Aria Snapshots.
- **[Deployment](deployment.md)**: Production settings, Docker builds, and monitoring.

## Quick Start

```bash
mise run install
mise run serve
```
