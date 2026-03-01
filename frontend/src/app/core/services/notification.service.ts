import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { environment } from '@env';
import {
  Notification,
  PaginatedResponse,
} from '@models/index';

@Injectable({ providedIn: 'root' })
export class NotificationService {
  private http = inject(HttpClient);
  private readonly API = `${environment.apiUrl}/notifications`;

  list(page = 1): Observable<PaginatedResponse<Notification>> {
    return this.http.get<PaginatedResponse<Notification>>(`${this.API}/`, {
      params: { page: page.toString() },
    });
  }

  getUnreadCount(): Observable<{ unread_count: number }> {
    return this.http.get<{ count: number }>(
      `${this.API}/unread-count/`
    ).pipe(
      map(res => ({ unread_count: res.count }))
    );
  }

  markRead(id: string): Observable<Notification> {
    return this.http.post<Notification>(
      `${this.API}/${id}/mark-read/`,
      {}
    );
  }

  markAllRead(): Observable<any> {
    return this.http.post(`${this.API}/mark-all-read/`, {});
  }

  clearRead(): Observable<any> {
    return this.http.delete(`${this.API}/clear-read/`);
  }
}
