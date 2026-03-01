import { Component, inject, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AuthService } from '@core/services/auth.service';
import { TranslationService } from '@core/services/translation.service';
import { User } from '@models/index';
import { UserAvatarComponent } from '@shared/components/user-avatar/user-avatar.component';
import { TranslatePipe } from '@shared/pipes/translate.pipe';

@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [FormsModule, UserAvatarComponent, TranslatePipe],
  templateUrl: './profile.component.html',
  styleUrls: ['./profile.component.scss'],
})
export class ProfileComponent implements OnInit {
  private authService = inject(AuthService);
  i18n = inject(TranslationService);

  user = this.authService.currentUser;
  saving = signal(false);
  saved = signal(false);
  error = signal('');

  // Form fields
  firstName = signal('');
  lastName = signal('');
  phone = signal('');
  jobTitle = signal('');

  // Password change
  changingPassword = signal(false);
  oldPassword = signal('');
  newPassword = signal('');
  confirmPassword = signal('');
  passwordError = signal('');
  passwordSuccess = signal(false);

  // Preferences
  selectedTheme = signal<'light' | 'dark' | 'auto'>('light');
  selectedLanguage = signal<'en' | 'es' | 'fr'>('en');
  emailNotifications = signal(true);
  savingPreferences = signal(false);
  preferencesSuccess = signal(false);
  preferencesError = signal('');

  ngOnInit(): void {
    const u = this.user();
    if (u) {
      this.firstName.set(u.first_name);
      this.lastName.set(u.last_name);
      this.phone.set(u.phone || '');
      this.jobTitle.set(u.job_title || '');
    }
    
    // Load preferences from localStorage
    this.loadPreferences();
  }

  saveProfile(): void {
    this.saving.set(true);
    this.saved.set(false);
    this.error.set('');

    this.authService
      .updateProfile({
        first_name: this.firstName(),
        last_name: this.lastName(),
        phone: this.phone(),
        job_title: this.jobTitle(),
      })
      .subscribe({
        next: () => {
          this.saving.set(false);
          this.saved.set(true);
          setTimeout(() => this.saved.set(false), 3000);
        },
        error: () => {
          this.saving.set(false);
          this.error.set(this.i18n.t('profile.saveFailed'));
        },
      });
  }

  changePassword(): void {
    this.passwordError.set('');
    this.passwordSuccess.set(false);

    if (this.newPassword() !== this.confirmPassword()) {
      this.passwordError.set(this.i18n.t('profile.passwordMismatch'));
      return;
    }
    if (this.newPassword().length < 8) {
      this.passwordError.set(this.i18n.t('profile.passwordMinLength'));
      return;
    }

    this.changingPassword.set(true);

    this.authService
      .changePassword({
        old_password: this.oldPassword(),
        new_password: this.newPassword(),
        new_password_confirm: this.confirmPassword(),
      })
      .subscribe({
        next: () => {
          this.changingPassword.set(false);
          this.passwordSuccess.set(true);
          this.oldPassword.set('');
          this.newPassword.set('');
          this.confirmPassword.set('');
          setTimeout(() => this.passwordSuccess.set(false), 3000);
        },
        error: (err) => {
          this.changingPassword.set(false);
          const msg =
            err?.error?.error?.message ||
            err?.error?.old_password?.[0] ||
            this.i18n.t('profile.passwordChangeFailed');
          this.passwordError.set(msg);
        },
      });
  }

  // Preferences Methods
  loadPreferences(): void {
    const theme = localStorage.getItem('app-theme') as 'light' | 'dark' | 'auto' || 'light';
    const language = localStorage.getItem('app-language') as 'en' | 'es' | 'fr' || 'en';
    const notifications = localStorage.getItem('email-notifications') !== 'false';

    this.selectedTheme.set(theme);
    this.selectedLanguage.set(language);
    this.emailNotifications.set(notifications);

    // Apply theme
    this.applyTheme(theme);
    
    // Set language
    this.i18n.changeLanguage(language);
  }

  onThemeChange(theme: 'light' | 'dark' | 'auto'): void {
    this.selectedTheme.set(theme);
    this.applyTheme(theme);
  }

  onLanguageChange(language: 'en' | 'es' | 'fr'): void {
    this.selectedLanguage.set(language);
    this.i18n.changeLanguage(language);
  }

  applyTheme(theme: 'light' | 'dark' | 'auto'): void {
    const body = document.body;
    
    // Remove existing theme classes
    body.classList.remove('theme-light', 'theme-dark');
    
    if (theme === 'auto') {
      // Use system preference
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      body.classList.add(prefersDark ? 'theme-dark' : 'theme-light');
    } else {
      body.classList.add(`theme-${theme}`);
    }
  }

  savePreferences(): void {
    this.savingPreferences.set(true);
    this.preferencesSuccess.set(false);
    this.preferencesError.set('');

    try {
      // Save to localStorage
      localStorage.setItem('app-theme', this.selectedTheme());
      localStorage.setItem('app-language', this.selectedLanguage());
      localStorage.setItem('email-notifications', String(this.emailNotifications()));

      // Apply changes immediately
      this.applyTheme(this.selectedTheme());
      this.i18n.changeLanguage(this.selectedLanguage());

      setTimeout(() => {
        this.savingPreferences.set(false);
        this.preferencesSuccess.set(true);
        setTimeout(() => this.preferencesSuccess.set(false), 3000);
      }, 500);
    } catch (error) {
      this.savingPreferences.set(false);
      this.preferencesError.set(this.i18n.t('profile.preferencesError'));
    }
  }
}
