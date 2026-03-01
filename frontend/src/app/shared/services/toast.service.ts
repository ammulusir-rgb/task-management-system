import { Injectable, signal } from '@angular/core';

export interface Toast {
  id: number;
  message: string;
  type: 'success' | 'error' | 'warning' | 'info';
  autoDismiss?: number;
}

@Injectable({ providedIn: 'root' })
export class ToastService {
  private _toasts = signal<Toast[]>([]);
  private _nextId = 0;

  readonly toasts = this._toasts.asReadonly();

  show(message: string, type: Toast['type'] = 'info', autoDismiss = 5000): void {
    const toast: Toast = { id: this._nextId++, message, type, autoDismiss };
    this._toasts.update((prev) => [...prev, toast]);

    if (autoDismiss > 0) {
      setTimeout(() => this.dismiss(toast.id), autoDismiss);
    }
  }

  success(message: string): void { this.show(message, 'success'); }
  error(message: string): void { this.show(message, 'error', 8000); }
  warning(message: string): void { this.show(message, 'warning'); }
  info(message: string): void { this.show(message, 'info'); }

  dismiss(id: number): void {
    this._toasts.update((prev) => prev.filter((t) => t.id !== id));
  }
}
