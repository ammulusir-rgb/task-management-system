import { Component, inject, OnInit, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { AuthService } from '@core/services/auth.service';
import { ProjectService } from '@core/services/project.service';
import { TaskService } from '@core/services/task.service';
import { Project, TaskListItem } from '@models/index';
import { LoadingSpinnerComponent } from '@shared/components/loading-spinner/loading-spinner.component';
import { PriorityBadgeComponent } from '@shared/components/priority-badge/priority-badge.component';
import { StatusBadgeComponent } from '@shared/components/status-badge/status-badge.component';
import { TranslatePipe } from '@shared/pipes/translate.pipe';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    RouterLink,
    LoadingSpinnerComponent,
    PriorityBadgeComponent,
    StatusBadgeComponent,
    TranslatePipe,
  ],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss'],
})
export class DashboardComponent implements OnInit {
  authService = inject(AuthService);
  private projectService = inject(ProjectService);
  private taskService = inject(TaskService);

  loading = signal(true);
  projects = signal<Project[]>([]);
  myTasks = signal<TaskListItem[]>([]);
  overdueTasks = signal<TaskListItem[]>([]);

  ngOnInit(): void {
    this.loadData();
  }

  private loadData(): void {
    this.projectService.list({ page_size: 10 }).subscribe({
      next: (res) => this.projects.set(res.results),
    });

    this.taskService
      .list({
        assignee: this.authService.currentUser()?.id,
        status: 'todo,in_progress,in_review',
        ordering: '-priority,due_date',
        page_size: 20,
      })
      .subscribe({
        next: (res) => {
          this.myTasks.set(res.results);
          const now = new Date();
          this.overdueTasks.set(
            res.results.filter(
              (t) => t.due_date && new Date(t.due_date) < now && t.status !== 'done'
            )
          );
          this.loading.set(false);
        },
        error: () => this.loading.set(false),
      });
  }
}
