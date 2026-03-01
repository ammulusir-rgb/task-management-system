import { Task, Comment, ActivityLog, Attachment, TaskListItem } from '@models/index';

/**
 * Task Detail component types and i18n keys
 */
export interface TaskDetailState {
  task: Task | null;
  subtasks: TaskListItem[];
  comments: Comment[];
  activityLogs: ActivityLog[];
  attachments: Attachment[];
}

export interface TaskDetailI18nKeys {
  description: string;
  subtasks: string;
  comments: string;
  activity: string;
  details: string;
  status: string;
  priority: string;
  dueDate: string;
  estimatedHours: string;
  tags: string;
  addTag: string;
  timeTracking: string;
  estimated: string;
  actual: string;
  attachments: string;
  upload: string;
  created: string;
  updated: string;
  started: string;
  completed: string;
  writeComment: string;
  addDescription: string;
  dblClickEdit: string;
  changed: string;
  from: string;
  to: string;
}

export const TASK_DETAIL_I18N_KEYS: TaskDetailI18nKeys = {
  description: 'taskDetail.description',
  subtasks: 'taskDetail.subtasks',
  comments: 'taskDetail.comments',
  activity: 'taskDetail.activity',
  details: 'taskDetail.details',
  status: 'taskDetail.status',
  priority: 'taskDetail.priority',
  dueDate: 'taskDetail.dueDate',
  estimatedHours: 'taskDetail.estimatedHours',
  tags: 'taskDetail.tags',
  addTag: 'taskDetail.addTag',
  timeTracking: 'taskDetail.timeTracking',
  estimated: 'taskDetail.estimated',
  actual: 'taskDetail.actual',
  attachments: 'taskDetail.attachments',
  upload: 'taskDetail.upload',
  created: 'taskDetail.created',
  updated: 'taskDetail.updated',
  started: 'taskDetail.started',
  completed: 'taskDetail.completed',
  writeComment: 'taskDetail.writeComment',
  addDescription: 'taskDetail.addDescription',
  dblClickEdit: 'taskDetail.dblClickEdit',
  changed: 'taskDetail.changed',
  from: 'taskDetail.from',
  to: 'taskDetail.to',
};
