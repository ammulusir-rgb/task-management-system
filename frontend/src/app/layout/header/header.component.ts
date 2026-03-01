import { Component, inject, output, OnInit, OnDestroy, signal, HostListener } from '@angular/core';
import { RouterLink } from '@angular/router';
import { AuthService } from '@core/services/auth.service';
import { NotificationService } from '@core/services/notification.service';
import { TranslationService } from '@core/services/translation.service';
import { ThemeService } from '@core/services/theme.service';
import { SupportedLocale } from '@core/i18n';
import { UserAvatarComponent } from '@shared/components/user-avatar/user-avatar.component';

const LANGUAGE_LABELS: Record<SupportedLocale, { flag: string; name: string }> = {
  en: { flag: '🇺🇸', name: 'English' },
  es: { flag: '🇪🇸', name: 'Español' },
  fr: { flag: '🇫🇷', name: 'Français' },
};

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [RouterLink, UserAvatarComponent],
  templateUrl: './header.component.html',
  styleUrls: ['./header.component.scss'],
})
export class HeaderComponent implements OnInit, OnDestroy {
  authService = inject(AuthService);
  i18n = inject(TranslationService);
  themeService = inject(ThemeService);
  private notificationService = inject(NotificationService);

  toggleSidebar = output<void>();

  currentUser = this.authService.currentUser;
  unreadCount = signal(0);
  languageLabels = LANGUAGE_LABELS;
  supportedLocales = this.i18n.supportedLocales;

  langDropdownOpen = signal(false);
  userDropdownOpen = signal(false);

  private pollInterval: ReturnType<typeof setInterval> | null = null;

  ngOnInit(): void {
    this.fetchUnread();
    this.pollInterval = setInterval(() => this.fetchUnread(), 30_000);
  }

  ngOnDestroy(): void {
    if (this.pollInterval) clearInterval(this.pollInterval);
  }

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: MouseEvent): void {
    // Close dropdowns when clicking outside
    const target = event.target as HTMLElement;
    if (!target.closest('.dropdown')) {
      this.closeDropdowns();
    }
  }

  toggleLangDropdown(event: Event): void {
    event.stopPropagation();
    const wasOpen = this.langDropdownOpen();
    this.closeDropdowns();
    this.langDropdownOpen.set(!wasOpen);
  }

  toggleUserDropdown(event: Event): void {
    event.stopPropagation();
    const wasOpen = this.userDropdownOpen();
    this.closeDropdowns();
    this.userDropdownOpen.set(!wasOpen);
  }

  closeDropdowns(): void {
    this.langDropdownOpen.set(false);
    this.userDropdownOpen.set(false);
  }

  switchLanguage(locale: SupportedLocale): void {
    this.i18n.setLocale(locale);
    this.closeDropdowns();
  }

  private fetchUnread(): void {
    this.notificationService.getUnreadCount().subscribe({
      next: (res) => this.unreadCount.set(res.unread_count),
    });
  }
}
