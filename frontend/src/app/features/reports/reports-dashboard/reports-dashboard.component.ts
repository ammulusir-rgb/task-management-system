import {
  Component,
  inject,
  OnInit,
  signal,
} from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { DecimalPipe } from '@angular/common';
import { NgxChartsModule } from '@swimlane/ngx-charts';
import { ReportService } from '@core/services/report.service';
import { TranslationService } from '@core/services/translation.service';
import {
  ProjectSummary,
  StatusDistribution,
  PriorityDistribution,
  AssigneeWorkload,
  BurndownPoint,
  VelocityPoint,
} from '@models/index';
import { LoadingSpinnerComponent } from '@shared/components/loading-spinner/loading-spinner.component';
import { TranslatePipe } from '@shared/pipes/translate.pipe';
import { ToastService } from '@shared/services/toast.service';

@Component({
  selector: 'app-reports-dashboard',
  standalone: true,
  imports: [
    RouterLink,
    DecimalPipe,
    NgxChartsModule,
    LoadingSpinnerComponent,
    TranslatePipe,
  ],
  templateUrl: './reports-dashboard.component.html',
  styleUrls: ['./reports-dashboard.component.scss'],
})
export class ReportsDashboardComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private reportService = inject(ReportService);
  private toast = inject(ToastService);
  private i18n = inject(TranslationService);

  loading = signal(true);
  summary = signal<ProjectSummary | null>(null);
  statusData = signal<{ name: string; value: number }[]>([]);
  priorityData = signal<{ name: string; value: number }[]>([]);
  burndownData = signal<{ name: string; series: { name: string; value: number }[] }[]>([]);
  velocityData = signal<{ name: string; value: number }[]>([]);
  assigneeData = signal<{ name: string; value: number }[]>([]);

  Math = Math;

  statusColorScheme: any = { domain: ['#6c757d', '#0d6efd', '#ffc107', '#17a2b8', '#198754'] };
  priorityColorScheme: any = { domain: ['#6c757d', '#0d6efd', '#ffc107', '#fd7e14', '#dc3545'] };
  lineColorScheme: any = { domain: ['#0d6efd', '#198754'] };
  assigneeColorScheme: any = { domain: ['#0d6efd', '#6610f2', '#6f42c1', '#d63384', '#fd7e14', '#20c997'] };

  private projectId = '';

  ngOnInit(): void {
    this.projectId = this.route.snapshot.params['projectId'];
    this.loadAllReports();
  }

  private loadAllReports(): void {
    // Summary
    this.reportService.getSummary(this.projectId).subscribe({
      next: (s) => {
        this.summary.set(s);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });

    // Status distribution
    this.reportService.getTasksByStatus(this.projectId).subscribe({
      next: (data) =>
        this.statusData.set(
          data.map((d: StatusDistribution) => ({ name: d.status, value: d.count }))
        ),
    });

    // Priority distribution
    this.reportService.getTasksByPriority(this.projectId).subscribe({
      next: (data) =>
        this.priorityData.set(
          data.map((d: PriorityDistribution) => ({ name: d.priority, value: d.count }))
        ),
    });

    // Burndown
    this.reportService.getBurndown(this.projectId).subscribe({
      next: (data) =>
        this.burndownData.set([
          {
            name: 'Remaining',
            series: data.map((d: BurndownPoint) => ({
              name: d.date,
              value: d.remaining,
            })),
          },
        ]),
    });

    // Velocity
    this.reportService.getVelocity(this.projectId).subscribe({
      next: (data) =>
        this.velocityData.set(
          data.map((d: VelocityPoint) => ({ name: d.week, value: d.completed }))
        ),
    });

    // Assignee workload
    this.reportService.getTasksByAssignee(this.projectId).subscribe({
      next: (data) =>
        this.assigneeData.set(
          data.map((d: AssigneeWorkload) => ({ name: `${d.assignee__first_name} ${d.assignee__last_name}`.trim() || d.assignee__email, value: d.total }))
        ),
    });
  }

  exportCsv(): void {
    this.reportService.exportCsv(this.projectId).subscribe({
      next: (blob) => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `project-${this.projectId}-tasks.csv`;
        a.click();
        URL.revokeObjectURL(url);
        this.toast.success(this.i18n.t('reports.exportDownloaded'));
      },
      error: () => this.toast.error(this.i18n.t('reports.exportFailed')),
    });
  }
}
