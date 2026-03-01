import {
  Component,
  inject,
  OnInit,
  OnDestroy,
  signal,
} from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { DatePipe } from '@angular/common';
import { TaskService } from '@core/services/task.service';
import { ProjectService } from '@core/services/project.service';
import { TranslationService } from '@core/services/translation.service';
import { Task, Comment, ActivityLog, Attachment, TaskListItem, User } from '@models/index';
import { LoadingSpinnerComponent } from '@shared/components/loading-spinner/loading-spinner.component';
import { PriorityBadgeComponent } from '@shared/components/priority-badge/priority-badge.component';
import { StatusBadgeComponent } from '@shared/components/status-badge/status-badge.component';
import { UserAvatarComponent } from '@shared/components/user-avatar/user-avatar.component';
import { TranslatePipe } from '@shared/pipes/translate.pipe';
import { TimeAgoPipe } from '@shared/pipes/time-ago.pipe';
import { ToastService } from '@shared/services/toast.service';

@Component({
  selector: 'app-task-detail',
  standalone: true,
  imports: [
    RouterLink,
    FormsModule,
    DatePipe,
    LoadingSpinnerComponent,
    PriorityBadgeComponent,
    StatusBadgeComponent,
    UserAvatarComponent,
    TranslatePipe,
    TimeAgoPipe,
  ],
  templateUrl: './task-detail.component.html',
  styleUrls: ['./task-detail.component.scss'],
})
export class TaskDetailComponent implements OnInit, OnDestroy {
  private route = inject(ActivatedRoute);
  private taskService = inject(TaskService);
  private projectService = inject(ProjectService);
  private toast = inject(ToastService);
  private i18n = inject(TranslationService);

  loading = signal(true);
  task = signal<Task | null>(null);
  subtasks = signal<TaskListItem[]>([]);
  comments = signal<Comment[]>([]);
  activityLogs = signal<ActivityLog[]>([]);
  attachments = signal<Attachment[]>([]);
  projectMembers = signal<User[]>([]);

  editingTitle = signal(false);
  editingDescription = signal(false);
  titleDraft = '';
  descriptionDraft = '';
  newComment = '';

  private taskId = '';

  ngOnInit(): void {
    this.taskId = this.route.snapshot.params['taskId'];
    this.loadTask();
  }

  ngOnDestroy(): void {}

  private loadTask(): void {
    this.taskService.get(this.taskId).subscribe({
      next: (task) => {
        this.task.set(task);
        this.loading.set(false);
        this.loadRelated();
      },
      error: () => this.loading.set(false),
    });
  }

  private loadRelated(): void {
    this.taskService.getComments(this.taskId).subscribe({
      next: (res) => this.comments.set(res.results),
    });
    this.taskService.getActivity(this.taskId).subscribe({
      next: (res) => this.activityLogs.set(res.results),
    });
    this.taskService.getAttachments(this.taskId).subscribe({
      next: (res) => this.attachments.set(res),
    });
    this.taskService.list({ parent: this.taskId }).subscribe({
      next: (res) => this.subtasks.set(res.results),
    });
    // Load project members for assignee picker
    const projectId = this.task()?.project;
    if (projectId) {
      this.projectService.getMembers(projectId).subscribe({
        next: (members) => this.projectMembers.set(members.map((m) => m.user)),
      });
    }
  }

  startEditTitle(): void {
    this.titleDraft = this.task()!.title;
    this.editingTitle.set(true);
  }

  saveTitle(): void {
    if (!this.titleDraft.trim()) return this.cancelEditTitle();
    this.updateField('title', this.titleDraft.trim());
    this.editingTitle.set(false);
  }

  cancelEditTitle(): void {
    this.editingTitle.set(false);
  }

  startEditDescription(): void {
    this.descriptionDraft = this.task()!.description ?? '';
    this.editingDescription.set(true);
  }

  saveDescription(): void {
    this.updateField('description', this.descriptionDraft);
    this.editingDescription.set(false);
  }

  cancelEditDescription(): void {
    this.editingDescription.set(false);
  }

  updateField(field: string, value: any): void {
    this.taskService.update(this.taskId, { [field]: value }).subscribe({
      next: (updated) => {
        this.task.set(updated);
        this.toast.success(this.i18n.t('taskDetail.fieldUpdated', { field: field.replace('_', ' ') }));
      },
      error: () => this.toast.error(this.i18n.t('taskDetail.updateFailed')),
    });
  }

  addComment(): void {
    const content = this.newComment.trim();
    if (!content) return;
    this.taskService.addComment(this.taskId, content).subscribe({
      next: (comment) => {
        this.comments.update((cs) => [comment, ...cs]);
        this.newComment = '';
      },
    });
  }

  toggleSubtask(sub: TaskListItem): void {
    const newStatus = sub.status === 'done' ? 'todo' : 'done';
    this.taskService.update(sub.id, { status: newStatus }).subscribe({
      next: () => {
        this.subtasks.update((subs) =>
          subs.map((s) => (s.id === sub.id ? { ...s, status: newStatus } : s))
        );
      },
    });
  }

  addTag(event: Event): void {
    const input = event.target as HTMLInputElement;
    const tag = input.value.trim();
    if (!tag || this.task()!.tags.includes(tag)) {
      input.value = '';
      return;
    }
    this.updateField('tags', [...this.task()!.tags, tag]);
    input.value = '';
  }

  removeTag(tag: string): void {
    this.updateField('tags', this.task()!.tags.filter((t: string) => t !== tag));
  }

  uploadAttachment(event: Event): void {
    const file = (event.target as HTMLInputElement).files?.[0];
    if (!file) return;
    this.taskService.uploadAttachment(this.taskId, file).subscribe({
      next: (att: Attachment) => {
        this.attachments.update((atts) => [...atts, att]);
        this.toast.success(this.i18n.t('taskDetail.fileUploaded'));
      },
      error: () => this.toast.error(this.i18n.t('taskDetail.uploadFailed')),
    });
  }

  formatSize(bytes: number): string {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  }
}
