/* ============================================================
   TypeScript interfaces mirroring backend API responses
   ============================================================ */

// ----- Auth -----
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  password_confirm: string;
  first_name: string;
  last_name: string;
}

export interface AuthResponse {
  access: string;
  user?: User;
}

export interface TokenRefreshResponse {
  access: string;
}

// ----- User -----
export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  role: 'admin' | 'manager' | 'member';
  avatar: string | null;
  phone: string;
  job_title: string;
  is_verified: boolean;
  is_active: boolean;
  date_joined: string;
}

// ----- Organization -----
export interface Organization {
  id: string;
  name: string;
  slug: string;
  description?: string;
  logo: string | null;
  website?: string;
  is_active: boolean;
  member_count: number;
  created_at: string;
}

export interface OrganizationMember {
  id: string;
  user: User;
  role: 'owner' | 'admin' | 'member';
  joined_at: string;
}

// ----- Project -----
export interface Project {
  id: string;
  name: string;
  slug: string;
  prefix: string;
  description: string;
  organization: string;
  organization_name: string;
  status: 'active' | 'archived' | 'deleted';
  created_by: string;
  member_count: number;
  task_count: number;
  created_at: string;
  updated_at: string;
}

// ----- Project Member -----
export interface ProjectMember {
  id: string;
  project: string;
  user: User;
  role: 'admin' | 'member' | 'viewer';
  is_active: boolean;
  created_at: string;
}

// ----- Board & Column -----
export interface Board {
  id: string;
  name: string;
  project: string;
  is_default: boolean;
  columns: Column[];
  created_at: string;
}

export interface Column {
  id: string;
  name: string;
  board: string;
  position: number;
  color: string;
  wip_limit: number | null;
  is_done_column: boolean;
  task_count: number;
}

// ----- Task -----
export interface Task {
  id: string;
  task_key: string;
  task_number: number;
  title: string;
  description: string;
  status: TaskStatus;
  priority: TaskPriority;
  column: string;
  column_name: string;
  board: string;
  project: string;
  assignee: User | null;
  reporter: User | null;
  parent: string | null;
  due_date: string | null;
  started_at: string | null;
  completed_at: string | null;
  story_points: number | null;
  estimated_hours: number | null;
  actual_hours: number | null;
  tags: string[];
  position: number;
  subtask_count: number;
  comment_count: number;
  attachment_count: number;
  created_at: string;
  updated_at: string;
}

export type TaskStatus = 'backlog' | 'todo' | 'in_progress' | 'in_review' | 'done' | 'cancelled';
export type TaskPriority = 'critical' | 'high' | 'medium' | 'low';

export interface TaskListItem {
  id: string;
  task_key: string;
  title: string;
  status: TaskStatus;
  priority: TaskPriority;
  assignee: Pick<User, 'id' | 'first_name' | 'last_name' | 'avatar'> | null;
  due_date: string | null;
  story_points: number | null;
  tags: string[];
  position: number;
  column: string;
  subtask_count: number;
  comment_count: number;
}

export interface TaskMoveRequest {
  column_id: string;
  position: number;
}

// ----- Comment -----
export interface Comment {
  id: string;
  task: string;
  author: User;
  content: string;
  parent: string | null;
  replies: Comment[];
  created_at: string;
  updated_at: string;
}

// ----- Attachment -----
export interface Attachment {
  id: string;
  task: string;
  uploaded_by: User;
  file: string;
  original_filename: string;
  file_size: number;
  mime_type: string;
  created_at: string;
}

// ----- Activity -----
export interface ActivityLog {
  id: string;
  task: string;
  user: User;
  action: string;
  field_name: string | null;
  old_value: any;
  new_value: any;
  created_at: string;
}

// ----- Notification -----
export interface Notification {
  id: string;
  notification_type: string;
  title: string;
  message: string;
  is_read: boolean;
  content_type: string | null;
  object_id: string | null;
  created_at: string;
}

// ----- Report -----
export interface ProjectSummary {
  total_tasks: number;
  completed_tasks: number;
  open_tasks: number;
  overdue_tasks: number;
  completion_rate: number;
  avg_cycle_time_hours: number | null;
}

export interface StatusDistribution {
  status: string;
  count: number;
}

export interface PriorityDistribution {
  priority: string;
  count: number;
}

export interface AssigneeWorkload {
  assignee__id: string | null;
  assignee__first_name: string;
  assignee__last_name: string;
  assignee__email: string;
  total: number;
  completed: number;
  in_progress: number;
}

export interface BurndownPoint {
  date: string;
  remaining: number;
  completed_cumulative: number;
  new_tasks: number;
}

export interface VelocityPoint {
  week: string;
  completed: number;
}

// ----- Email Configuration -----
export interface EmailConfiguration {
  id: string;
  organization: string;
  imap_enabled: boolean;
  imap_host: string;
  imap_port: number;
  imap_use_ssl: boolean;
  imap_username: string;
  imap_password_set: boolean;
  smtp_enabled: boolean;
  smtp_host: string;
  smtp_port: number;
  smtp_use_tls: boolean;
  smtp_username: string;
  smtp_password_set: boolean;
  task_email_address: string;
  default_project: string;
  auto_assign_reporter: boolean;
  created_at: string;
  updated_at: string;
}

export interface EmailRule {
  id: string;
  organization: string;
  name: string;
  rule_type: 'subject_contains' | 'sender_domain' | 'sender_email' | 'body_contains';
  rule_value: string;
  is_active: boolean;
  target_project: Project;
  default_assignee: User | null;
  default_priority: TaskPriority;
  default_status: TaskStatus;
  created_at: string;
  updated_at: string;
}

export interface ProcessedEmail {
  id: string;
  organization: string;
  message_id: string;
  subject: string;
  sender: string;
  received_at: string;
  processed_at: string;
  task_key: string | null;
  task_title: string | null;
  processing_error: string;
}

// ----- Paginated Response -----
export interface PaginatedResponse<T> {
  count: number;
  total_pages: number;
  current_page: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
