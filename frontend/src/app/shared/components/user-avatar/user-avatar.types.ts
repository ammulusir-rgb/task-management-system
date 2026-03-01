/**
 * User Avatar component types
 */
export type AvatarSize = 'sm' | 'md' | 'lg';

export const AVATAR_SIZE_MAP: Record<AvatarSize, number> = {
  sm: 28,
  md: 36,
  lg: 48,
};

export const AVATAR_COLORS: string[] = [
  '#2563eb', '#7c3aed', '#db2777', '#ea580c',
  '#16a34a', '#0891b2', '#4f46e5', '#dc2626',
];
