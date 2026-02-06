import re
from playwright.sync_api import Page, expect


def test_login_page_title(page: Page, live_server):
    # live_server.url gives us the base URL of the running Django server
    page.goto(f'{live_server.url}/accounts/login/')

    # Expect a title "to contain" a substring.
    expect(page).to_have_title(re.compile('Login|Sign In', re.IGNORECASE))
