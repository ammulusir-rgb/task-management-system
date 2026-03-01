import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '@env';
import {
  Organization,
  OrganizationMember,
  PaginatedResponse,
} from '@models/index';

@Injectable({ providedIn: 'root' })
export class OrganizationService {
  private http = inject(HttpClient);
  private readonly API = `${environment.apiUrl}/organizations`;

  list(params?: any): Observable<PaginatedResponse<Organization>> {
    let httpParams = new HttpParams();
    if (params) {
      Object.keys(params).forEach((key) => {
        if (params[key] !== null && params[key] !== undefined) {
          httpParams = httpParams.set(key, params[key]);
        }
      });
    }
    return this.http.get<PaginatedResponse<Organization>>(`${this.API}/`, {
      params: httpParams,
    });
  }

  get(id: string): Observable<Organization> {
    return this.http.get<Organization>(`${this.API}/${id}/`);
  }

  create(data: Partial<Organization>): Observable<Organization> {
    return this.http.post<Organization>(`${this.API}/`, data);
  }

  update(id: string, data: Partial<Organization>): Observable<Organization> {
    return this.http.patch<Organization>(`${this.API}/${id}/`, data);
  }

  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${this.API}/${id}/`);
  }

  getMembers(orgId: string): Observable<OrganizationMember[]> {
    return this.http.get<OrganizationMember[]>(
      `${this.API}/${orgId}/members/`
    );
  }

  addMember(
    orgId: string,
    data: { email?: string; user_id?: string; role?: string }
  ): Observable<OrganizationMember> {
    return this.http.post<OrganizationMember>(
      `${this.API}/${orgId}/members/add/`,
      data
    );
  }

  updateMember(
    orgId: string,
    memberId: string,
    data: { role: string }
  ): Observable<OrganizationMember> {
    return this.http.patch<OrganizationMember>(
      `${this.API}/${orgId}/members/${memberId}/role/`,
      data
    );
  }

  removeMember(orgId: string, memberId: string): Observable<void> {
    return this.http.delete<void>(
      `${this.API}/${orgId}/members/${memberId}/`
    );
  }
}
