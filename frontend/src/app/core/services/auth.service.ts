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

  // Storage keys
  private readonly ACCESS_TOKEN_KEY = 'taskflow_access_token';
  private readonly USER_KEY = 'taskflow_user';

  // Access token stored in memory (signal) and localStorage for persistence
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
    // Load from localStorage first
    if (isPlatformBrowser(this.platformId)) {
      this.loadFromStorage();
      
      // Only attempt silent refresh if we have a token
      if (this._accessToken()) {
        this.silentRefresh().subscribe({
          next: (res) => {
            if (res) {
              // Successful refresh, start the refresh timer
              this.startRefreshTimer();
            }
            this._isLoading.set(false);
          },
          error: (error) => {
            // Only clear storage if token is actually invalid (401/403)
            if (error.status === 401 || error.status === 403) {
              this.clearStorage();
              this._accessToken.set(null);
              this._currentUser.set(null);
            }
            this._isLoading.set(false);
          },
        });
      } else {
        // No token in storage, just finish loading
        this._isLoading.set(false);
      }
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
          this.setToken(res.access);
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
          this.setToken(res.access);
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
    this.clearStorage();
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
          this.setToken(res.access);
          this.fetchProfile().subscribe();
        }),
        catchError((error) => {
          if (error.status === 401 || error.status === 403) {
            this._accessToken.set(null);
            this._currentUser.set(null);
            this.clearStorage();
          }
          return of(null);
        })
      );
  }

  fetchProfile(): Observable<User> {
    return this.http.get<User>(`${this.API}/auth/me/`).pipe(
      tap((user) => {
        this._currentUser.set(user);
        this.saveUserToStorage(user);
      })
    );
  }

  updateProfile(data: Partial<User>): Observable<User> {
    return this.http.patch<User>(`${this.API}/auth/me/`, data).pipe(
      tap((user) => {
        this._currentUser.set(user);
        this.saveUserToStorage(user);
      })
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
    // Refresh every 4 minutes (token expires in 15 minutes)
    this._refreshTimerSub = timer(environment.tokenRefreshInterval, environment.tokenRefreshInterval)
      .pipe(switchMap(() => this.silentRefresh()))
      .subscribe({
        next: (res) => {
          if (!res) {
            // Refresh failed, stop the timer
            this.stopRefreshTimer();
          }
        },
        error: () => {
          // On error, stop the timer
          this.stopRefreshTimer();
        }
      });
  }

  private stopRefreshTimer(): void {
    if (this._refreshTimerSub) {
      this._refreshTimerSub.unsubscribe();
      this._refreshTimerSub = null;
    }
  }

  // ── localStorage Management ───────────────────────────────────────────────

  private setToken(token: string): void {
    this._accessToken.set(token);
    if (isPlatformBrowser(this.platformId)) {
      localStorage.setItem(this.ACCESS_TOKEN_KEY, token);
    }
  }

  private saveUserToStorage(user: User): void {
    if (isPlatformBrowser(this.platformId)) {
      localStorage.setItem(this.USER_KEY, JSON.stringify(user));
    }
  }

  private loadFromStorage(): void {
    if (!isPlatformBrowser(this.platformId)) return;

    const token = localStorage.getItem(this.ACCESS_TOKEN_KEY);
    const userJson = localStorage.getItem(this.USER_KEY);

    if (token) {
      this._accessToken.set(token);
    }

    if (userJson) {
      try {
        const user = JSON.parse(userJson);
        this._currentUser.set(user);
      } catch (e) {
        console.warn('Failed to parse user from localStorage:', e);
        localStorage.removeItem(this.USER_KEY);
      }
    }
  }

  private clearStorage(): void {
    if (isPlatformBrowser(this.platformId)) {
      localStorage.removeItem(this.ACCESS_TOKEN_KEY);
      localStorage.removeItem(this.USER_KEY);
    }
  }
}
