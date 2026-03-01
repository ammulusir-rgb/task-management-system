import { TaskListItem } from '@models/index';

/**
 * Board component types and i18n keys
 */
export type TasksByColumn = Record<string, TaskListItem[]>;

export interface BoardI18nKeys {
  addColumn: string;
  wip: string;
  columnAdded: string;
  moveError: string;
}

export const BOARD_I18N_KEYS: BoardI18nKeys = {
  addColumn: 'board.addColumn',
  wip: 'board.wip',
  columnAdded: 'board.columnAdded',
  moveError: 'board.moveError',
};
