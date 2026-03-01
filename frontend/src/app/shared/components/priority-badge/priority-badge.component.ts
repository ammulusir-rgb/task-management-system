import { Component, inject, input } from '@angular/core';
import { NgClass } from '@angular/common';
import { TranslationService } from '@core/services/translation.service';
import { PriorityLevel, PRIORITY_ICON_MAP } from './priority-badge.types';

@Component({
  selector: 'app-priority-badge',
  standalone: true,
  imports: [NgClass],
  templateUrl: './priority-badge.component.html',
  styleUrls: ['./priority-badge.component.scss'],
})
export class PriorityBadgeComponent {
  private i18n = inject(TranslationService);

  priority = input<string>('none');

  label = (): string => {
    return this.i18n.t(`priority.${this.priority()}`);
  };

  iconClass = (): string => {
    return PRIORITY_ICON_MAP[this.priority() as PriorityLevel] ?? 'bi-three-dots';
  };
}
