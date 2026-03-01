import { CanActivateFn, Router } from '@angular/router';
import { inject } from '@angular/core';
import { AuthService } from '@core/services/auth.service';

/**
 * Prevents access to protected routes when not authenticated.
 * Redirects to /auth/login.
 */
export const authGuard: CanActivateFn = () => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (authService.isAuthenticated()) {
    return true;
  }

  // If still loading (initial refresh in progress), wait
  if (authService.isLoading()) {
    // Return a promise that resolves once loading finishes
    return new Promise<boolean>((resolve) => {
      const check = setInterval(() => {
        if (!authService.isLoading()) {
          clearInterval(check);
          if (authService.isAuthenticated()) {
            resolve(true);
          } else {
            router.navigate(['/auth/login']);
            resolve(false);
          }
        }
      }, 50);

      // Timeout after 5s
      setTimeout(() => {
        clearInterval(check);
        if (!authService.isAuthenticated()) {
          router.navigate(['/auth/login']);
          resolve(false);
        }
      }, 5000);
    });
  }

  router.navigate(['/auth/login']);
  return false;
};
