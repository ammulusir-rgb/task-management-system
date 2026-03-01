import { Component, inject, OnInit, signal } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { ProjectService } from '@core/services/project.service';
import { TranslationService } from '@core/services/translation.service';
import { Board, Project } from '@models/index';
import { LoadingSpinnerComponent } from '@shared/components/loading-spinner/loading-spinner.component';
import { TranslatePipe } from '@shared/pipes/translate.pipe';
import { ToastService } from '@shared/services/toast.service';

@Component({
  selector: 'app-project-detail',
  standalone: true,
  imports: [RouterLink, LoadingSpinnerComponent, TranslatePipe],
  templateUrl: './project-detail.component.html',
  styleUrls: ['./project-detail.component.scss'],
})
export class ProjectDetailComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private projectService = inject(ProjectService);
  private toast = inject(ToastService);
  private i18n = inject(TranslationService);

  loading = signal(true);
  project = signal<Project | null>(null);
  boards = signal<Board[]>([]);

  ngOnInit(): void {
    const id = this.route.snapshot.params['projectId'];
    this.projectService.get(id).subscribe({
      next: (p) => {
        this.project.set(p);
        this.loadBoards(id);
      },
      error: () => {
        this.loading.set(false);
        this.router.navigate(['/projects']);
      },
    });
  }

  private loadBoards(projectId: string): void {
    this.projectService.getBoards(projectId).subscribe({
      next: (boards) => {
        this.boards.set(boards);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  archiveProject(): void {
    const id = this.project()!.id;
    this.projectService.archive(id).subscribe({
      next: (p) => {
        this.project.set(p);
        this.toast.success(this.i18n.t('projects.archived'));
      },
    });
  }

  restoreProject(): void {
    const id = this.project()!.id;
    this.projectService.restore(id).subscribe({
      next: (p) => {
        this.project.set(p);
        this.toast.success(this.i18n.t('projects.restored'));
      },
    });
  }
}
