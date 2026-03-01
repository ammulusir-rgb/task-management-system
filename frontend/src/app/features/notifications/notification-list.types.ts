/**
 * Notification List component types and i18n keys
 */
export interface NotificationIconMap {
  [key: string]: string;
}

export const NOTIFICATION_ICON_MAP: NotificationIconMap = {
  task_assigned: 'bi-person-check text-primary',
  task_updated: 'bi-pencil-square text-info',
  task_completed: 'bi-check-circle text-success',
  comment_added: 'bi-chat-left-text text-secondary',
  mentioned: 'bi-at text-warning',
  due_date_reminder: 'bi-clock text-warning',
  task_overdue: 'bi-exclamation-triangle text-danger',
  project_invitation: 'bi-envelope text-primary',
};

export interface NotificationListI18nKeys {
  title: string;
  markAllRead: string;
  clearRead: string;
  empty: string;
  allCaughtUp: string;
}

export const NOTIFICATION_LIST_I18N_KEYS: NotificationListI18nKeys = {
  title: 'notifications.title',
  markAllRead: 'notifications.markAllRead',
  clearRead: 'notifications.clearRead',
  empty: 'notifications.empty',
  allCaughtUp: 'notifications.allCaughtUp',
};
