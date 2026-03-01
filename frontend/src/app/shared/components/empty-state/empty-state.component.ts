import { Component, inject, input } from '@angular/core';
import { TranslationService } from '@core/services/translation.service';

@Component({
  selector: 'app-empty-state',
  standalone: true,
  templateUrl: './empty-state.component.html',
  styleUrls: ['./empty-state.component.scss'],
})
export class EmptyStateComponent {
  private i18n = inject(TranslationService);

  icon = input('bi-inbox');
  title = input(this.i18n.t('emptyState.default'));
  subtitle = input('');
}
