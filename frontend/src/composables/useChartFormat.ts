/**
 * Number and label formatting shared by the charts, in the current locale.
 */
import type { Benchmark } from '@/components/plots/charts';

export function useChartFormat() {
  const { t, locale } = useI18n();

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

  /**
   * a 0..1 share as a whole percentage; a share short of either end never
   * rounds onto it: a trace shows "< 1%", a near-whole "> 99%"
   */
  function formatShare(value: number): string {
    if (value > 0 && value < 0.005) return '< 1%';
    if (value < 1 && value >= 0.995) return '> 99%';
    return `${Math.round(value * 100)}%`;
  }

  /** "800 ppm", marked "(placeholder)" while the reference is a stand-in */
  function describeReference(b: Benchmark): string {
    const value = `${formatValue(b.value)} ${b.unit}`;
    return b.placeholder ? `${value} (${t('plots.placeholder').toLowerCase()})` : value;
  }

  return {
    formatValue,
    formatCount,
    formatCompact,
    formatShare,
    describeReference,
  };
}
