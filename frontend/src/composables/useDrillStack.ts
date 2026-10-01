/**
 * A chart's drill stack, `stack[0]` being the level it opens on, the last
 * one the level shown. `show(levels)` makes them the stack and loads the
 * last one; `popTo(i)` goes back up to a breadcrumb.
 */
import type { ShallowRef } from 'vue';

export interface DrillStackOptions<L, R> {
  /** load a level; called with null when the stack is empty, to reset */
  fetch: (level: L | null) => Promise<R | null>;
  /** draw the loaded level */
  paint: (level: L, result: R) => void;
  /** nothing to draw: the stack is empty or the load failed */
  clear: () => void;
}

export function useDrillStack<L, R>({
  fetch,
  paint,
  clear,
}: DrillStackOptions<L, R>) {
  // replaced whole, never mutated: its levels stay plain objects
  const stack: ShallowRef<L[]> = shallowRef([]);
  const current = computed(() => stack.value[stack.value.length - 1] ?? null);

  /** Make `levels` the drill stack and load its last level. */
  async function show(levels: L[]): Promise<void> {
    stack.value = levels;
    const level = current.value;
    const result = await fetch(level);
    // a later show() took over while this one waited
    if (current.value !== level) return;
    if (level === null || result === null) clear();
    else paint(level, result);
  }

  function popTo(index: number): void {
    if (index < stack.value.length - 1)
      void show(stack.value.slice(0, index + 1));
  }

  return { stack, current, show, popTo };
}
