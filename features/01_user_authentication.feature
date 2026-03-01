# =============================================================================
# Feature 01: User Authentication & Account Management
# Module: apps/users
# JWT Strategy: Access token in memory, Refresh token in HttpOnly cookie
# =============================================================================

@authentication
Feature: User Authentication and Account Management
  As a user of the Task Management SaaS platform
  I want to register, log in, and manage my account securely
  So that I can access the system with proper identity verification

  Background:
    Given the API server is running at "/api/v1"
    And the following system roles exist:
      | Role    |
      | ADMIN   |
      | MANAGER |
      | MEMBER  |

  # ---------------------------------------------------------------------------
  # User Registration
  # ---------------------------------------------------------------------------
  @registration
  Scenario: Successful user registration
    Given I am a new user with no existing account
    When I send a POST request to "/api/v1/auth/register/" with:
      | Field            | Value                |
      | email            | alice@example.com    |
      | first_name       | Alice                |
      | last_name        | Johnson              |
      | password         | SecureP@ss123        |
      | password_confirm | SecureP@ss123        |
    Then the response status should be 201 Created
    And the response body should contain an "access" JWT token
    And the response should set an HttpOnly cookie named "refresh_token"
    And the cookie should have the following attributes:
      | Attribute | Value                        |
      | HttpOnly  | true                         |
      | Secure    | true (in production)         |
      | SameSite  | Lax                          |
      | Path      | /api/v1/auth/token/          |
      | Max-Age   | 604800 (7 days)              |
    And the response body should contain user details:
      | Field      | Value             |
      | email      | alice@example.com |
      | first_name | Alice             |
      | last_name  | Johnson           |
      | role       | MEMBER            |
    And a welcome email task should be dispatched via Celery

  @registration @validation
  Scenario: Registration fails with duplicate email
    Given a user "alice@example.com" already exists
    When I send a POST request to "/api/v1/auth/register/" with email "alice@example.com"
    Then the response status should be 400 Bad Request
    And the error response should contain:
      | code    | message                                     |
      | INVALID | A user with that email already exists.       |

  @registration @validation
  Scenario: Registration fails with weak password
    When I send a POST request to "/api/v1/auth/register/" with password "123"
    Then the response status should be 400 Bad Request
    And the error should indicate password does not meet complexity requirements

  @registration @validation
  Scenario: Registration fails when passwords do not match
    When I send a POST request to "/api/v1/auth/register/" with:
      | password         | SecureP@ss123  |
      | password_confirm | DifferentP@ss  |
    Then the response status should be 400 Bad Request
    And the error should indicate "Passwords do not match"

  # ---------------------------------------------------------------------------
  # Login (JWT Token Obtain)
  # ---------------------------------------------------------------------------
  @login
  Scenario: Successful login with email and password
    Given a verified user exists with email "alice@example.com" and password "SecureP@ss123"
    When I send a POST request to "/api/v1/auth/token/" with:
      | email    | alice@example.com |
      | password | SecureP@ss123     |
    Then the response status should be 200 OK
    And the response body should contain:
      | Field  | Description                           |
      | access | Short-lived JWT (15 minutes)          |
    And the "access" token payload should include custom claims:
      | Claim     | Value             |
      | email     | alice@example.com |
      | role      | MEMBER            |
      | full_name | Alice Johnson     |
    And the response should set an HttpOnly "refresh_token" cookie
    And the "refresh" field should NOT appear in the response body

  @login @rate-limiting
  Scenario: Login is rate-limited after 5 failed attempts
    Given a user "alice@example.com" exists
    When I send 5 failed login attempts within 1 minute
    Then the 6th login attempt should return 429 Too Many Requests
    And the response should include a "Retry-After" header

  @login @validation
  Scenario: Login fails with incorrect credentials
    When I send a POST request to "/api/v1/auth/token/" with:
      | email    | alice@example.com |
      | password | WrongPassword     |
    Then the response status should be 401 Unauthorized

  # ---------------------------------------------------------------------------
  # Token Refresh (Silent Refresh via HttpOnly Cookie)
  # ---------------------------------------------------------------------------
  @token-refresh
  Scenario: Silently refresh access token using HttpOnly cookie
    Given I am logged in and have a valid "refresh_token" cookie
    When I send a POST request to "/api/v1/auth/token/refresh/"
    And the request includes the "refresh_token" cookie automatically
    Then the response status should be 200 OK
    And the response body should contain a new "access" token
    And the old refresh token should be rotated (blacklisted)
    And a new "refresh_token" cookie should be set

  @token-refresh
  Scenario: Token refresh fails with expired cookie
    Given my "refresh_token" cookie has expired (older than 7 days)
    When I send a POST request to "/api/v1/auth/token/refresh/"
    Then the response status should be 401 Unauthorized
    And I should be redirected to the login page on the frontend

  @token-refresh
  Scenario: Frontend auto-refreshes token every 4 minutes
    Given I am logged in on the Angular frontend
    Then the AuthService should schedule a silent refresh timer
    And the timer should fire every 4 minutes
    And each refresh should obtain a new access token
    And the access token should be stored in an Angular signal (memory only)
    And the access token should NOT be stored in localStorage or sessionStorage

  # ---------------------------------------------------------------------------
  # Logout
  # ---------------------------------------------------------------------------
  @logout
  Scenario: Successful logout
    Given I am logged in with a valid session
    When I send a POST request to "/api/v1/auth/logout/"
    Then the response status should be 200 OK
    And the refresh token should be blacklisted in the database
    And the "refresh_token" cookie should be cleared
    And the Angular AuthService should:
      | Action                                    |
      | Clear the access token signal             |
      | Clear the current user signal             |
      | Cancel the refresh timer                  |
      | Navigate to the login page                |

  # ---------------------------------------------------------------------------
  # User Profile (Me Endpoint)
  # ---------------------------------------------------------------------------
  @profile
  Scenario: Retrieve current user profile
    Given I am authenticated as "alice@example.com"
    When I send a GET request to "/api/v1/users/me/"
    Then the response status should be 200 OK
    And the response should contain my profile:
      | Field     | Value                    |
      | id        | <uuid>                   |
      | email     | alice@example.com        |
      | first_name| Alice                    |
      | last_name | Johnson                  |
      | role      | MEMBER                   |
      | avatar    | null or <url>            |
      | phone     | ""                       |
      | job_title | ""                       |

  @profile
  Scenario: Update my profile
    Given I am authenticated as "alice@example.com"
    When I send a PATCH request to "/api/v1/users/me/" with:
      | first_name | Alice Marie             |
      | job_title  | Senior Engineer         |
      | phone      | +1-555-0123             |
    Then the response status should be 200 OK
    And my profile should reflect the updated fields

  # ---------------------------------------------------------------------------
  # Change Password
  # ---------------------------------------------------------------------------
  @password
  Scenario: Successfully change password
    Given I am authenticated as "alice@example.com"
    When I send a POST request to "/api/v1/users/change-password/" with:
      | current_password | SecureP@ss123     |
      | new_password     | EvenMoreSecure!99 |
      | new_password_confirm | EvenMoreSecure!99 |
    Then the response status should be 200 OK
    And I should be able to log in with "EvenMoreSecure!99"

  # ---------------------------------------------------------------------------
  # Password Reset
  # ---------------------------------------------------------------------------
  @password-reset
  Scenario: Request a password reset
    Given a user "alice@example.com" exists
    When I send a POST request to "/api/v1/auth/password-reset/" with:
      | email | alice@example.com |
    Then the response status should be 200 OK
    And the response should say "If an account exists, a reset email has been sent"
    And a Celery task should be dispatched to send the reset email
    And the response should NOT reveal whether the email exists

  @password-reset @rate-limiting
  Scenario: Password reset is rate-limited
    When I send 3 password reset requests within 1 hour
    Then the 4th request should return 429 Too Many Requests

  @password-reset
  Scenario: Confirm password reset with valid token
    Given I received a password reset email with uid and token
    When I send a POST request to "/api/v1/auth/password-reset/confirm/" with:
      | uid       | <base64-encoded-uid> |
      | token     | <reset-token>        |
      | password  | NewSecureP@ss!1      |
    Then the response status should be 200 OK
    And I should be able to log in with the new password
