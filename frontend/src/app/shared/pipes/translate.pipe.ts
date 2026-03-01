import { Pipe, PipeTransform, inject } from '@angular/core';
import { TranslationService } from '@core/services/translation.service';

/**
 * Translate pipe for templates.
 * Usage: {{ 'auth.signIn' | translate }}
 * With params: {{ 'dashboard.welcome' | translate:{ name: user.first_name } }}
 */
@Pipe({ name: 'translate', standalone: true, pure: false })
export class TranslatePipe implements PipeTransform {
  private i18n = inject(TranslationService);

  transform(key: string, params?: Record<string, string | number>): string {
    return this.i18n.translate(key, params);
  }
}
