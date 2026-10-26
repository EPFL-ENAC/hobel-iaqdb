/** A value offered by a filter, with how many datasets it has. */
export interface FacetOption {
  value: string;
  label: string;
  count: number;
  /** said, not picked: e.g. "Not reported" */
  disabled?: boolean;
  /** the full label on hover, when the shown one is short */
  title?: string;
}

/** Options from a facet's counts, most counted first; unknown keys are said apart. */
export function toOptions(
  counts: Map<string | null, number>,
  label: (key: string) => string,
  keep: (key: string) => boolean = () => true,
): FacetOption[] {
  return [...counts.entries()]
    .flatMap(([key, count]) => (key !== null && key !== 'unknown' && keep(key) ? [{ value: key, label: label(key), count }] : []))
    .sort((a, b) => b.count - a.count || a.label.localeCompare(b.label));
}

/** The entities that do not say, as a "Not reported" option; none when every one says. */
export function notReported(counts: Map<string | null, number>, label: string): FacetOption | null {
  const count = (counts.get(null) ?? 0) + (counts.get('unknown') ?? 0);
  return count ? { value: '', label, count, disabled: true } : null;
}
