/**
 * Reports Dashboard component types and i18n keys
 */
export interface ChartDataPoint {
  name: string;
  value: number;
}

export interface ChartSeriesData {
  name: string;
  series: ChartDataPoint[];
}

export interface ColorScheme {
  domain: string[];
}

export interface ReportsDashboardI18nKeys {
  title: string;
  projectReports: string;
  exportCsv: string;
  totalTasks: string;
  completed: string;
  overdue: string;
  completion: string;
  tasksByStatus: string;
  tasksByPriority: string;
  burndown: string;
  velocity: string;
  assigneeWorkload: string;
  exportDownloaded: string;
  exportFailed: string;
}

export const REPORTS_DASHBOARD_I18N_KEYS: ReportsDashboardI18nKeys = {
  title: 'reports.title',
  projectReports: 'reports.projectReports',
  exportCsv: 'reports.exportCsv',
  totalTasks: 'reports.totalTasks',
  completed: 'reports.completed',
  overdue: 'reports.overdue',
  completion: 'reports.completion',
  tasksByStatus: 'reports.tasksByStatus',
  tasksByPriority: 'reports.tasksByPriority',
  burndown: 'reports.burndown',
  velocity: 'reports.velocity',
  assigneeWorkload: 'reports.assigneeWorkload',
  exportDownloaded: 'reports.exportDownloaded',
  exportFailed: 'reports.exportFailed',
};
