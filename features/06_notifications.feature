# =============================================================================
# Feature 06: Notifications (In-App + WebSocket + Email)
# Module: apps/notifications + Django Channels + Celery
# Types: TASK_ASSIGNED, TASK_UPDATED, TASK_COMPLETED, COMMENT_ADDED,
#        MENTION, DUE_DATE_REMINDER, PROJECT_INVITATION, SYSTEM
# =============================================================================

@notifications
Feature: Notifications System
  As a platform user
  I want to receive real-time notifications about relevant activity
  So that I can stay informed and respond to changes promptly

  Background:
    Given I am authenticated as "alice@example.com"
    And the notification types are:
      | Type                 | Description                        | Trigger                          |
      | TASK_ASSIGNED        | Task assigned to you               | Task assignee field changed      |
      | TASK_UPDATED         | Task you follow was updated        | Any field change on watched task |
      | TASK_COMPLETED       | A task was marked done             | Status changes to DONE           |
      | COMMENT_ADDED        | Someone commented on your task     | New comment on assigned task     |
      | MENTION              | You were mentioned                 | @mention in comment              |
      | DUE_DATE_REMINDER    | Task due date approaching          | Celery beat at 8:00 AM daily     |
      | PROJECT_INVITATION   | Invited to a project               | Added as project member          |
      | SYSTEM               | System-level notice                | Admin broadcasts                 |

  # ---------------------------------------------------------------------------
  # In-App Notification Generation (Backend Signals)
  # ---------------------------------------------------------------------------
  @notification-signals
  Scenario: Notification created when task is assigned
    Given task "WEB-1" is being assigned to Bob by Alice
    When the task save signal fires (post_save)
    Then a Notification record should be created:
      | Field             | Value                              |
      | recipient         | bob@example.com                    |
      | sender            | alice@example.com                  |
      | notification_type | TASK_ASSIGNED                      |
      | title             | Task Assigned: WEB-1               |
      | message           | Alice assigned you to "Design..."  |
      | is_read           | false                              |
      | content_type      | tasks.Task (GenericForeignKey)      |
      | object_id         | <task_uuid>                        |
    And the notification should be sent to Bob's WebSocket channel

  @notification-signals
  Scenario: Notification created when task is completed
    Given Bob completes task "WEB-1" (status → DONE)
    Then Alice (the reporter) should receive a "TASK_COMPLETED" notification

  @notification-signals
  Scenario: Notification created when comment is added
    Given Bob adds a comment to Alice's task "WEB-1"
    Then Alice should receive a "COMMENT_ADDED" notification

  # ---------------------------------------------------------------------------
  # Celery Periodic Notifications
  # ---------------------------------------------------------------------------
  @celery-beat
  Scenario: Due date reminders sent daily at 8:00 AM
    Given the Celery beat schedule includes "due_date_reminders" at 8:00 AM
    And the following tasks are due tomorrow:
      | Task Key | Assignee            | Due Date   |
      | WEB-5    | alice@example.com   | 2026-03-01 |
      | WEB-8    | bob@example.com     | 2026-03-01 |
    When the celery beat task fires
    Then a DUE_DATE_REMINDER notification should be created for Alice about WEB-5
    And a DUE_DATE_REMINDER notification should be created for Bob about WEB-8
    And email reminders should be sent to both users

  @celery-beat
  Scenario: Overdue task notifications sent daily at 9:00 AM
    Given the Celery beat schedule includes "overdue_notifications" at 9:00 AM
    And the following tasks are overdue:
      | Task Key | Assignee          | Due Date   | Status      |
      | WEB-3    | alice@example.com | 2026-02-20 | IN_PROGRESS |
    When the celery beat task fires
    Then an overdue notification should be created for Alice
    And an email about overdue tasks should be sent to Alice

  @celery-beat
  Scenario: Old notifications are cleaned up periodically
    Given notifications older than 90 days exist
    And the Celery beat schedule includes "cleanup_old_notifications"
    When the cleanup task runs
    Then read notifications older than 90 days should be deleted

  # ---------------------------------------------------------------------------
  # WebSocket Real-Time Delivery
  # ---------------------------------------------------------------------------
  @websocket @realtime
  Scenario: Real-time notification delivery via WebSocket
    Given I have an active WebSocket connection to "ws/notifications/"
    When another user triggers a notification for me
    Then the Django Channels NotificationConsumer should:
      | Step                                                  |
      | Receive the notification from the channel layer       |
      | Serialize the notification to JSON                    |
      | Send it to my personal WebSocket group                |
    And my Angular app should receive the WebSocket message
    And the notification should be prepended to the notification list
    And the unread count should increment

  @websocket
  Scenario: WebSocket authentication via query parameter
    When my Angular app connects to "ws/notifications/?token={jwt_access_token}"
    Then the JWTAuthMiddleware should:
      | Step                                                |
      | Extract the token from query parameter              |
      | Validate the JWT token                              |
      | Set the user on the WebSocket scope                 |
    And the connection should be accepted
    And I should be added to my personal notification group

  @websocket
  Scenario: WebSocket connection rejected with invalid token
    When I try to connect with an invalid or expired token
    Then the WebSocket connection should be rejected (close code 4001)

  # ---------------------------------------------------------------------------
  # Notification List (Frontend)
  # ---------------------------------------------------------------------------
  @notification-list
  Scenario: View notification list page
    Given I have the following notifications:
      | Type             | Title                          | Read  | Age    |
      | TASK_ASSIGNED    | Task Assigned: WEB-1           | false | 2 min  |
      | COMMENT_ADDED    | New Comment on WEB-3           | false | 1 hour |
      | TASK_COMPLETED   | WEB-5 Complete                 | true  | 1 day  |
      | DUE_DATE_REMINDER| WEB-8 due tomorrow             | true  | 2 days |
    When I navigate to "/notifications"
    Then I should see all 4 notifications in reverse chronological order
    And each notification should display:
      | Element              | Description                              |
      | Type icon            | Contextual icon (e.g., person-check for assigned) |
      | Title                | Bold text                                |
      | Time ago             | Relative timestamp                       |
      | Message              | Notification detail text                 |
      | Unread indicator     | Blue dot for unread notifications        |
    And unread notifications should have a light background (bg-light)

  @notification-list
  Scenario: Notification icons by type
    Then notifications should show the following icons:
      | Notification Type     | Bootstrap Icon               | Color    |
      | TASK_ASSIGNED         | bi-person-check              | primary  |
      | TASK_UPDATED          | bi-pencil-square             | info     |
      | TASK_COMPLETED        | bi-check-circle              | success  |
      | COMMENT_ADDED         | bi-chat-left-text            | secondary|
      | MENTION               | bi-at                        | warning  |
      | DUE_DATE_REMINDER     | bi-clock                     | warning  |
      | task_overdue          | bi-exclamation-triangle      | danger   |
      | PROJECT_INVITATION    | bi-envelope                  | primary  |

  # ---------------------------------------------------------------------------
  # Notification Actions
  # ---------------------------------------------------------------------------
  @notification-actions
  Scenario: Mark a single notification as read
    Given I have an unread notification
    When I click on the notification
    Then a POST request should be sent to "/api/v1/notifications/{id}/mark-read/"
    And the notification's "read_at" should be set to the current timestamp
    And the unread count should decrement by 1
    And the blue dot indicator should disappear

  @notification-actions
  Scenario: Mark all notifications as read
    Given I have 5 unread notifications
    When I click the "Mark all read" button
    Then a POST request should be sent to "/api/v1/notifications/mark-all-read/"
    And all notifications should have their "read_at" set
    And the unread count should become 0
    And a success toast "All marked as read" should appear

  @notification-actions
  Scenario: Clear all read notifications
    Given I have 3 read and 2 unread notifications
    When I click the "Clear read" button
    Then a DELETE request should be sent to "/api/v1/notifications/clear-read/"
    And the 3 read notifications should be removed from the list
    And only the 2 unread notifications should remain
    And a success toast "Read notifications cleared" should appear

  @notification-actions
  Scenario: Load more notifications (pagination)
    Given I have 50 notifications total
    And the first page shows 25
    When I click the "Load more" button
    Then page 2 should be loaded and appended to the list
    And if there are no more pages, the "Load more" button should disappear

  # ---------------------------------------------------------------------------
  # Header Bell (Unread Count)
  # ---------------------------------------------------------------------------
  @header-bell
  Scenario: Notification bell shows unread count in the header
    Given I have 3 unread notifications
    When the HeaderComponent loads
    Then it should poll the unread count every 30 seconds
    And the bell icon should show a badge with "3"
    And clicking the bell should navigate to "/notifications"

  @header-bell
  Scenario: Unread count updates in real-time
    Given my unread count is 3
    And I receive a new notification via WebSocket
    Then the unread count on the bell should update to 4 without page refresh

  # ---------------------------------------------------------------------------
  # Email Notifications (Celery Background Tasks)
  # ---------------------------------------------------------------------------
  @email
  Scenario: Email notification sent for task assignment
    Given email notifications are enabled
    When a task is assigned to "bob@example.com"
    Then a Celery task should be dispatched to send an email
    And the email should contain:
      | Field   | Description                      |
      | To      | bob@example.com                  |
      | Subject | Task Assigned: WEB-1             |
      | Body    | Details of the task assignment   |
      | Link    | URL to view the task             |

  @email
  Scenario: Welcome email sent on registration
    When a new user registers successfully
    Then a "send_welcome_email" Celery task should be dispatched
    And the email should welcome the user and provide getting-started info
