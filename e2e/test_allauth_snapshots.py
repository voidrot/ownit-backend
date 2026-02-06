from playwright.sync_api import Page, expect


def test_login_page_aria_snapshot(page: Page, live_server):
    page.goto(f'{live_server.url}/accounts/login/')
    page.wait_for_selector('.card')
    expect(page.locator('body')).to_match_aria_snapshot("""
        - main:
          - heading "Sign In" [level=1]
          - paragraph:
            - text: If you have not created an account yet, then please
            - link "sign up":
              - /url: /accounts/signup/
            - text: first.
          - text: Login
          - textbox "Username or email"
          - text: Password
          - textbox "Password"
          - list:
            - listitem: At least 8 characters
            - listitem: Cannot be entirely numeric
          - checkbox "Remember Me"
          - text: Remember Me
          - button "Sign In"
    """)


def test_signup_page_aria_snapshot(page: Page, live_server):
    page.goto(f'{live_server.url}/accounts/signup/')
    page.wait_for_selector('.card')
    expect(page.locator('body')).to_match_aria_snapshot("""
        - main:
          - heading "Sign Up" [level=1]
          - paragraph:
            - text: Already have an account? Then please
            - link "sign in":
              - /url: /accounts/login/
            - text: .
          - text: Email
          - textbox "Email address"
          - text: Username
          - textbox "Username"
          - text: Password
          - textbox "Password"
          - list:
            - listitem: At least 8 characters
            - listitem: Cannot be entirely numeric
          - button "Sign Up"
    """)


def test_password_reset_page_aria_snapshot(page: Page, live_server):
    page.goto(f'{live_server.url}/accounts/password/reset/')
    page.wait_for_selector('.card')
    expect(page.locator('body')).to_match_aria_snapshot("""
        - main:
          - heading "Password Reset" [level=1]
          - paragraph: Forgotten your password? Enter your email address below, and we'll send you an email allowing you to reset it.
          - text: Email
          - textbox "Email address"
          - button "Reset My Password"
          - paragraph: Please contact us if you have any trouble resetting your password.
    """)
