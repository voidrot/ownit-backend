from playwright.sync_api import Page, expect


def test_landing_page_loads(page: Page, live_server):
    page.goto(f'{live_server.url}/')
    expect(page).to_have_title('Welcome to Django Starter')
    expect(page.locator('h1')).to_contain_text('Hello!')

    # Snapshot test logic
    expect(page.locator('body')).to_match_aria_snapshot(r"""
        - banner:
          - link "Django Starter":
            - /url: /admin/
          - list:
            - listitem:
              - link "Login":
                - /url: /accounts/login/
            - listitem:
              - link "Sign Up":
                - /url: /accounts/signup/
        - main:
          - heading "Hello!" [level=1]
          - paragraph: Welcome to your new Django project.
          - link "Login":
            - /url: /accounts/login/
          - link "Sign Up":
            - /url: /accounts/signup/
        - contentinfo:
          - complementary:
            - paragraph: /Copyright © \d+ - All right reserved by Your Company/
    """)
