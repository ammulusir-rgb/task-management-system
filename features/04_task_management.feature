# =============================================================================
# Feature 04: Task Management (Core Domain)
# Module: apps/tasks
# Models: Task, Comment, Attachment, ActivityLog
# =============================================================================

@tasks
Feature: Task Management
  As a project member
  I want to create, track, and manage tasks with full lifecycle support
  So that my team can collaborate and deliver work effectively

  Background:
    Given I am authenticated as "alice@example.com"
    And I am a MEMBER of project "Website Redesign" (prefix: WEB)
    And the project board has columns: Backlog, To Do, In Progress, In Review, Done
    And the available task statuses are:
      | Status      | Label        |
      | BACKLOG     | Backlog      |
      | TODO        | To Do        |
      | IN_PROGRESS | In Progress  |
      | IN_REVIEW   | In Review    |
      | DONE        | Done         |
      | CANCELLED   | Cancelled    |
    And the available task priorities are:
      | Priority | Label    |
      | CRITICAL | Critical |
      | HIGH     | High     |
      | MEDIUM   | Medium   |
      | LOW      | Low      |

  # ---------------------------------------------------------------------------
  # Task Creation
  # ---------------------------------------------------------------------------
  @task-create
  Scenario: Create a new task in the backlog
    When I send a POST request to "/api/v1/tasks/" with:
      | Field           | Value                                 |
      | project         | <website_redesign_id>                 |
      | title           | Design new homepage layout            |
      | description     | Create mockups for the new homepage   |
      | priority        | HIGH                                  |
      | assignee        | <bob_user_id>                         |
      | due_date        | 2026-04-15T00:00:00Z                  |
      | estimated_hours | 16.0                                  |
      | tags            | ["design", "homepage", "ui"]          |
    Then the response status should be 201 Created
    And the task should have:
      | Field       | Value                     |
      | task_number | 1 (auto-incremented)      |
      | task_key    | WEB-1                     |
      | status      | BACKLOG (default)         |
      | priority    | HIGH                      |
      | reporter    | alice@example.com         |
    And Bob should receive a "TASK_ASSIGNED" notification
    And an ActivityLog entry should be created with action "CREATED"

  @task-create
  Scenario: Task key auto-generation
    Given the project "Website Redesign" has prefix "WEB"
    And the last task number in the project is 41
    When I create a new task
    Then the task should be assigned task_number 42
    And the task_key should be "WEB-42"
    And the task_key should be unique and indexed

  @task-create
  Scenario: Create a subtask
    Given task "WEB-1" exists
    When I create a task with parent set to "WEB-1":
      | title  | Create hero section mockup |
      | parent | <web_1_task_id>            |
    Then the subtask should be linked to WEB-1
    And WEB-1's subtask_count property should return 1

  # ---------------------------------------------------------------------------
  # Task Listing & Filtering
  # ---------------------------------------------------------------------------
  @task-list
  Scenario: List tasks with pagination
    Given the project has 150 tasks
    When I send a GET request to "/api/v1/tasks/?project={project_id}"
    Then the response should follow standard pagination (25 per page):
      | Field    | Description                     |
      | count    | Total number of results (150)   |
      | next     | URL to next page                |
      | previous | null (first page)               |
      | results  | Array of 25 task items          |
    And each task item should include:
      | Field          | Description                      |
      | id             | UUID                             |
      | task_key       | Project prefix + number          |
      | title          | Task title                       |
      | status         | Current status                   |
      | priority       | Priority level                   |
      | assignee       | Nested user object (id, name, avatar) |
      | due_date       | Due date or null                 |
      | tags           | Array of tag strings             |
      | subtask_count  | Number of subtasks               |
      | comment_count  | Number of comments               |
      | column         | Column ID                        |

  @task-filter
  Scenario Outline: Filter tasks by various criteria
    When I send a GET request to "/api/v1/tasks/" with query parameters:
      | Parameter | Value    |
      | <param>   | <value>  |
    Then I should receive only tasks matching the filter

    Examples:
      | param        | value                        |
      | status       | IN_PROGRESS                  |
      | priority     | HIGH                         |
      | assignee     | <bob_user_id>                |
      | is_overdue   | true                         |
      | tags         | design                       |
      | due_date_gte | 2026-04-01                   |
      | due_date_lte | 2026-04-30                   |
      | search       | homepage                     |
      | column       | <in_progress_column_id>      |

  @task-filter
  Scenario: Search tasks by keyword
    Given the following tasks exist:
      | Task Key | Title                       |
      | WEB-1    | Design new homepage layout  |
      | WEB-2    | Implement header component  |
      | WEB-3    | Homepage SEO optimization   |
    When I search for "homepage"
    Then I should receive WEB-1 and WEB-3

  @task-filter
  Scenario: Filter overdue tasks
    Given the current date is 2026-02-28
    And the following tasks exist:
      | Task Key | Due Date   | Status      |
      | WEB-1    | 2026-02-15 | IN_PROGRESS | # Overdue
      | WEB-2    | 2026-03-15 | TODO        | # Not overdue
      | WEB-3    | 2026-02-20 | DONE        | # Done (not overdue)
    When I filter by "is_overdue=true"
    Then I should receive only WEB-1

  # ---------------------------------------------------------------------------
  # Task Update
  # ---------------------------------------------------------------------------
  @task-update
  Scenario: Update task details
    Given task "WEB-1" exists
    When I send a PATCH request to "/api/v1/tasks/{task_id}/" with:
      | title    | Design new homepage layout (v2) |
      | priority | CRITICAL                        |
    Then the task should be updated
    And an ActivityLog entry should be created:
      | field_name | old_value | new_value                        |
      | title      | Design... | Design new homepage layout (v2)  |
      | priority   | HIGH      | CRITICAL                         |
    And the change should be broadcast via WebSocket to board subscribers

  @task-update
  Scenario: Assign a task to a user
    Given task "WEB-1" is unassigned
    When I update the assignee to "bob@example.com"
    Then Bob should receive a "TASK_ASSIGNED" notification
    And an ActivityLog with action "ASSIGNED" should be created

  @task-update
  Scenario: Changing status to IN_PROGRESS auto-sets started_at
    Given task "WEB-1" has status "TODO" and started_at is null
    When I change the status to "IN_PROGRESS"
    Then the "started_at" timestamp should be automatically set to now

  @task-update
  Scenario: Changing status to DONE auto-sets completed_at
    Given task "WEB-1" has status "IN_REVIEW"
    When I change the status to "DONE"
    Then the "completed_at" timestamp should be automatically set to now

  @task-update
  Scenario: Inline editing on the Task Detail page
    Given I am viewing task "WEB-1" on the frontend
    When I double-click on the task title
    Then the title should become an editable input field
    When I change the title and press Enter
    Then the title should be saved via PATCH request
    And a success toast should appear

  @task-update
  Scenario: Edit description with click-to-edit
    Given I am viewing task "WEB-1" on the frontend
    When I click on the description area
    Then a textarea should appear with the current description
    When I modify the text and click "Save"
    Then the description should be updated via PATCH request

  # ---------------------------------------------------------------------------
  # Tags
  # ---------------------------------------------------------------------------
  @tags
  Scenario: Add a tag to a task
    Given task "WEB-1" has tags ["design"]
    When I add tag "urgent"
    Then the tags field should be updated to ["design", "urgent"]
    And the tags are stored in a PostgreSQL ArrayField with GIN index

  @tags
  Scenario: Remove a tag from a task
    Given task "WEB-1" has tags ["design", "urgent"]
    When I remove tag "urgent"
    Then the tags field should be updated to ["design"]

  # ---------------------------------------------------------------------------
  # Time Tracking
  # ---------------------------------------------------------------------------
  @time-tracking
  Scenario: Track estimated vs actual hours
    Given task "WEB-1" has estimated_hours 16.0
    When I update logged_hours to 12.5
    Then the task detail sidebar should show:
      | Metric    | Value |
      | Estimated | 16.0h |
      | Actual    | 12.5h |

  # ---------------------------------------------------------------------------
  # Task Soft Delete
  # ---------------------------------------------------------------------------
  @soft-delete
  Scenario: Soft delete a task
    Given task "WEB-1" exists
    When I send a DELETE request to "/api/v1/tasks/{task_id}/"
    Then the task should be soft-deleted (deleted_at set, not physically removed)
    And the task should no longer appear in default task listings
    And the task data should still exist in the database for audit

  # ---------------------------------------------------------------------------
  # Comments
  # ---------------------------------------------------------------------------
  @comments
  Scenario: Add a comment to a task
    Given task "WEB-1" exists
    When I send a POST request to "/api/v1/tasks/{task_id}/comments/" with:
      | content | Looking great! Can we add a CTA button? |
    Then the comment should be created with:
      | Field   | Value                                    |
      | author  | alice@example.com                        |
      | content | Looking great! Can we add a CTA button?  |
      | parent  | null (top-level comment)                 |
    And the task assignee should receive a "COMMENT_ADDED" notification

  @comments
  Scenario: Reply to a comment (threaded)
    Given task "WEB-1" has a comment by Alice (comment_id: <parent_id>)
    When Bob replies to Alice's comment:
      | content | Sure, I'll add it to the design. |
      | parent  | <parent_id>                      |
    Then the reply should be linked to Alice's comment as a child
    And Alice should receive a notification

  @comments
  Scenario: List comments on the task detail page
    Given task "WEB-1" has 5 comments
    When I view the task detail page
    Then comments should be listed in chronological order
    And each comment should show:
      | Element          | Description                          |
      | Author avatar    | User avatar or initials              |
      | Author name      | First name + Last name               |
      | Time ago         | Relative timestamp (e.g., "2h ago")  |
      | Content          | Comment text (pre-wrapped)           |

  # ---------------------------------------------------------------------------
  # Attachments
  # ---------------------------------------------------------------------------
  @attachments
  Scenario: Upload a file attachment
    Given task "WEB-1" exists
    When I upload a file "mockup.png" (2.5MB) to "/api/v1/tasks/{task_id}/attachments/"
    Then the attachment should be created with:
      | Field          | Value          |
      | filename       | mockup.png     |
      | file_size      | 2621440        |
      | content_type   | image/png      |
      | uploaded_by    | alice@example  |
    And an ActivityLog with action "ATTACHMENT_ADDED" should be created
    And the file should be stored at the configured storage backend

  @attachments @validation
  Scenario: Reject files larger than 10MB
    When I try to upload a file larger than 10MB
    Then the response status should be 400 Bad Request
    And the error should indicate the file exceeds the maximum size

  @attachments
  Scenario: List and download attachments
    Given task "WEB-1" has 3 attachments
    When I view the task detail sidebar
    Then I should see each attachment with:
      | Element       | Description        |
      | File icon     | Paperclip icon     |
      | Filename      | Clickable link     |
      | File size     | Formatted (KB/MB)  |
    And clicking the filename should open/download the file

  # ---------------------------------------------------------------------------
  # Activity Log (Audit Trail)
  # ---------------------------------------------------------------------------
  @activity-log
  Scenario: View task activity history
    Given task "WEB-1" has undergone the following changes:
      | User  | Action          | Field    | Old Value    | New Value     |
      | Alice | CREATED         |          |              |               |
      | Alice | ASSIGNED        | assignee | null         | Bob           |
      | Bob   | STATUS_CHANGED  | status   | BACKLOG      | IN_PROGRESS   |
      | Bob   | PRIORITY_CHANGED| priority | HIGH         | CRITICAL      |
      | Alice | COMMENTED       |          |              |               |
      | Bob   | ATTACHMENT_ADDED|          |              | mockup.png    |
    When I send a GET request to "/api/v1/tasks/{task_id}/activity/"
    Then I should see all activity entries in reverse chronological order
    And each entry should include the user, action, old/new values, and timestamp
    And the frontend should display this as a timeline with relative timestamps
