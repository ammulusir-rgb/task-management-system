import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '@env';
import {
  Task,
  TaskListItem,
  TaskMoveRequest,
  Comment,
  Attachment,
  ActivityLog,
  PaginatedResponse,
} from '@models/index';

@Injectable({ providedIn: 'root' })
export class TaskService {
  private http = inject(HttpClient);
  private readonly API = `${environment.apiUrl}/tasks`;

  list(params?: any): Observable<PaginatedResponse<TaskListItem>> {
    let httpParams = new HttpParams();
    if (params) {
      Object.keys(params).forEach((key) => {
        if (params[key] != null && params[key] !== '') {
          httpParams = httpParams.set(key, params[key]);
        }
      });
    }
    return this.http.get<PaginatedResponse<TaskListItem>>(`${this.API}/`, {
      params: httpParams,
    });
  }

  get(id: string): Observable<Task> {
    return this.http.get<Task>(`${this.API}/${id}/`);
  }

  create(data: Partial<Task>): Observable<Task> {
    return this.http.post<Task>(`${this.API}/`, data);
  }

  update(id: string, data: Partial<Task>): Observable<Task> {
    return this.http.patch<Task>(`${this.API}/${id}/`, data);
  }

  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${this.API}/${id}/`);
  }

  move(id: string, data: TaskMoveRequest): Observable<Task> {
    return this.http.post<Task>(`${this.API}/${id}/move/`, data);
  }

  bulkMove(
    taskIds: string[],
    columnId: string
  ): Observable<{ moved_count: number }> {
    return this.http.post<{ moved_count: number }>(
      `${this.API}/bulk_move/`,
      { task_ids: taskIds, column_id: columnId }
    );
  }

  // ----- Comments -----
  getComments(
    taskId: string,
    page = 1
  ): Observable<PaginatedResponse<Comment>> {
    return this.http.get<PaginatedResponse<Comment>>(
      `${this.API}/${taskId}/comments/`,
      { params: { page: page.toString() } }
    );
  }

  addComment(taskId: string, content: string, parentId?: string): Observable<Comment> {
    const body: any = { content };
    if (parentId) body.parent = parentId;
    return this.http.post<Comment>(`${this.API}/${taskId}/comments/`, body);
  }

  // ----- Attachments -----
  getAttachments(taskId: string): Observable<Attachment[]> {
    return this.http.get<Attachment[]>(
      `${this.API}/${taskId}/attachments/`
    );
  }

  uploadAttachment(taskId: string, file: File): Observable<Attachment> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<Attachment>(
      `${this.API}/${taskId}/attachments/`,
      formData
    );
  }

  // ----- Activity -----
  getActivity(taskId: string): Observable<PaginatedResponse<ActivityLog>> {
    return this.http.get<PaginatedResponse<ActivityLog>>(
      `${this.API}/${taskId}/activity/`
    );
  }
}
