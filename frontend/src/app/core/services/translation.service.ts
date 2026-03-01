import { Injectable, signal, computed } from '@angular/core';
import {
  EN_TRANSLATIONS,
  ES_TRANSLATIONS,
  FR_TRANSLATIONS,
  SupportedLocale,
} from '@core/i18n/index';

const LOCALE_MAP: Record<SupportedLocale, Record<string, string>> = {
  en: EN_TRANSLATIONS,
  es: ES_TRANSLATIONS,
  fr: FR_TRANSLATIONS,
};

const STORAGE_KEY = 'app_locale';

@Injectable({ providedIn: 'root' })
export class TranslationService {
  /** Current active locale */
  private _locale = signal<SupportedLocale>(this.getInitialLocale());

  /** Public readonly signal of the active locale */
  readonly locale = this._locale.asReadonly();

  /** List of all supported locales */
  readonly supportedLocales: { code: SupportedLocale; label: string }[] = [
    { code: 'en', label: 'English' },
    { code: 'es', label: 'Español' },
    { code: 'fr', label: 'Français' },
  ];

  /** Active translations dictionary */
  private translations = computed(() => LOCALE_MAP[this._locale()] ?? EN_TRANSLATIONS);

  /**
   * Translate a key with optional interpolation params.
   * Usage: translate('dashboard.welcome', { name: 'Alice' })
   */
  translate(key: string, params?: Record<string, string | number>): string {
    let value = this.translations()[key] ?? EN_TRANSLATIONS[key] ?? key;

    if (params) {
      Object.entries(params).forEach(([paramKey, paramValue]) => {
        value = value.replace(new RegExp(`\\{${paramKey}\\}`, 'g'), String(paramValue));
      });
    }

    return value;
  }

  /** Shorthand alias */
  t(key: string, params?: Record<string, string | number>): string {
    return this.translate(key, params);
  }

  /** Switch active locale */
  setLocale(locale: SupportedLocale): void {
    this._locale.set(locale);
    try {
      localStorage.setItem(STORAGE_KEY, locale);
    } catch {
      // localStorage unavailable (SSR, etc.)
    }
    document.documentElement.lang = locale;
  }

  /** Change language (alias for setLocale) */
  changeLanguage(locale: SupportedLocale): void {
    this.setLocale(locale);
  }

  /** Get current locale code */
  getLocale(): SupportedLocale {
    return this._locale();
  }

  /**
   * Register additional translations at runtime.
   * Useful for lazy-loaded feature modules.
   */
  static registerTranslations(
    locale: SupportedLocale,
    translations: Record<string, string>
  ): void {
    const existing = LOCALE_MAP[locale];
    if (existing) {
      Object.assign(existing, translations);
    }
  }

  private getInitialLocale(): SupportedLocale {
    try {
      const stored = localStorage.getItem(STORAGE_KEY) as SupportedLocale | null;
      if (stored && stored in LOCALE_MAP) return stored;
    } catch {
      // noop
    }
    // Detect from browser
    const browserLang = navigator.language?.split('-')[0] as SupportedLocale;
    return browserLang in LOCALE_MAP ? browserLang : 'en';
  }
}
