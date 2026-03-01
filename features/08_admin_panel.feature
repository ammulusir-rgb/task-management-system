# =============================================================================
# Feature 08: Admin Panel (Organization Settings & Member Management)
# Module: frontend/features/admin
# Pages: Org Settings, Member Management
# =============================================================================

@admin
Feature: Admin Panel — Organization Settings and Member Management
  As an organization owner or admin
  I want a dedicated admin panel to manage organization settings and members
  So that I can control access and configure my workspace

  Background:
    Given I am authenticated as "alice@example.com"
    And I am the OWNER of "Acme Corporation"
    And the admin panel is accessible at "/admin"

  # ---------------------------------------------------------------------------
  # Organization Settings Page
  # ---------------------------------------------------------------------------
  @org-settings
  Scenario: View organization settings
    When I navigate to "/admin"
    Then the OrgSettingsComponent should load
    And a breadcrumb should show: Dashboard > Organization Settings
    And the form should display current organization data:
      | Field       | Current Value         |
      | Name        | Acme Corporation      |
      | Description | Enterprise task mgmt  |

  @org-settings
  Scenario: Update organization settings
    When I change the name to "Acme Corp International"
    And I update the description to "Global project management"
    And I click "Save Changes"
    Then a PATCH request should be sent to "/api/v1/organizations/{org_id}/"
    And the button should show "Saving..." while the request is in progress
    And on success, a toast "Settings saved" should appear
    And on failure, a toast "Save failed" should appear

  @org-settings
  Scenario: Navigate to member management
    When I click the "Manage Members" button
    Then I should be navigated to "/admin/members"

  # ---------------------------------------------------------------------------
  # Member Management Page
  # ---------------------------------------------------------------------------
  @member-management
  Scenario: View organization members table
    Given "Acme Corporation" has the following members:
      | Name           | Email               | Role   | Joined     |
      | Alice Johnson  | alice@example.com   | OWNER  | Jan 15, 2025|
      | Bob Smith      | bob@example.com     | ADMIN  | Feb 1, 2025 |
      | Carol Davis    | carol@example.com   | MEMBER | Mar 10, 2025|
    When I navigate to "/admin/members"
    Then a breadcrumb should show: Dashboard > Settings > Members
    And a table should display all 3 members with columns:
      | Column  | Content                                      |
      | Member  | Avatar + Full name + Email                   |
      | Role    | Dropdown selector (OWNER/ADMIN/MEMBER)       |
      | Joined  | Formatted date                               |
      | Actions | Remove button (disabled for OWNER)            |

  @member-management
  Scenario: OWNER role dropdown is disabled
    Given Alice's role is "OWNER"
    Then the role dropdown for Alice should be disabled
    And the remove button should not be shown for OWNER

  @member-management @invite
  Scenario: Invite a new member
    When I click the "Invite" button
    Then an invite form should appear with:
      | Field | Type          | Default  |
      | Email | email input   | empty    |
      | Role  | select        | member   |
    When I enter "dave@example.com" and select role "member"
    And I click "Send"
    Then a POST request should be sent to "/api/v1/organizations/{org_id}/members/"
    And on success:
      | Action                              |
      | Toast "Member invited" appears      |
      | Invite form closes                  |
      | Member list refreshes               |
    And on failure, toast "Failed to invite member" appears

  @member-management @role-change
  Scenario: Change a member's role inline
    Given Bob is listed with role "ADMIN"
    When I change Bob's role dropdown to "MEMBER"
    Then a PATCH request should update Bob's membership role
    And a toast "Role updated" should appear
    And the table should reflect the new role

  @member-management @removal
  Scenario: Remove a member with confirmation
    Given Carol is listed as a MEMBER
    When I click the remove button (trash icon) for Carol
    Then a ConfirmDialog modal should appear:
      | Property     | Value                                 |
      | Title        | Remove Member                         |
      | Message      | Are you sure you want to remove this member? |
      | Confirm btn  | Remove (btn-danger)                   |
    When I click "Remove"
    Then a DELETE request should remove Carol from the organization
    And Carol should disappear from the member list
    And a toast "Member removed" should appear

  @member-management @removal
  Scenario: Cancel member removal
    When the ConfirmDialog appears
    And I click "Cancel"
    Then the dialog should close
    And no API request should be sent
    And the member list should remain unchanged
