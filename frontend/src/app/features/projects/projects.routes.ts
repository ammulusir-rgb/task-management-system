import { Routes } from '@angular/router';

export const PROJECT_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./project-list/project-list.component').then(
        (m) => m.ProjectListComponent
      ),
  },
  {
    path: 'new',
    loadComponent: () =>
      import('./project-form/project-form.component').then(
        (m) => m.ProjectFormComponent
      ),
  },
  {
    path: ':projectId',
    loadComponent: () =>
      import('./project-detail/project-detail.component').then(
        (m) => m.ProjectDetailComponent
      ),
  },
  {
    path: ':projectId/edit',
    loadComponent: () =>
      import('./project-form/project-form.component').then(
        (m) => m.ProjectFormComponent
      ),
  },
];
