/**
 * Returns a placeholder pole ID used before GPS resolves the nearest real pole.
 * Intentionally not a real DB pole so it can't be confused with an actual match.
 */
export function randomPoleId(): string {
  return 'Locating…';
}
