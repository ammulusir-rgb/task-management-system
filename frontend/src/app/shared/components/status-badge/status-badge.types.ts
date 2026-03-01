/**
 * Status Badge component types and i18n keys
 */
export type TaskStatus = 'todo' | 'in_progress' | 'in_review' | 'done' | 'cancelled';

export interface StatusBadgeI18nKeys {
  todo: string;
  inProgress: string;
  inReview: string;
  done: string;
  cancelled: string;
}

export const STATUS_BADGE_I18N_KEYS: StatusBadgeI18nKeys = {
  todo: 'status.todo',
  inProgress: 'status.inProgress',
  inReview: 'status.inReview',
  done: 'status.done',
  cancelled: 'status.cancelled',
};
