/**
 * Number and label formatting shared by the charts, in the current locale.
 */
import type { Benchmark } from '@/components/plots/charts';
import { DEFAULT_MEASUREMENT_YEARS } from '@/stores/filters';

export function useChartFormat() {
  const { t, locale } = useI18n();
  const filtersStore = useFiltersStore();

  /** a measured value: 2 decimals below 10 in magnitude, none above */
  function formatValue(value: number): string {
    return new Intl.NumberFormat(locale.value, {
      maximumFractionDigits: Math.abs(value) < 10 ? 2 : 0,
    }).format(value);
  }

  function formatCount(value: number): string {
    return value.toLocaleString(locale.value);
  }

  /** axis ticks: 2M rather than 2,000,000 */
  function formatCompact(value: number): string {
    return new Intl.NumberFormat(locale.value, { notation: 'compact' }).format(
      value,
    );
  }

  /** a 0..1 share as a whole percentage */
  function formatShare(value: number): string {
    return `${Math.round(value * 100)}%`;
  }

  /** "WHO 2021 · 15 µg/m³ (24 h)" */
  function describeBenchmark(b: Benchmark): string {
    const note = b.note ? ` (${b.note})` : '';
    return `${b.source} · ${formatValue(b.value)} ${b.unit}${note}`;
  }

  /** the measurement years filtered to: "All years", "2015 – 2020", "Since 2015"… */
  const rangeLabel = computed(() => {
    void filtersStore.updates;
    const { min, max } = filtersStore.measurement_years;
    const from = min > DEFAULT_MEASUREMENT_YEARS.min ? `${min}` : '';
    const to = max < DEFAULT_MEASUREMENT_YEARS.max ? `${max}` : '';
    if (!from && !to) return t('plots.all_years');
    if (from === to) return from;
    return from && to
      ? `${from} – ${to}`
      : from
        ? t('plots.since_year', { year: from })
        : t('plots.until_year', { year: to });
  });

  return {
    formatValue,
    formatCount,
    formatCompact,
    formatShare,
    describeBenchmark,
    rangeLabel,
  };
}
