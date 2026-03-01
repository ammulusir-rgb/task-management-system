# =============================================================================
# Feature 05: Kanban Board (Drag & Drop)
# Module: frontend/features/board + backend/apps/tasks (move endpoint)
# Tech: Angular CDK DragDrop + Django Channels WebSocket
# =============================================================================

@kanban
Feature: Kanban Board with Drag-and-Drop
  As a project member
  I want to use an interactive Kanban board to visualize and manage tasks
  So that I can track work progress and move tasks through workflow stages

  Background:
    Given I am authenticated and viewing the board for project "Website Redesign"
    And the board "Main Board" has columns:
      | Column       | Position | Color   | WIP Limit | Is Done Column |
      | Backlog      | 0        | #6C757D | null      | false          |
      | To Do        | 1        | #0D6EFD | null      | false          |
      | In Progress  | 2        | #FFC107 | 4         | false          |
      | In Review    | 3        | #17A2B8 | null      | false          |
      | Done         | 4        | #198754 | true      | true           |

  # ---------------------------------------------------------------------------
  # Board View
  # ---------------------------------------------------------------------------
  @board-view
  Scenario: Board layout renders all columns with task cards
    When the board component loads
    Then I should see a horizontal scrollable Kanban container
    And each column should display:
      | Element            | Description                           |
      | Column header      | Name + color indicator (8px circle)   |
      | Task count badge   | Number of tasks in the column         |
      | WIP limit label    | "WIP: N" shown if wip_limit is set    |
      | Task cards         | Vertically stacked, draggable         |
    And tasks should be loaded via GET "/api/v1/tasks/?board={board_id}&page_size=200&ordering=position"
    And tasks should be grouped by their column_id

  @board-view
  Scenario: Task card displays key information
    Given a task card for "WEB-1" is visible in the "In Progress" column
    Then the card should display:
      | Element          | Description                              |
      | Task key         | "WEB-1" in muted text                    |
      | Priority badge   | Colored icon badge (e.g., red for HIGH)  |
      | Title            | Task title text (medium weight)          |
      | Subtask count    | Icon + count (if subtasks exist)         |
      | Comment count    | Icon + count (if comments exist)         |
      | Due date         | Calendar icon + formatted date           |
      | Assignee avatar  | Small circular avatar (or initials)      |
    And clicking the card should navigate to "/tasks/{task_id}"

  @board-view
  Scenario: Due date appears red when overdue
    Given a task "WEB-5" has due_date "2026-02-15" (in the past)
    And the task status is "IN_PROGRESS"
    Then the due date text on the card should have class "text-danger"

  # ---------------------------------------------------------------------------
  # Drag and Drop — Move Within Same Column
  # ---------------------------------------------------------------------------
  @drag-drop @reorder
  Scenario: Reorder tasks within the same column
    Given the "To Do" column has tasks in order: WEB-1, WEB-2, WEB-3
    When I drag "WEB-3" above "WEB-1" within the "To Do" column
    Then the CDK DragDrop event should fire with:
      | Property           | Value                    |
      | previousContainer  | same as container        |
      | previousIndex      | 2                        |
      | currentIndex       | 0                        |
    And the frontend calls "moveItemInArray" to reorder locally
    And a PATCH is sent to update position without changing column
    And the task order should now be: WEB-3, WEB-1, WEB-2

  # ---------------------------------------------------------------------------
  # Drag and Drop — Move Between Columns
  # ---------------------------------------------------------------------------
  @drag-drop @move
  Scenario: Move a task from "To Do" to "In Progress"
    Given task "WEB-1" is in the "To Do" column at position 0
    When I drag "WEB-1" and drop it into the "In Progress" column at position 1
    Then the CDK DragDrop event should fire with:
      | Property            | Value                       |
      | previousContainer   | column-{todo_column_id}     |
      | container           | column-{progress_column_id} |
      | previousIndex       | 0                           |
      | currentIndex        | 1                           |
    And the frontend calls "transferArrayItem" to move locally
    And the tasksByColumn signal should be updated
    And a POST request should be sent to "/api/v1/tasks/{task_id}/move/" with:
      | column_id | <in_progress_column_id> |
      | position  | 1                       |
    And the backend should:
      | Action                                                |
      | Update the task's column to "In Progress"             |
      | Update the task's position to 1                       |
      | Auto-set "started_at" if transitioning to IN_PROGRESS |
      | Create an ActivityLog with action "MOVED"             |
      | Broadcast update via WebSocket to board subscribers   |

  @drag-drop @move
  Scenario: Move a task to the "Done" column
    Given task "WEB-1" is in "In Review"
    When I drag "WEB-1" to the "Done" column
    Then the task's "completed_at" should be automatically set
    And the task's status should update to "DONE"
    And the assignee should receive a "TASK_COMPLETED" notification

  @drag-drop @error
  Scenario: Handle move failure gracefully
    Given task "WEB-1" is in "To Do"
    When I drag it to "In Progress"
    And the API POST "/api/v1/tasks/{task_id}/move/" fails (e.g., network error)
    Then a toast error "Failed to move task" should appear
    And the UI should remain in the optimistic state (no rollback by default)

  # ---------------------------------------------------------------------------
  # Bulk Move
  # ---------------------------------------------------------------------------
  @bulk-move
  Scenario: Bulk move multiple tasks between columns
    Given tasks WEB-1, WEB-2, WEB-3 are selected in "To Do"
    When I bulk-move them to "In Progress"
    Then a POST request should be sent to "/api/v1/tasks/bulk-move/" with:
      | task_ids  | [<web1_id>, <web2_id>, <web3_id>] |
      | column_id | <in_progress_column_id>           |
    And all 3 tasks should be moved atomically

  # ---------------------------------------------------------------------------
  # WIP Limits
  # ---------------------------------------------------------------------------
  @wip-limit
  Scenario: WIP limit warning when column is at capacity
    Given the "In Progress" column has a WIP limit of 4
    And the column currently has 4 tasks
    Then the WIP badge should display "WIP: 4" in normal color
    When a 5th task is added to the column
    Then the WIP badge text should turn red (class "text-danger")
    And the count badge should show 5

  @wip-limit
  Scenario: WIP limit is advisory (does not block)
    Given the "In Progress" column has WIP limit of 4 and has 4 tasks
    When I drag a task into "In Progress"
    Then the move should still succeed (WIP limits are advisory)
    And the visual warning should alert the user

  # ---------------------------------------------------------------------------
  # Connected Drop Lists
  # ---------------------------------------------------------------------------
  @connected-lists
  Scenario: All columns are connected for drag-and-drop
    Given the board has 5 columns
    Then the CDK connectedDropLists should contain:
      | Value                         |
      | column-{backlog_column_id}    |
      | column-{todo_column_id}       |
      | column-{progress_column_id}   |
      | column-{review_column_id}     |
      | column-{done_column_id}       |
    And I should be able to drag a task from any column to any other column

  # ---------------------------------------------------------------------------
  # Add Column
  # ---------------------------------------------------------------------------
  @add-column
  Scenario: Add a new column to the board
    When I click the "+ Column" button in the board header
    And I enter the column name "QA Testing" in the prompt dialog
    Then a POST request should be sent to create the column with:
      | name     | QA Testing                        |
      | board    | <board_id>                        |
      | position | 5 (appended to end)               |
    And the new column should appear on the board
    And a success toast "Column added" should appear

  # ---------------------------------------------------------------------------
  # Real-Time Updates via WebSocket
  # ---------------------------------------------------------------------------
  @websocket @realtime
  Scenario: Receive real-time task updates on the board
    Given I am viewing the board
    And a WebSocket connection is established to "ws/board/{board_id}/"
    When another user (Bob) moves task "WEB-5" from "To Do" to "In Progress"
    Then the backend should broadcast a "task_update" message via Django Channels
    And my WebSocket should receive the message
    And the board should reload to reflect the change

  @websocket
  Scenario: WebSocket connection lifecycle
    When I navigate to the board page
    Then a WebSocket should connect to "ws/board/{board_id}/" with JWT token
    And the connection should be tracked by the WebSocketService as key "board"
    When I navigate away from the board
    Then the WebSocket for key "board" should be disconnected via ngOnDestroy
