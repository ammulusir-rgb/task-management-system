import { Injectable, inject, signal } from '@angular/core';
import { environment } from '@env';
import { AuthService } from './auth.service';

export interface WsMessage {
  type: string;
  [key: string]: any;
}

@Injectable({ providedIn: 'root' })
export class WebSocketService {
  private authService = inject(AuthService);
  private connections = new Map<string, WebSocket>();

  readonly connectionStatus = signal<Record<string, 'connecting' | 'open' | 'closed' | 'error'>>({});

  connect(channel: string, path: string): WebSocket {
    if (this.connections.has(channel)) {
      const existing = this.connections.get(channel)!;
      if (existing.readyState === WebSocket.OPEN || existing.readyState === WebSocket.CONNECTING) {
        return existing;
      }
    }

    const token = this.authService.getToken();
    const url = `${environment.wsUrl}/${path}?token=${token}`;
    const ws = new WebSocket(url);

    this.updateStatus(channel, 'connecting');

    ws.onopen = () => this.updateStatus(channel, 'open');
    ws.onclose = () => {
      this.updateStatus(channel, 'closed');
      this.connections.delete(channel);
    };
    ws.onerror = () => this.updateStatus(channel, 'error');

    this.connections.set(channel, ws);
    return ws;
  }

  disconnect(channel: string): void {
    const ws = this.connections.get(channel);
    if (ws) {
      ws.close();
      this.connections.delete(channel);
    }
  }

  disconnectAll(): void {
    this.connections.forEach((ws) => ws.close());
    this.connections.clear();
  }

  send(channel: string, message: WsMessage): void {
    const ws = this.connections.get(channel);
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(message));
    }
  }

  private updateStatus(channel: string, status: 'connecting' | 'open' | 'closed' | 'error'): void {
    this.connectionStatus.update((prev) => ({ ...prev, [channel]: status }));
  }
}
