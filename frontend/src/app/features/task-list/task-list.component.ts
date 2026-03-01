import {
  Component,
  inject,
  OnInit,
  signal,
  computed,
} from '@angular/core';
import { FormsModule, ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { DatePipe, TitleCasePipe, NgClass } from '@angular/common';
import { AuthService } from '@core/services/auth.service';
import { TaskService } from '@core/services/task.service';
import { ProjectService } from '@core/services/project.service';
import { TranslationService } from '@core/services/translation.service';
import { TaskListItem, TaskStatus, TaskPriority, Project, User, Task } from '@models/index';
import { ToastService } from '@shared/services/toast.service';
import { LoadingSpinnerComponent } from '@shared/components/loading-spinner/loading-spinner.component';
import { EmptyStateComponent } from '@shared/components/empty-state/empty-state.component';
import { PriorityBadgeComponent } from '@shared/components/priority-badge/priority-badge.component';
import { StatusBadgeComponent } from '@shared/components/status-badge/status-badge.component';
import { TranslatePipe } from '@shared/pipes/translate.pipe';

interface TaskCreateRequest {
  project: string;
  title: string;
  description?: string;
  status: TaskStatus;
  priority: TaskPriority;
  assignee?: string;
  due_date?: string;
  estimated_hours?: number | null;
}

@Component({
  selector: 'app-task-list',
  standalone: true,
  imports: [
    FormsModule,
    ReactiveFormsModule,
    RouterLink,
    DatePipe,
    TitleCasePipe,
    NgClass,
    LoadingSpinnerComponent,
    EmptyStateComponent,
    PriorityBadgeComponent,
    StatusBadgeComponent,
    TranslatePipe,
  ],
  templateUrl: './task-list.component.html',
  styleUrls: ['./task-list.component.scss'],
})
export class TaskListComponent implements OnInit {
  private taskService = inject(TaskService);
  private projectService = inject(ProjectService);
  private authService = inject(AuthService);
  private fb = inject(FormBuilder);
  private toast = inject(ToastService);
  i18n = inject(TranslationService);

  loading = signal(true);
  tasks = signal<TaskListItem[]>([]);
  hasMore = signal(false);
  page = 1;

  // Filters
  statusFilter = signal<string>('');
  priorityFilter = signal<string>('');
  searchQuery = signal<string>('');
  onlyMyTasks = signal<boolean>(true);

  // Task Creation Modal
  showCreateModal = signal(false);
  creatingTask = signal(false);
  taskFormSubmitted = signal(false);
  availableProjects = signal<Project[]>([]);
  projectMembers = signal<User[]>([]);

  taskForm = this.fb.nonNullable.group({
    project: ['', Validators.required],
    title: ['', Validators.required],
    description: [''],
    status: ['todo'],
    priority: ['medium'],
    assignee: [''],
    due_date: [''],
    estimated_hours: [null],
  });

  filteredTasks = computed(() => {
    let result = this.tasks();
    const s = this.statusFilter();
    const p = this.priorityFilter();
    const q = this.searchQuery().toLowerCase();

    if (s) result = result.filter((t) => t.status === s);
    if (p) result = result.filter((t) => t.priority === p);
    if (q) result = result.filter((t) => t.title.toLowerCase().includes(q) || t.task_key.toLowerCase().includes(q));

    return result;
  });

  statuses: TaskStatus[] = ['backlog', 'todo', 'in_progress', 'in_review', 'done', 'cancelled'];
  priorities: TaskPriority[] = ['critical', 'high', 'medium', 'low'];

  ngOnInit(): void {
    this.loadTasks();
    this.loadProjects();
  }

  loadTasks(): void {
    this.loading.set(true);
    const params: any = { page: this.page };

    // Filter by current user (my tasks)
    if (this.onlyMyTasks()) {
      const user = this.authService.currentUser();
      if (user?.id) {
        params.assignee = user.id;
      }
    }

    this.taskService.list(params).subscribe({
      next: (res) => {
        if (this.page === 1) {
          this.tasks.set(res.results);
        } else {
          this.tasks.update((ts) => [...ts, ...res.results]);
        }
        this.hasMore.set(!!res.next);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  loadMore(): void {
    this.page++;
    this.loadTasks();
  }

  toggleMyTasks(): void {
    this.onlyMyTasks.update((v) => !v);
    this.page = 1;
    this.loadTasks();
  }

  onStatusChange(value: string): void {
    this.statusFilter.set(value);
  }

  onPriorityChange(value: string): void {
    this.priorityFilter.set(value);
  }

  onSearch(value: string): void {
    this.searchQuery.set(value);
  }

  isOverdue(dueDate: string): boolean {
    return new Date(dueDate) < new Date();
  }

  // Task Creation Modal Methods
  loadProjects(): void {
    this.projectService.list().subscribe({
      next: (res) => this.availableProjects.set(res.results),
      error: () => this.availableProjects.set([])
    });
  }

  openCreateTaskModal(): void {
    this.showCreateModal.set(true);
    this.taskFormSubmitted.set(false);
  }

  closeCreateModal(): void {
    this.showCreateModal.set(false);
    this.taskForm.reset({
      status: 'todo',
      priority: 'medium'
    });
    this.taskFormSubmitted.set(false);
    this.creatingTask.set(false);
    this.projectMembers.set([]);
  }

  onProjectChange(): void {
    const projectId = this.taskForm.get('project')?.value;
    if (projectId) {
      this.projectService.getMembers(projectId).subscribe({
        next: (members) => this.projectMembers.set(members.map(member => member.user)),
        error: () => this.projectMembers.set([])
      });
    } else {
      this.projectMembers.set([]);
    }
  }

  onSubmitTask(): void {
    this.taskFormSubmitted.set(true);
    
    if (this.taskForm.invalid) return;

    this.creatingTask.set(true);
    
    const rawFormData = this.taskForm.getRawValue();
    
    // Create the task data object with proper typing
    const taskData: Partial<Task> = {
      project: rawFormData.project,
      title: rawFormData.title,
      status: rawFormData.status as TaskStatus,
      priority: rawFormData.priority as TaskPriority,
    };

    // Handle optional fields
    if (rawFormData.description) taskData.description = rawFormData.description;
    if (rawFormData.assignee) taskData.assignee = rawFormData.assignee as any; // Backend expects string ID
    if (rawFormData.due_date) taskData.due_date = rawFormData.due_date;
    if (rawFormData.estimated_hours) taskData.estimated_hours = rawFormData.estimated_hours;

    this.taskService.create(taskData).subscribe({
      next: (newTask) => {
        this.toast.success(this.i18n.t('taskForm.created'));
        this.closeCreateModal();
        
        // Add to tasks list if matches current filters
        const taskItem: TaskListItem = {
          id: newTask.id,
          task_key: newTask.task_key,
          title: newTask.title,
          status: newTask.status,
          priority: newTask.priority,
          assignee: newTask.assignee ? {
            id: newTask.assignee.id,
            first_name: newTask.assignee.first_name,
            last_name: newTask.assignee.last_name,
            avatar: newTask.assignee.avatar
          } : null,
          due_date: newTask.due_date,
          story_points: newTask.story_points,
          tags: newTask.tags,
          position: newTask.position,
          column: newTask.column,
          subtask_count: newTask.subtask_count,
          comment_count: newTask.comment_count
        };
        
        this.tasks.update((tasks: TaskListItem[]) => [taskItem, ...tasks]);
      },
      error: (error) => {
        console.error('Failed to create task:', error);
        this.toast.error(this.i18n.t('taskForm.createFailed'));
      },
      complete: () => this.creatingTask.set(false)
    });
  }
}
