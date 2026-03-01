import { Project, TaskListItem } from '@models/index';

/**
 * Dashboard component types and i18n keys
 */
export interface DashboardStats {
  totalProjects: number;
  totalTasks: number;
  inProgress: number;
  overdue: number;
}

export interface DashboardI18nKeys {
  title: string;
  welcome: string;
  newProject: string;
  totalProjects: string;
  myTasks: string;
  inProgress: string;
  overdue: string;
  recentProjects: string;
  noProjects: string;
  noTasks: string;
}

export const DASHBOARD_I18N_KEYS: DashboardI18nKeys = {
  title: 'dashboard.title',
  welcome: 'dashboard.welcome',
  newProject: 'dashboard.newProject',
  totalProjects: 'dashboard.totalProjects',
  myTasks: 'dashboard.myTasks',
  inProgress: 'dashboard.inProgress',
  overdue: 'dashboard.overdue',
  recentProjects: 'dashboard.recentProjects',
  noProjects: 'dashboard.noProjects',
  noTasks: 'dashboard.noTasks',
};
