import { CanActivateFn, Router } from '@angular/router';
import { inject } from '@angular/core';
import { AuthService } from '@core/services/auth.service';

/**
 * Prevents already-authenticated users from seeing login/register pages.
 * Redirects to /dashboard. Waits for auth loading to complete.
 */
export const guestGuard: CanActivateFn = () => {
  const authService = inject(AuthService);
  const router = inject(Router);

  return new Promise<boolean>((resolve) => {
    // If not loading, decide immediately
    if (!authService.isLoading()) {
      if (authService.isAuthenticated()) {
        router.navigate(['/dashboard']);
        resolve(false);
      } else {
        resolve(true);
      }
      return;
    }

    // Wait for auth loading to finish
    const interval = setInterval(() => {
      if (!authService.isLoading()) {
        clearInterval(interval);
        clearTimeout(timeout);
        if (authService.isAuthenticated()) {
          router.navigate(['/dashboard']);
          resolve(false);
        } else {
          resolve(true);
        }
      }
    }, 50);

    const timeout = setTimeout(() => {
      clearInterval(interval);
      resolve(true); // Allow access on timeout
    }, 5000);
  });
};
