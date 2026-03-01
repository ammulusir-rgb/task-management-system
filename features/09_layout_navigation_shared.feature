# =============================================================================
# Feature 09: Frontend Layout, Navigation & Shared Components
# Module: frontend/layout + frontend/shared
# Components: Shell, Header, Sidebar, Shared UI
# =============================================================================

@layout
Feature: Application Layout, Navigation and Shared Components
  As a user of the Task Management platform
  I want a responsive, intuitive layout with consistent navigation
  So that I can efficiently access all features of the application

  # ---------------------------------------------------------------------------
  # Shell Layout
  # ---------------------------------------------------------------------------
  @shell
  Scenario: Authenticated users see the shell layout
    Given I am authenticated
    When I navigate to any protected route (e.g., "/dashboard")
    Then the ShellComponent should render with:
      | Section        | Position              | Description               |
      | Sidebar        | Left column           | Navigation sidebar        |
      | Header         | Top of main content   | Search + user controls    |
      | Router outlet  | Main content area     | Current page component    |
      | Toast overlay  | Fixed bottom-right    | Toast notifications       |

  @shell
  Scenario: Unauthenticated users see auth pages without shell
    Given I am NOT authenticated
    When I navigate to "/auth/login"
    Then the ShellComponent should NOT render
    And only the auth page should be displayed

  @shell
  Scenario: Sidebar collapse toggle
    Given the sidebar is expanded by default
    When I click the sidebar collapse button
    Then the sidebar should collapse to icon-only width
    And the main content area should expand
    And the collapse state should be stored in a signal

  # ---------------------------------------------------------------------------
  # Header Component
  # ---------------------------------------------------------------------------
  @header
  Scenario: Header displays search, notifications, and user menu
    When the header renders
    Then I should see:
      | Element                | Description                             |
      | Search input           | Placeholder "Search tasks, projects..." |
      | Notification bell      | With unread count badge                 |
      | User avatar dropdown   | Shows avatar or initials                |

  @header
  Scenario: Notification bell polls unread count
    When the HeaderComponent initializes
    Then it should request the unread count from the NotificationService
    And the count should be polled every 30 seconds
    And the badge should show the current unread count
    And clicking the bell should navigate to "/notifications"

  @header
  Scenario: User dropdown menu
    When I click on my avatar in the header
    Then a dropdown should appear with options:
      | Option        | Action              |
      | My Profile    | Navigate to profile |
      | Settings      | Navigate to /admin  |
      | Sign Out      | Trigger logout()    |
    When I click "Sign Out"
    Then AuthService.logout() should be called
    And I should be redirected to "/auth/login"

  # ---------------------------------------------------------------------------
  # Sidebar Component
  # ---------------------------------------------------------------------------
  @sidebar
  Scenario: Sidebar navigation items
    When the sidebar renders
    Then I should see the following navigation items:
      | Label         | Icon             | Route           |
      | Dashboard     | bi-speedometer2  | /dashboard      |
      | Projects      | bi-folder2       | /projects       |
      | Notifications | bi-bell          | /notifications  |
      | Settings      | bi-gear          | /admin          |

  @sidebar
  Scenario: Active route highlighting
    Given I am on the "/projects" page
    Then the "Projects" nav item should have the "active" class
    And other nav items should not have the "active" class

  @sidebar
  Scenario: Organization selector
    Given I belong to 2 organizations: "Acme Corp" and "Beta Labs"
    Then the sidebar should show an organization selector
    And the currently selected organization should be displayed at the top

  @sidebar @responsive
  Scenario: Sidebar collapses on small screens
    Given the viewport width is less than 768px
    Then the sidebar should be collapsed by default
    And a toggle button should be available to expand/collapse

  # ---------------------------------------------------------------------------
  # Dashboard Page
  # ---------------------------------------------------------------------------
  @dashboard
  Scenario: Dashboard displays overview statistics and lists
    When I navigate to "/dashboard"
    Then the DashboardComponent should load and display:
      | Section            | Content                                |
      | Stats cards row    | Total Projects, Total Tasks, In Progress, Overdue |
      | Recent Projects    | List of latest projects with names     |
      | My Tasks           | List of tasks assigned to me           |

  @dashboard
  Scenario: My Tasks shows priority and status badges
    Given I have tasks assigned to me:
      | Task Key | Title            | Priority | Status      |
      | WEB-1    | Design homepage  | HIGH     | IN_PROGRESS |
      | WEB-5    | Fix nav bug      | CRITICAL | TODO        |
    Then each task should show:
      | Element        | Component           |
      | Priority badge | PriorityBadgeComponent (colored icon) |
      | Status badge   | StatusBadgeComponent (colored label)  |

  # ---------------------------------------------------------------------------
  # Shared Components
  # ---------------------------------------------------------------------------
  @shared-components
  Scenario: Loading spinner displays during async operations
    Given a page is loading data from the API
    Then the LoadingSpinnerComponent should be shown
    And it should accept:
      | Input     | Description                    |
      | size      | "sm" / "md" / "lg"             |
      | message   | Optional loading text          |
      | minHeight | Minimum container height       |

  @shared-components
  Scenario: Confirm dialog for destructive actions
    When a destructive action is triggered (e.g., delete, remove)
    Then the ConfirmDialogComponent should display as a modal with:
      | Input        | Description                     |
      | title        | Dialog title                    |
      | message      | Confirmation message            |
      | confirmLabel | Confirm button text             |
      | confirmClass | CSS class (e.g., "btn-danger")  |
    And it should emit "confirmed" or "cancelled" events

  @shared-components
  Scenario: User avatar component
    Given a user has first_name "Bob" and last_name "Smith"
    When the UserAvatarComponent renders
    Then if the user has an avatar URL, it should display the image
    And if no avatar, it should display initials "BS"
    And the background color should be deterministic based on name hash
    And sizes should be "sm" (24px), "md" (32px), or "lg" (48px)

  @shared-components
  Scenario: Priority badge component
    Then priority badges should render as:
      | Priority | Icon Color | Icon                          |
      | CRITICAL | red        | bi-exclamation-triangle-fill  |
      | HIGH     | orange     | bi-arrow-up                   |
      | MEDIUM   | blue       | bi-dash                       |
      | LOW      | gray       | bi-arrow-down                 |

  @shared-components
  Scenario: Status badge component
    Then status badges should render as colored Bootstrap badges:
      | Status      | CSS Class          |
      | BACKLOG     | bg-secondary       |
      | TODO        | bg-primary         |
      | IN_PROGRESS | bg-warning         |
      | IN_REVIEW   | bg-info            |
      | DONE        | bg-success         |
      | CANCELLED   | bg-dark            |

  @shared-components
  Scenario: Empty state component
    When a list has no data to display
    Then the EmptyStateComponent should show:
      | Element   | Description                         |
      | Icon      | Large Bootstrap icon                |
      | Title     | "No items found" or custom title    |
      | Subtitle  | Optional descriptive text           |
      | Action    | Content projection for CTA button   |

  @shared-components
  Scenario: Toast notifications
    When an action succeeds or fails
    Then the ToastService should:
      | Step                                          |
      | Add a toast to the signal-based queue         |
      | Auto-dismiss after the configured timeout     |
    And toast types should be:
      | Type    | CSS Class        | Icon                  |
      | success | bg-success       | bi-check-circle       |
      | error   | bg-danger        | bi-x-circle           |
      | warning | bg-warning       | bi-exclamation-triangle|
      | info    | bg-info          | bi-info-circle        |

  # ---------------------------------------------------------------------------
  # Shared Pipes
  # ---------------------------------------------------------------------------
  @pipes
  Scenario: TimeAgo pipe formats relative timestamps
    Then the TimeAgoPipe should transform dates:
      | Input                     | Output         |
      | 30 seconds ago            | just now       |
      | 3 minutes ago             | 3 minutes ago  |
      | 2 hours ago               | 2 hours ago    |
      | 1 day ago                 | 1 day ago      |
      | 5 days ago                | 5 days ago     |
      | 45 days ago               | 1 month ago    |
      | 400 days ago              | 1 year ago     |

  @pipes
  Scenario: Truncate pipe truncates long text
    Given text "This is a very long description that should be truncated"
    When TruncatePipe is applied with limit 20
    Then the output should be "This is a very long ..."

  # ---------------------------------------------------------------------------
  # Guards and Route Protection
  # ---------------------------------------------------------------------------
  @guards
  Scenario: Auth guard protects routes
    Given I am NOT authenticated
    When I try to navigate to "/dashboard"
    Then the authGuard should block the navigation
    And I should be redirected to "/auth/login"

  @guards
  Scenario: Auth guard waits during initial loading
    Given the app is initializing and AuthService.isLoading is true
    Then the authGuard should poll every 50ms (up to 5 seconds)
    And once isLoading becomes false and isAuthenticated is true
    Then navigation should proceed

  @guards
  Scenario: Guest guard redirects authenticated users
    Given I am authenticated
    When I try to navigate to "/auth/login"
    Then the guestGuard should redirect me to "/dashboard"

  # ---------------------------------------------------------------------------
  # 404 Not Found Page
  # ---------------------------------------------------------------------------
  @not-found
  Scenario: Navigating to unknown route shows 404
    When I navigate to "/some/nonexistent/route"
    Then the NotFoundComponent should render with:
      | Element     | Content                 |
      | Heading     | "404" (large, muted)    |
      | Message     | "Page not found"        |
      | Button      | "Back to Dashboard"     |
    And clicking the button should navigate to "/dashboard"
