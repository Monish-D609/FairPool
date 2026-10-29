// High-visibility, distinct chromatic palette optimized for dark and satellite map tiles
export const ROUTE_PALETTE = [
  '#06B6D4', // Car 1: Electric Cyan
  '#F97316', // Car 2: Radiant Orange
  '#10B981', // Car 3: Emerald Mint
  '#A855F7', // Car 4: Vivid Violet
  '#EC4899', // Car 5: Neon Pink
  '#FBBF24', // Car 6: Amber Gold
  '#3B82F6', // Car 7: Cobalt Blue
  '#14B8A6', // Car 8: Deep Teal
  '#F43F5E', // Car 9: Rose Red
  '#84CC16', // Car 10: Lime Green
  '#6366F1', // Car 11: Electric Indigo
  '#D946EF', // Car 12: Bright Fuchsia
]

export function getTripColor(index: number): string {
  return ROUTE_PALETTE[index % ROUTE_PALETTE.length]
}
