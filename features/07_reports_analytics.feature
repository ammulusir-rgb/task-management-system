# =============================================================================
# Feature 07: Reports & Analytics Dashboard
# Module: apps/reports (backend) + features/reports (frontend)
# Charts: @swimlane/ngx-charts (pie, bar-vertical, bar-horizontal, line)
# =============================================================================

@reports
Feature: Reports and Analytics Dashboard
  As a project manager
  I want to view analytical reports and charts for my project
  So that I can track progress, identify bottlenecks, and make data-driven decisions

  Background:
    Given I am authenticated as "alice@example.com"
    And I am a member of project "Website Redesign" (ID: {project_id})
    And the project has 100 tasks with various statuses, priorities, and assignees
    And the reports are accessed via "/api/v1/projects/{project_id}/reports/"

  # ---------------------------------------------------------------------------
  # Project Summary (KPIs)
  # ---------------------------------------------------------------------------
  @summary
  Scenario: View project summary KPI cards
    When I navigate to "/reports/{project_id}"
    And the ReportsDashboardComponent loads
    Then a GET request is sent to "/api/v1/projects/{project_id}/reports/summary/"
    And the response should contain:
      | Field                  | Description                           |
      | total_tasks            | Total count of non-deleted tasks      |
      | completed_tasks        | Tasks with status DONE                |
      | open_tasks             | total - completed                     |
      | overdue_tasks          | Tasks past due_date and not done      |
      | completion_rate        | Percentage completed (1 decimal)      |
      | avg_cycle_time_hours   | Average started_at → completed_at     |
    And 4 summary cards should be displayed:
      | Card            | Value Source       | Color  |
      | Total Tasks     | total_tasks        | primary|
      | Completed       | completed_tasks    | success|
      | Overdue         | overdue_tasks      | danger |
      | Completion %    | completion_rate    | default|

  @summary
  Scenario: Completion percentage calculation
    Given the project has 80 total tasks and 60 completed
    Then the completion_rate should be 75.0%
    And the display should show "75%"

  @summary
  Scenario: Average cycle time calculation
    Given completed tasks have the following cycle times:
      | Task   | Started At          | Completed At        | Hours |
      | WEB-1  | 2026-02-01 09:00    | 2026-02-03 09:00    | 48.0  |
      | WEB-2  | 2026-02-05 09:00    | 2026-02-06 09:00    | 24.0  |
    Then avg_cycle_time_hours should be 36.0

  # ---------------------------------------------------------------------------
  # Tasks by Status (Doughnut / Pie Chart)
  # ---------------------------------------------------------------------------
  @status-chart
  Scenario: View tasks by status distribution
    When the component loads
    Then a GET request is sent to "/reports/tasks-by-status/"
    And the response should be an array:
      | status      | count |
      | BACKLOG     | 15    |
      | TODO        | 25    |
      | IN_PROGRESS | 30    |
      | IN_REVIEW   | 10    |
      | DONE        | 20    |
    And the data should be transformed to ngx-charts format:
      | name        | value |
      | BACKLOG     | 15    |
      | TODO        | 25    |
      | IN_PROGRESS | 30    |
      | IN_REVIEW   | 10    |
      | DONE        | 20    |
    And a doughnut pie chart should be rendered using ngx-charts-pie-chart
    And the chart should use the status color scheme:
      | Color   | Status      |
      | #6c757d | BACKLOG     |
      | #0d6efd | TODO        |
      | #ffc107 | IN_PROGRESS |
      | #17a2b8 | IN_REVIEW   |
      | #198754 | DONE        |

  # ---------------------------------------------------------------------------
  # Tasks by Priority (Vertical Bar Chart)
  # ---------------------------------------------------------------------------
  @priority-chart
  Scenario: View tasks by priority distribution
    When the component loads
    Then a GET request is sent to "/reports/tasks-by-priority/"
    And the response should be:
      | priority | count |
      | CRITICAL | 8     |
      | HIGH     | 22    |
      | MEDIUM   | 45    |
      | LOW      | 25    |
    And a vertical bar chart should be rendered using ngx-charts-bar-vertical
    And the chart should use the priority color scheme:
      | Color   | Priority |
      | #6c757d | LOW      |
      | #0d6efd | MEDIUM   |
      | #ffc107 | HIGH     |
      | #fd7e14 | (unused) |
      | #dc3545 | CRITICAL |

  # ---------------------------------------------------------------------------
  # Burndown Chart (Line Chart)
  # ---------------------------------------------------------------------------
  @burndown
  Scenario: View 30-day burndown chart
    When the component loads
    Then a GET request is sent to "/reports/burndown/?days=30"
    And the response should be an array of daily data points:
      | Field                  | Description                            |
      | date                   | ISO date string                        |
      | remaining              | Tasks remaining (total - done + scope) |
      | completed_cumulative   | Running total of completed tasks       |
      | new_tasks              | Tasks created that day (scope creep)   |
    And the data should be transformed to ngx-charts line format:
      | name      | series                               |
      | Remaining | [{name: "2026-01-29", value: 45}...] |
    And a line chart should be rendered with timeline enabled
    And the chart should show the trend of remaining work over time

  @burndown
  Scenario: Burndown accounts for scope creep
    Given on 2026-02-15:
      | Remaining from yesterday | New tasks created | Tasks completed |
      | 40                       | 5                 | 3               |
    Then today's remaining should be 42 (40 + 5 - 3)

  # ---------------------------------------------------------------------------
  # Velocity Chart (Bar Chart)
  # ---------------------------------------------------------------------------
  @velocity
  Scenario: View weekly velocity over 12 weeks
    When the component loads
    Then a GET request is sent to "/reports/velocity/?weeks=12"
    And the response should be an array of weekly data:
      | week       | completed |
      | 2025-12-01 | 8         |
      | 2025-12-08 | 12        |
      | 2025-12-15 | 10        |
      | ...        | ...       |
    And the data should be transformed to:
      | name       | value |
      | 2025-12-01 | 8     |
      | 2025-12-08 | 12    |
      | ...        | ...   |
    And a vertical bar chart should show tasks completed per week

  # ---------------------------------------------------------------------------
  # Assignee Workload (Horizontal Bar Chart)
  # ---------------------------------------------------------------------------
  @workload
  Scenario: View workload distribution by assignee
    When the component loads
    Then a GET request is sent to "/reports/tasks-by-assignee/"
    And the response should include per-assignee metrics:
      | assignee_name | total | completed | in_progress |
      | Bob Johnson   | 25    | 15        | 10          |
      | Carol Smith   | 18    | 10        | 8           |
      | Alice Johnson | 12    | 8         | 4           |
    And the data should be transformed for horizontal bar chart:
      | name          | value |
      | Bob Johnson   | 25    |
      | Carol Smith   | 18    |
      | Alice Johnson | 12    |
    And the chart height should dynamically adjust based on number of assignees
    And the formula should be: max(200, assigneeCount * 40) pixels

  # ---------------------------------------------------------------------------
  # Additional Report Endpoints
  # ---------------------------------------------------------------------------
  @labels
  Scenario: View tasks by labels/tags
    When a GET request is sent to "/reports/tasks-by-label/"
    Then the response should show tag frequency from PostgreSQL ArrayField:
      | tag        | count |
      | design     | 18    |
      | frontend   | 15    |
      | bug        | 12    |
    And the query uses raw SQL "SELECT tag, COUNT(*) FROM tasks_task, unnest(tags)"

  @activity-heatmap
  Scenario: View activity heatmap (90 days)
    When a GET request is sent to "/reports/activity-heatmap/?days=90"
    Then the response should show daily activity counts
    And the data is aggregated from the ActivityLog model

  @throughput
  Scenario: View monthly throughput
    When a GET request is sent to "/reports/monthly-throughput/?months=12"
    Then the response should show tasks completed per month over 12 months

  # ---------------------------------------------------------------------------
  # CSV Export
  # ---------------------------------------------------------------------------
  @csv-export
  Scenario: Export all project tasks as CSV
    When I click the "Export CSV" button on the reports page
    Then a GET request is sent to "/reports/export-csv/"
    And the backend ReportService.export_tasks_csv() should:
      | Step                                         |
      | Query all non-deleted tasks for the project  |
      | Generate CSV with headers:                   |
      |   Task Key, Title, Status, Priority,         |
      |   Assignee, Reporter, Due Date, Created,     |
      |   Completed, Column, Tags, Story Points      |
      | Return CSV content as a blob                 |
    And the frontend should:
      | Step                                         |
      | Create a Blob from the response              |
      | Generate an object URL                       |
      | Create and click a download link             |
      | Name the file "project-{id}-tasks.csv"       |
      | Revoke the object URL                        |
      | Show success toast "Export downloaded"        |

  @csv-export @error
  Scenario: CSV export failure
    When the CSV export request fails
    Then an error toast "Export failed" should appear
