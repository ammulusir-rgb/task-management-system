import {
  Component,
  inject,
  OnInit,
  OnDestroy,
  signal,
} from '@angular/core';
import { NotificationService } from '@core/services/notification.service';
import { WebSocketService } from '@core/services/websocket.service';
import { TranslationService } from '@core/services/translation.service';
import { Notification } from '@models/index';
import { LoadingSpinnerComponent } from '@shared/components/loading-spinner/loading-spinner.component';
import { EmptyStateComponent } from '@shared/components/empty-state/empty-state.component';
import { TranslatePipe } from '@shared/pipes/translate.pipe';
import { TimeAgoPipe } from '@shared/pipes/time-ago.pipe';
import { ToastService } from '@shared/services/toast.service';
import { NOTIFICATION_ICON_MAP } from './notification-list.types';

@Component({
  selector: 'app-notification-list',
  standalone: true,
  imports: [
    LoadingSpinnerComponent,
    EmptyStateComponent,
    TranslatePipe,
    TimeAgoPipe,
  ],
  templateUrl: './notification-list.component.html',
  styleUrls: ['./notification-list.component.scss'],
})
export class NotificationListComponent implements OnInit, OnDestroy {
  private notifService = inject(NotificationService);
  private wsService = inject(WebSocketService);
  private toast = inject(ToastService);
  private i18n = inject(TranslationService);

  loading = signal(true);
  notifications = signal<Notification[]>([]);
  unreadCount = signal(0);
  hasMore = signal(false);
  private page = 1;

  ngOnInit(): void {
    this.load();
    this.connectWebSocket();
  }

  ngOnDestroy(): void {
    this.wsService.disconnect('notifications');
  }

  private load(): void {
    this.notifService.list(this.page).subscribe({
      next: (res) => {
        if (this.page === 1) {
          this.notifications.set(res.results);
        } else {
          this.notifications.update((ns) => [...ns, ...res.results]);
        }
        this.hasMore.set(!!res.next);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
    this.notifService.getUnreadCount().subscribe({
      next: (res) => this.unreadCount.set(res.unread_count),
    });
  }

  loadMore(): void {
    this.page++;
    this.load();
  }

  markRead(notif: Notification): void {
    if (notif.is_read) return;
    this.notifService.markRead(notif.id).subscribe({
      next: () => {
        this.notifications.update((ns) =>
          ns.map((n) =>
            n.id === notif.id ? { ...n, is_read: true } : n
          )
        );
        this.unreadCount.update((c) => Math.max(0, c - 1));
      },
    });
  }

  markAllRead(): void {
    this.notifService.markAllRead().subscribe({
      next: () => {
        this.notifications.update((ns) =>
          ns.map((n) => ({ ...n, is_read: true }))
        );
        this.unreadCount.set(0);
        this.toast.success(this.i18n.t('notifications.allMarkedRead'));
      },
    });
  }

  clearRead(): void {
    this.notifService.clearRead().subscribe({
      next: () => {
        this.notifications.update((ns) => ns.filter((n) => !n.is_read));
        this.toast.success(this.i18n.t('notifications.readCleared'));
      },
    });
  }

  getIcon(type: string): string {
    return NOTIFICATION_ICON_MAP[type] ?? 'bi-bell text-muted';
  }

  private connectWebSocket(): void {
    const ws = this.wsService.connect('notifications', 'notifications/');
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'notification') {
        this.notifications.update((ns) => [data.notification, ...ns]);
        this.unreadCount.update((c) => c + 1);
      }
    };
  }
}
