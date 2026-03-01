import { Component, inject, input, output } from '@angular/core';
import { TranslationService } from '@core/services/translation.service';

@Component({
  selector: 'app-confirm-dialog',
  standalone: true,
  templateUrl: './confirm-dialog.component.html',
  styleUrls: ['./confirm-dialog.component.scss'],
})
export class ConfirmDialogComponent {
  private i18n = inject(TranslationService);

  title = input(this.i18n.t('confirm.title'));
  message = input(this.i18n.t('confirm.message'));
  confirmText = input(this.i18n.t('confirm.confirm'));
  cancelText = input(this.i18n.t('confirm.cancel'));
  confirmClass = input('btn-danger');

  confirmed = output<void>();
  cancelled = output<void>();
}
