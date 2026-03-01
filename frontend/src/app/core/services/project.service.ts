import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '@env';
import {
  Project,
  ProjectMember,
  Board,
  Column,
  PaginatedResponse,
} from '@models/index';

@Injectable({ providedIn: 'root' })
export class ProjectService {
  private http = inject(HttpClient);
  private readonly API = `${environment.apiUrl}/projects`;

  list(params?: any): Observable<PaginatedResponse<Project>> {
    let httpParams = new HttpParams();
    if (params) {
      Object.keys(params).forEach((key) => {
        if (params[key] != null) {
          httpParams = httpParams.set(key, params[key]);
        }
      });
    }
    return this.http.get<PaginatedResponse<Project>>(`${this.API}/`, {
      params: httpParams,
    });
  }

  get(id: string): Observable<Project> {
    return this.http.get<Project>(`${this.API}/${id}/`);
  }

  create(data: Partial<Project>): Observable<Project> {
    return this.http.post<Project>(`${this.API}/`, data);
  }

  update(id: string, data: Partial<Project>): Observable<Project> {
    return this.http.patch<Project>(`${this.API}/${id}/`, data);
  }

  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${this.API}/${id}/`);
  }

  archive(id: string): Observable<Project> {
    return this.http.post<Project>(`${this.API}/${id}/archive/`, {});
  }

  restore(id: string): Observable<Project> {
    return this.http.post<Project>(`${this.API}/${id}/restore/`, {});
  }

  // ----- Members -----
  getMembers(projectId: string): Observable<ProjectMember[]> {
    return this.http.get<ProjectMember[]>(`${this.API}/${projectId}/members/`);
  }

  // ----- Boards -----
  getBoards(projectId: string): Observable<Board[]> {
    return this.http.get<Board[]>(
      `${this.API}/boards/?project=${projectId}`
    );
  }

  getBoard(boardId: string): Observable<Board> {
    return this.http.get<Board>(`${this.API}/boards/${boardId}/`);
  }

  // ----- Columns -----
  createColumn(data: Partial<Column>): Observable<Column> {
    return this.http.post<Column>(`${this.API}/columns/`, data);
  }

  updateColumn(id: string, data: Partial<Column>): Observable<Column> {
    return this.http.patch<Column>(`${this.API}/columns/${id}/`, data);
  }

  deleteColumn(id: string): Observable<void> {
    return this.http.delete<void>(`${this.API}/columns/${id}/`);
  }

  reorderColumns(columnIds: string[]): Observable<any> {
    return this.http.post(`${this.API}/columns/reorder/`, {
      column_ids: columnIds,
    });
  }
}
