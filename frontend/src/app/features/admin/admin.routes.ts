import { Routes } from '@angular/router';

export const ADMIN_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./org-settings/org-settings.component').then(
        (m) => m.OrgSettingsComponent
      ),
  },
  {
    path: 'members',
    loadComponent: () =>
      import('./member-management/member-management.component').then(
        (m) => m.MemberManagementComponent
      ),
  },
  {
    path: 'users',
    loadComponent: () =>
      import('./user-management/user-management.component').then(
        (m) => m.UserManagementComponent
      ),
  },
  {
    path: 'teams',
    loadComponent: () =>
      import('./team-management/team-management.component').then(
        (m) => m.TeamManagementComponent
      ),
  },
  {
    path: 'email',
    loadComponent: () =>
      import('./email-configuration/email-configuration.component').then(
        (m) => m.EmailConfigurationComponent
      ),
  },
];
