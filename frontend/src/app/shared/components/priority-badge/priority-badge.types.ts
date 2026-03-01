/**
 * Priority Badge component types and i18n keys
 */
export type PriorityLevel = 'critical' | 'high' | 'medium' | 'low';

export const PRIORITY_ICON_MAP: Record<PriorityLevel, string> = {
  critical: 'bi-exclamation-triangle-fill',
  high: 'bi-arrow-up',
  medium: 'bi-dash',
  low: 'bi-arrow-down',
};

export interface PriorityBadgeI18nKeys {
  critical: string;
  high: string;
  medium: string;
  low: string;
}

export const PRIORITY_BADGE_I18N_KEYS: PriorityBadgeI18nKeys = {
  critical: 'priority.critical',
  high: 'priority.high',
  medium: 'priority.medium',
  low: 'priority.low',
};
