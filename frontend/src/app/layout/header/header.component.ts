import { Component, inject, output, OnInit, OnDestroy, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { AuthService } from '@core/services/auth.service';
import { NotificationService } from '@core/services/notification.service';
import { TranslationService } from '@core/services/translation.service';
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
  private notificationService = inject(NotificationService);

  toggleSidebar = output<void>();

  currentUser = this.authService.currentUser;
  unreadCount = signal(0);
  languageLabels = LANGUAGE_LABELS;
  supportedLocales = this.i18n.supportedLocales;

  private pollInterval: ReturnType<typeof setInterval> | null = null;

  ngOnInit(): void {
    this.fetchUnread();
    this.pollInterval = setInterval(() => this.fetchUnread(), 30_000);
  }

  ngOnDestroy(): void {
    if (this.pollInterval) clearInterval(this.pollInterval);
  }

  switchLanguage(locale: SupportedLocale): void {
    this.i18n.setLocale(locale);
  }

  private fetchUnread(): void {
    this.notificationService.getUnreadCount().subscribe({
      next: (res) => this.unreadCount.set(res.unread_count),
    });
  }
}
