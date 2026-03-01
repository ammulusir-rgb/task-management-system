import { Pipe, PipeTransform } from '@angular/core';

/**
 * Truncates a string to a max length with ellipsis.
 */
@Pipe({ name: 'truncate', standalone: true })
export class TruncatePipe implements PipeTransform {
  transform(value: string, maxLength = 100): string {
    if (!value || value.length <= maxLength) return value;
    return value.substring(0, maxLength) + '...';
  }
}
