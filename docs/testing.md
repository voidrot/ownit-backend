# Testing

Reliable testing is core to this project's philosophy. We use **Pytest** for all test execution.

## Running Tests

Execute all tests (Unit + E2E):

```bash
mise run test
```

Or run `pytest` directly:

```bash
uv run pytest
```

## Testing Strategies

### 1. Unit & Integration Tests
Located in `tests/` and within `apps/<app_name>/tests/`.
These tests use `pytest-django` to interact with the database and verify views, models, and utility functions.

Example:
```python
def test_landing_page(client):
    response = client.get("/")
    assert response.status_code == 200
```

### 2. End-to-End (E2E) Tests
Located in `e2e/`.
We use **Playwright** (`pytest-playwright`) to test the application behaves correctly in a real browser environment.

#### Aria Snapshots (Structural Testing)
To avoid brittle tests that break with every CSS change, we strictly use **Aria Snapshots**.
This verifies the *accessibility tree* (the meaningful structure of the page) rather than pixels.

**Good Pattern (`to_match_aria_snapshot`)**:
```python
from playwright.sync_api import expect

def test_page_structure(page, live_server):
    page.goto(live_server.url)
    expect(page.locator("body")).to_match_aria_snapshot("""
        - heading "Welcome" [level=1]
        - button "Login"
    """)
```
This test passes even if you change the button color or font size, but fails if you remove the button.

**Bad Pattern (Visual Screenshots)**:
Do NOT use `to_have_screenshot()` for general UI testing as it is too sensitive to minor style updates.

## Writing New Tests
1.  Create a file starting with `test_` in `tests/` or `e2e/`.
2.  Use fixtures like `client` (Django) or `page` (Playwright).
3.  Run `mise run test`.
