import { CanActivateFn, Router } from '@angular/router';
import { inject } from '@angular/core';
import { AuthService } from '@core/services/auth.service';
import { effect } from '@angular/core';

/**
 * Prevents access to protected routes when not authenticated.
 * Redirects to /auth/login.
 */
export const authGuard: CanActivateFn = () => {
  const authService = inject(AuthService);
  const router = inject(Router);

  // If authenticated, allow access
  if (authService.isAuthenticated()) {
    return true;
  }

  // If still loading (initial refresh in progress), wait for it to complete
  if (authService.isLoading()) {
    return new Promise<boolean>((resolve) => {
      const maxWaitTime = 5000; // 5 seconds max
      const startTime = Date.now();
      
      const checkAuth = () => {
        // Check if loading is done
        if (!authService.isLoading()) {
          if (authService.isAuthenticated()) {
            resolve(true);
          } else {
            router.navigate(['/auth/login']);
            resolve(false);
          }
          return;
        }
        
        // Check if timeout
        if (Date.now() - startTime > maxWaitTime) {
          router.navigate(['/auth/login']);
          resolve(false);
          return;
        }
        
        // Check again in 50ms
        setTimeout(checkAuth, 50);
      };
      
      checkAuth();
    });
  }

  // Not authenticated and not loading
  router.navigate(['/auth/login']);
  return false;
};
