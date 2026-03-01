import {
  Injectable,
  signal,
  computed,
  inject,
  PLATFORM_ID,
} from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, tap, catchError, of, BehaviorSubject, switchMap, timer } from 'rxjs';
import { environment } from '@env';
import {
  AuthResponse,
  LoginRequest,
  RegisterRequest,
  TokenRefreshResponse,
  User,
} from '@models/index';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private http = inject(HttpClient);
  private router = inject(Router);
  private platformId = inject(PLATFORM_ID);

  // Access token stored in memory (signal) — never in localStorage
  private _accessToken = signal<string | null>(null);
  private _currentUser = signal<User | null>(null);
  private _isLoading = signal(true);
  private _refreshTimerSub: any = null;

  // Public read-only signals
  readonly accessToken = this._accessToken.asReadonly();
  readonly currentUser = this._currentUser.asReadonly();
  readonly isLoading = this._isLoading.asReadonly();
  readonly isAuthenticated = computed(() => !!this._accessToken());

  private readonly API = environment.apiUrl;

  constructor() {
    // Attempt silent refresh on app init
    if (isPlatformBrowser(this.platformId)) {
      this.silentRefresh().subscribe({
        next: () => this._isLoading.set(false),
        error: () => this._isLoading.set(false),
      });
    } else {
      this._isLoading.set(false);
    }
  }

  login(credentials: LoginRequest): Observable<AuthResponse> {
    return this.http
      .post<AuthResponse>(`${this.API}/auth/token/`, credentials, {
        withCredentials: true,
      })
      .pipe(
        tap((res) => {
          this._accessToken.set(res.access);
          this.fetchProfile().subscribe();
          this.startRefreshTimer();
        })
      );
  }

  register(data: RegisterRequest): Observable<AuthResponse> {
    return this.http
      .post<AuthResponse>(`${this.API}/auth/register/`, data, {
        withCredentials: true,
      })
      .pipe(
        tap((res) => {
          this._accessToken.set(res.access);
          this.fetchProfile().subscribe();
          this.startRefreshTimer();
        })
      );
  }

  logout(): void {
    this.http
      .post(`${this.API}/auth/logout/`, {}, { withCredentials: true })
      .subscribe({ error: () => {} });

    this._accessToken.set(null);
    this._currentUser.set(null);
    this.stopRefreshTimer();
    this.router.navigate(['/auth/login']);
  }

  silentRefresh(): Observable<TokenRefreshResponse | null> {
    return this.http
      .post<TokenRefreshResponse>(
        `${this.API}/auth/token/refresh/`,
        {},
        { withCredentials: true }
      )
      .pipe(
        tap((res) => {
          this._accessToken.set(res.access);
          this.fetchProfile().subscribe();
          this.startRefreshTimer();
        }),
        catchError(() => {
          this._accessToken.set(null);
          this._currentUser.set(null);
          return of(null);
        })
      );
  }

  fetchProfile(): Observable<User> {
    return this.http.get<User>(`${this.API}/auth/me/`).pipe(
      tap((user) => this._currentUser.set(user))
    );
  }

  updateProfile(data: Partial<User>): Observable<User> {
    return this.http.patch<User>(`${this.API}/auth/me/`, data).pipe(
      tap((user) => this._currentUser.set(user))
    );
  }

  changePassword(data: {
    old_password: string;
    new_password: string;
    new_password_confirm: string;
  }): Observable<any> {
    return this.http.post(`${this.API}/auth/me/change-password/`, data);
  }

  getToken(): string | null {
    return this._accessToken();
  }

  private startRefreshTimer(): void {
    this.stopRefreshTimer();
    // Refresh 1 minute before the 15-minute access token expires
    this._refreshTimerSub = timer(environment.tokenRefreshInterval)
      .pipe(switchMap(() => this.silentRefresh()))
      .subscribe();
  }

  private stopRefreshTimer(): void {
    if (this._refreshTimerSub) {
      this._refreshTimerSub.unsubscribe();
      this._refreshTimerSub = null;
    }
  }
}
