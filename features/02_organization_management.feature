# =============================================================================
# Feature 02: Organization Management (Multi-Tenancy)
# Module: apps/organizations
# Roles: OWNER > ADMIN > MEMBER
# =============================================================================

@organizations
Feature: Organization Management
  As a platform user
  I want to create and manage organizations (tenants)
  So that I can collaborate with my team within a shared workspace

  Background:
    Given I am authenticated as "alice@example.com"
    And the organization roles are:
      | Role   | Permissions                                          |
      | OWNER  | Full control, transfer ownership, delete organization |
      | ADMIN  | Manage members, projects, settings                   |
      | MEMBER | View and participate in assigned projects             |

  # ---------------------------------------------------------------------------
  # Organization CRUD
  # ---------------------------------------------------------------------------
  @org-create
  Scenario: Create a new organization
    When I send a POST request to "/api/v1/organizations/" with:
      | Field       | Value                          |
      | name        | Acme Corporation               |
      | description | Enterprise task management      |
      | website     | https://acme.example.com       |
    Then the response status should be 201 Created
    And the organization should be created with:
      | Field      | Value                |
      | name       | Acme Corporation     |
      | slug       | acme-corporation     |
      | is_active  | true                 |
      | created_by | alice@example.com    |
    And I should automatically become the OWNER of this organization
    And an OrganizationMember record should be created with role "OWNER"

  @org-create
  Scenario: Organization slug is auto-generated and unique
    Given an organization "Acme Corporation" already exists with slug "acme-corporation"
    When I create another organization named "Acme Corporation"
    Then the new organization should have slug "acme-corporation-1"

  @org-read
  Scenario: List my organizations
    Given I am a member of the following organizations:
      | Name               | My Role |
      | Acme Corporation   | OWNER   |
      | Beta Labs          | MEMBER  |
    When I send a GET request to "/api/v1/organizations/"
    Then the response should contain 2 organizations
    And each organization should include its member count

  @org-read
  Scenario: View organization details
    Given I am a member of "Acme Corporation"
    When I send a GET request to "/api/v1/organizations/{org_id}/"
    Then the response should include:
      | Field       | Value                    |
      | id          | <uuid>                   |
      | name        | Acme Corporation         |
      | slug        | acme-corporation         |
      | description | Enterprise task management|
      | logo        | null or <url>            |
      | member_count| <number>                 |
      | created_at  | <datetime>               |

  @org-update
  Scenario: Update organization settings as OWNER
    Given I am the OWNER of "Acme Corporation"
    When I send a PATCH request to "/api/v1/organizations/{org_id}/" with:
      | name        | Acme Corp (Renamed)     |
      | description | Updated description      |
    Then the response status should be 200 OK
    And the organization name should be updated

  @org-update @permissions
  Scenario: MEMBER cannot update organization settings
    Given I am a MEMBER of "Acme Corporation"
    When I try to update the organization settings
    Then the response status should be 403 Forbidden

  # ---------------------------------------------------------------------------
  # Member Management
  # ---------------------------------------------------------------------------
  @members
  Scenario: List organization members
    Given "Acme Corporation" has the following members:
      | Email               | Role   | Joined     |
      | alice@example.com   | OWNER  | 2025-01-15 |
      | bob@example.com     | ADMIN  | 2025-02-01 |
      | carol@example.com   | MEMBER | 2025-03-10 |
    When I send a GET request to "/api/v1/organizations/{org_id}/members/"
    Then the response should contain 3 members
    And each member should include:
      | Field    | Description                  |
      | id       | Member record UUID           |
      | user     | Nested user object (email, name, avatar) |
      | role     | OWNER / ADMIN / MEMBER       |
      | joined_at| Membership creation date     |

  @members @invite
  Scenario: Invite a new member as ADMIN
    Given I am an ADMIN of "Acme Corporation"
    When I send a POST request to "/api/v1/organizations/{org_id}/members/" with:
      | email | dave@example.com |
      | role  | MEMBER           |
    Then the response status should be 201 Created
    And "dave@example.com" should be added as a MEMBER
    And a notification should be sent to Dave

  @members @role-change
  Scenario: Change a member's role
    Given I am the OWNER of "Acme Corporation"
    And "bob@example.com" is an ADMIN
    When I send a PATCH request to update Bob's role to "MEMBER"
    Then Bob's role should be updated to MEMBER

  @members @role-change @permissions
  Scenario: MEMBER cannot change roles
    Given I am a MEMBER of "Acme Corporation"
    When I try to change another member's role
    Then the response status should be 403 Forbidden

  @members @removal
  Scenario: Remove a member from the organization
    Given I am the OWNER of "Acme Corporation"
    And "carol@example.com" is a MEMBER
    When I send a DELETE request to remove Carol
    Then Carol should be removed from the organization
    And Carol should lose access to all projects in the organization

  @members @removal @protection
  Scenario: Last OWNER cannot be removed
    Given I am the only OWNER of "Acme Corporation"
    When I try to remove myself from the organization
    Then the response status should be 400 Bad Request
    And the error should state "Cannot remove the last owner"

  @members @permissions
  Scenario: Non-members cannot access organization data
    Given I am NOT a member of "Secret Corp"
    When I try to access "/api/v1/organizations/{secret_org_id}/"
    Then the response status should be 403 Forbidden
