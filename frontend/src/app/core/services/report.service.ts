import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '@env';
import {
  ProjectSummary,
  StatusDistribution,
  PriorityDistribution,
  AssigneeWorkload,
  BurndownPoint,
  VelocityPoint,
} from '@models/index';

@Injectable({ providedIn: 'root' })
export class ReportService {
  private http = inject(HttpClient);

  private apiUrl(projectId: string, action: string): string {
    return `${environment.apiUrl}/projects/${projectId}/reports/${action}/`;
  }

  getSummary(projectId: string): Observable<ProjectSummary> {
    return this.http.get<ProjectSummary>(this.apiUrl(projectId, 'summary'));
  }

  getTasksByStatus(projectId: string): Observable<StatusDistribution[]> {
    return this.http.get<StatusDistribution[]>(
      this.apiUrl(projectId, 'tasks-by-status')
    );
  }

  getTasksByPriority(projectId: string): Observable<PriorityDistribution[]> {
    return this.http.get<PriorityDistribution[]>(
      this.apiUrl(projectId, 'tasks-by-priority')
    );
  }

  getTasksByAssignee(projectId: string): Observable<AssigneeWorkload[]> {
    return this.http.get<AssigneeWorkload[]>(
      this.apiUrl(projectId, 'tasks-by-assignee')
    );
  }

  getBurndown(projectId: string, days = 30): Observable<BurndownPoint[]> {
    return this.http.get<BurndownPoint[]>(
      this.apiUrl(projectId, 'burndown'),
      { params: { days: days.toString() } }
    );
  }

  getVelocity(projectId: string, weeks = 12): Observable<VelocityPoint[]> {
    return this.http.get<VelocityPoint[]>(
      this.apiUrl(projectId, 'velocity'),
      { params: { weeks: weeks.toString() } }
    );
  }

  exportCsv(projectId: string): Observable<Blob> {
    return this.http.get(this.apiUrl(projectId, 'export-csv'), {
      responseType: 'blob',
    });
  }
}
