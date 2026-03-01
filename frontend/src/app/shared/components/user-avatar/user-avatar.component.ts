import { Component, input, computed } from '@angular/core';
import { AvatarSize, AVATAR_SIZE_MAP, AVATAR_COLORS } from './user-avatar.types';

@Component({
  selector: 'app-user-avatar',
  standalone: true,
  templateUrl: './user-avatar.component.html',
  styleUrls: ['./user-avatar.component.scss'],
})
export class UserAvatarComponent {
  name = input('');
  avatarUrl = input<string | null>(null);
  size = input<AvatarSize>('md');

  sizePx = computed(() => AVATAR_SIZE_MAP[this.size()]);

  initials = computed(() => {
    const n = this.name();
    if (!n) return '?';
    const parts = n.trim().split(/\s+/);
    return parts
      .slice(0, 2)
      .map((p) => p[0]?.toUpperCase() ?? '')
      .join('');
  });

  bgColor = computed(() => {
    const hash = this.name()
      .split('')
      .reduce((acc, c) => acc + c.charCodeAt(0), 0);
    return AVATAR_COLORS[hash % AVATAR_COLORS.length];
  });
}
