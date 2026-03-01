import { Component, inject, input } from '@angular/core';
import { NgClass } from '@angular/common';
import { TranslationService } from '@core/services/translation.service';

@Component({
  selector: 'app-status-badge',
  standalone: true,
  imports: [NgClass],
  templateUrl: './status-badge.component.html',
  styleUrls: ['./status-badge.component.scss'],
})
export class StatusBadgeComponent {
  private i18n = inject(TranslationService);

  status = input<string>('todo');

  label = (): string => {
    const keyMap: Record<string, string> = {
      backlog: 'status.backlog',
      todo: 'status.todo',
      in_progress: 'status.inProgress',
      in_review: 'status.inReview',
      done: 'status.done',
      cancelled: 'status.cancelled',
    };
    return this.i18n.t(keyMap[this.status()] ?? this.status());
  };
}
