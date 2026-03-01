import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '@env';
import { User, PaginatedResponse } from '@models/index';

@Injectable({ providedIn: 'root' })
export class UserManagementService {
  private http = inject(HttpClient);
  private readonly API = `${environment.apiUrl}/auth/users`;

  list(params?: any): Observable<PaginatedResponse<User>> {
    let httpParams = new HttpParams();
    if (params) {
      Object.keys(params).forEach((key) => {
        if (params[key] != null && params[key] !== '') {
          httpParams = httpParams.set(key, params[key]);
        }
      });
    }
    return this.http.get<PaginatedResponse<User>>(`${this.API}/`, {
      params: httpParams,
    });
  }

  get(id: string): Observable<User> {
    return this.http.get<User>(`${this.API}/${id}/`);
  }

  create(data: {
    email: string;
    first_name: string;
    last_name: string;
    password: string;
    role?: string;
    phone?: string;
    job_title?: string;
  }): Observable<User> {
    return this.http.post<User>(`${this.API}/`, data);
  }

  update(id: string, data: Partial<User>): Observable<User> {
    return this.http.patch<User>(`${this.API}/${id}/`, data);
  }

  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${this.API}/${id}/`);
  }
}
