# =============================================================================
# Feature 03: Project Management
# Module: apps/projects
# Includes: Projects, Boards, Columns, Project Members
# =============================================================================

@projects
Feature: Project Management
  As an organization member
  I want to create and configure projects with Kanban boards
  So that I can organize work for my team

  Background:
    Given I am authenticated as "alice@example.com"
    And I am a member of "Acme Corporation"
    And project member roles are:
      | Role   | Permissions                                     |
      | ADMIN  | Full project control, manage members, settings  |
      | MEMBER | Create/edit tasks, move cards, comment           |
      | VIEWER | Read-only access to board and tasks              |

  # ---------------------------------------------------------------------------
  # Project CRUD
  # ---------------------------------------------------------------------------
  @project-create
  Scenario: Create a new project
    When I send a POST request to "/api/v1/projects/" with:
      | Field        | Value                                    |
      | organization | <acme_org_id>                            |
      | name         | Website Redesign                         |
      | description  | Complete overhaul of the company website  |
      | prefix       | WEB                                      |
      | start_date   | 2026-03-01                               |
      | end_date     | 2026-06-30                               |
    Then the response status should be 201 Created
    And the project should be created with:
      | Field      | Value                |
      | name       | Website Redesign     |
      | slug       | website-redesign     |
      | prefix     | WEB                  |
      | status     | ACTIVE               |
      | created_by | alice@example.com    |
    And a default Kanban board named "Main Board" should be auto-created
    And the default board should have 5 columns:
      | Name         | Position | Color   | Is Done Column |
      | Backlog      | 0        | #6C757D | false          |
      | To Do        | 1        | #0D6EFD | false          |
      | In Progress  | 2        | #FFC107 | false          |
      | In Review    | 3        | #17A2B8 | false          |
      | Done         | 4        | #198754 | true           |
    And I should be added as a project ADMIN automatically

  @project-create
  Scenario: Auto-generate prefix when not provided
    When I create a project named "Mobile App Development" without a prefix
    Then the prefix should be auto-generated as "MAD" (first letters of words)

  @project-create
  Scenario: Slug uniqueness within organization
    Given a project "Website Redesign" exists in "Acme Corporation"
    When I create another project named "Website Redesign"
    Then the new project should have slug "website-redesign-1"

  @project-list
  Scenario: List projects in my organization
    Given "Acme Corporation" has the following projects:
      | Name               | Status   | Task Count |
      | Website Redesign   | ACTIVE   | 42         |
      | Mobile App         | ACTIVE   | 18         |
      | Legacy Migration   | ARCHIVED | 95         |
    When I send a GET request to "/api/v1/projects/"
    Then the response should contain the projects I have access to
    And each project should include:
      | Field        | Description                       |
      | id           | UUID primary key                  |
      | name         | Project name                      |
      | description  | Project description               |
      | status       | ACTIVE / ARCHIVED                 |
      | prefix       | Task key prefix                   |
      | task_count   | Number of tasks                   |
      | member_count | Number of project members         |
      | created_at   | Creation timestamp                |

  @project-detail
  Scenario: View project details with boards
    When I send a GET request to "/api/v1/projects/{project_id}/"
    Then the response should include project details
    And the response should include a list of boards with their columns

  @project-update
  Scenario: Update project settings
    Given I am a project ADMIN
    When I send a PATCH request to "/api/v1/projects/{project_id}/" with:
      | description | Updated project description |
      | end_date    | 2026-09-30                 |
    Then the project should be updated successfully

  # ---------------------------------------------------------------------------
  # Archive / Restore (Soft Delete)
  # ---------------------------------------------------------------------------
  @project-archive
  Scenario: Archive a project
    Given I am a project ADMIN of "Website Redesign"
    When I send a POST request to "/api/v1/projects/{project_id}/archive/"
    Then the project status should change to "ARCHIVED"
    And the project should still be accessible (read-only)
    And the "deleted_at" timestamp should be set
    And I should see a success toast notification on the frontend

  @project-restore
  Scenario: Restore an archived project
    Given "Website Redesign" is archived
    When I send a POST request to "/api/v1/projects/{project_id}/restore/"
    Then the project status should change to "ACTIVE"
    And the "deleted_at" field should be cleared

  # ---------------------------------------------------------------------------
  # Project Members
  # ---------------------------------------------------------------------------
  @project-members
  Scenario: Add a member to a project
    Given I am a project ADMIN
    When I send a POST request to add "bob@example.com" with role "MEMBER"
    Then Bob should be added to the project as MEMBER
    And Bob should receive a project invitation notification

  @project-members
  Scenario: Change a project member's role
    Given "bob@example.com" is a MEMBER of the project
    When I update Bob's role to "VIEWER"
    Then Bob should only have read-only access to the project

  @project-members @permissions
  Scenario: VIEWER cannot create or modify tasks
    Given I am a VIEWER on the project
    When I try to create a new task
    Then the response status should be 403 Forbidden

  # ---------------------------------------------------------------------------
  # Boards
  # ---------------------------------------------------------------------------
  @boards
  Scenario: Create an additional board
    Given I am a project ADMIN of "Website Redesign"
    When I send a POST request to "/api/v1/projects/{project_id}/boards/" with:
      | name | Sprint 2 Board |
    Then a new board should be created
    And the board should start with no columns

  @boards
  Scenario: List project boards
    When I send a GET request to "/api/v1/projects/{project_id}/boards/"
    Then I should see all boards for the project
    And the default board should be listed first

  # ---------------------------------------------------------------------------
  # Columns (Board Lanes)
  # ---------------------------------------------------------------------------
  @columns
  Scenario: Add a custom column to a board
    Given I am viewing the "Main Board" of "Website Redesign"
    When I add a new column with:
      | name      | QA Testing |
      | color     | #E83E8C    |
      | position  | 3          |
      | wip_limit | 5          |
    Then the column should be created at position 3
    And existing columns at position 3+ should shift right

  @columns
  Scenario: Set a WIP (Work In Progress) limit on a column
    Given the "In Progress" column exists with no WIP limit
    When I update the column to set wip_limit to 4
    Then the column should enforce a WIP limit of 4
    And the frontend should visually warn when the limit is exceeded
    And the WIP badge should turn red when count > limit

  @columns
  Scenario: Mark a column as the "Done" column
    Given the "Done" column has is_done_column set to true
    When a task is moved to this column
    Then the task's "completed_at" timestamp should be automatically set

  @columns @reorder
  Scenario: Reorder columns on a board
    Given the board has columns in order: Backlog, To Do, In Progress, Review, Done
    When I reorder the columns to: Backlog, To Do, Review, In Progress, Done
    Then the column positions should be atomically updated
    And the board should reflect the new order immediately
