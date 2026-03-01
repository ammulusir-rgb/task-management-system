import { Injectable, signal, computed } from '@angular/core';

export type ThemeMode = 'light' | 'dark' | 'auto';

const STORAGE_KEY = 'app-theme';

@Injectable({ providedIn: 'root' })
export class ThemeService {
  private _mode = signal<ThemeMode>(this.getInitialMode());

  /** Current theme mode setting */
  readonly mode = this._mode.asReadonly();

  /** Whether dark theme is actually active (resolved from 'auto') */
  readonly isDark = computed(() => {
    const m = this._mode();
    if (m === 'auto') {
      return window.matchMedia('(prefers-color-scheme: dark)').matches;
    }
    return m === 'dark';
  });

  constructor() {
    this.applyTheme();

    // Listen for system preference changes when in 'auto' mode
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
      if (this._mode() === 'auto') {
        this.applyTheme();
      }
    });
  }

  /** Set the theme mode and persist it */
  setMode(mode: ThemeMode): void {
    this._mode.set(mode);
    try {
      localStorage.setItem(STORAGE_KEY, mode);
    } catch {
      // localStorage unavailable
    }
    this.applyTheme();
  }

  /** Cycle through light → dark → auto */
  toggle(): void {
    const current = this._mode();
    const next: ThemeMode = current === 'light' ? 'dark' : current === 'dark' ? 'auto' : 'light';
    this.setMode(next);
  }

  /** Apply the resolved theme class to <body> */
  private applyTheme(): void {
    const body = document.body;
    body.classList.remove('theme-light', 'theme-dark');

    const m = this._mode();
    if (m === 'auto') {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      body.classList.add(prefersDark ? 'theme-dark' : 'theme-light');
    } else {
      body.classList.add(`theme-${m}`);
    }
  }

  private getInitialMode(): ThemeMode {
    try {
      const stored = localStorage.getItem(STORAGE_KEY) as ThemeMode | null;
      if (stored && ['light', 'dark', 'auto'].includes(stored)) {
        return stored;
      }
    } catch {
      // localStorage unavailable
    }
    return 'light';
  }
}
