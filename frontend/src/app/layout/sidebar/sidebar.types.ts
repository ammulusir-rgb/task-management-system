/**
 * Sidebar component types and i18n keys
 */
export interface NavItem {
  labelKey: string;
  icon: string;
  route: string;
}

export interface SidebarI18nKeys {
  dashboard: string;
  projects: string;
  myTasks: string;
  notifications: string;
  settings: string;
}

export const SIDEBAR_I18N_KEYS: SidebarI18nKeys = {
  dashboard: 'sidebar.dashboard',
  projects: 'sidebar.projects',
  myTasks: 'sidebar.myTasks',
  notifications: 'sidebar.notifications',
  settings: 'sidebar.settings',
};
