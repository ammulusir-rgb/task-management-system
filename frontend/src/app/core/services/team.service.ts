import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '@env';
import { PaginatedResponse, User } from '@models/index';

export interface Team {
  id: string;
  organization: string;
  name: string;
  description: string;
  created_by: string;
  member_count: number;
  created_at: string;
  updated_at: string;
}

export interface TeamMember {
  id: string;
  team: string;
  user: Pick<User, 'id' | 'email' | 'first_name' | 'last_name' | 'avatar' | 'role'>;
  is_lead: boolean;
  created_at: string;
}

@Injectable({ providedIn: 'root' })
export class TeamService {
  private http = inject(HttpClient);
  private readonly API = `${environment.apiUrl}/organizations/teams`;

  list(params?: any): Observable<PaginatedResponse<Team>> {
    let httpParams = new HttpParams();
    if (params) {
      Object.keys(params).forEach((key) => {
        if (params[key] != null && params[key] !== '') {
          httpParams = httpParams.set(key, params[key]);
        }
      });
    }
    return this.http.get<PaginatedResponse<Team>>(`${this.API}/`, {
      params: httpParams,
    });
  }

  get(id: string): Observable<Team> {
    return this.http.get<Team>(`${this.API}/${id}/`);
  }

  create(data: Partial<Team>): Observable<Team> {
    return this.http.post<Team>(`${this.API}/`, data);
  }

  update(id: string, data: Partial<Team>): Observable<Team> {
    return this.http.patch<Team>(`${this.API}/${id}/`, data);
  }

  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${this.API}/${id}/`);
  }

  getMembers(teamId: string): Observable<TeamMember[]> {
    return this.http.get<TeamMember[]>(`${this.API}/${teamId}/members/`);
  }

  addMember(
    teamId: string,
    data: { user_id: string; is_lead?: boolean }
  ): Observable<TeamMember> {
    return this.http.post<TeamMember>(
      `${this.API}/${teamId}/members/add/`,
      data
    );
  }

  removeMember(teamId: string, memberId: string): Observable<void> {
    return this.http.delete<void>(
      `${this.API}/${teamId}/members/${memberId}/`
    );
  }
}
