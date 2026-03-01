import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
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
    return this.http.get<{ unread_count: number }>(
      `${this.API}/unread_count/`
    );
  }

  markRead(id: string): Observable<Notification> {
    return this.http.post<Notification>(
      `${this.API}/${id}/mark_read/`,
      {}
    );
  }

  markAllRead(): Observable<any> {
    return this.http.post(`${this.API}/mark_all_read/`, {});
  }

  clearRead(): Observable<any> {
    return this.http.post(`${this.API}/clear_read/`, {});
  }
}
