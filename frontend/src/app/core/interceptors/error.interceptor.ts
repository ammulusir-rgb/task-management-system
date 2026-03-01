import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, switchMap, throwError } from 'rxjs';
import { AuthService } from '@core/services/auth.service';

/**
 * Functional HTTP interceptor that handles error responses.
 * - 401: Attempts silent token refresh, then retries the request.
 * - 403/404/500: Maps to user-friendly handling.
 */
export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      if (error.status === 401 && !req.url.includes('/auth/')) {
        // Attempt silent refresh
        return authService.silentRefresh().pipe(
          switchMap((result) => {
            if (result?.access) {
              // Retry original request with new token
              const retryReq = req.clone({
                setHeaders: {
                  Authorization: `Bearer ${result.access}`,
                },
              });
              return next(retryReq);
            }
            authService.logout();
            return throwError(() => error);
          }),
          catchError(() => {
            authService.logout();
            return throwError(() => error);
          })
        );
      }

      if (error.status === 403) {
        console.error('Forbidden:', error.error);
      }

      if (error.status === 0) {
        console.error('Network error — API may be unreachable');
      }

      return throwError(() => error);
    })
  );
};
