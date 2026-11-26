 /**
 * Number and label formatting shared by the charts, in the current locale.
 */
import type { ExploreBenchmark } from '@/models';

export function useChartFormat() {
  const { t, locale } = useI18n();
  const exploreStore = useExploreStore();

  /** a measured value: 2 decimals below 10 in magnitude, none above */
  function formatValue(value: number): string {
    return new Intl.NumberFormat(locale.value, {
      maximumFractionDigits: Math.abs(value) < 10 ? 2 : 0,
    }).format(value);
  }

  /** a year: 1995, not 1,995 */
  function formatYear(value: number): string {
    return new Intl.NumberFormat(locale.value, { useGrouping: false, maximumFractionDigits: 0 }).format(value);
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

  /** a reference's value and unit, e.g. "1,200 ppm" */
  function describeReference(b: ExploreBenchmark): string {
    return `${formatValue(b.value)} ${b.unit}`;
  }

  /**
   * A figure's eyebrow with the pollutants it shows, as the filter bar counts
   * them: "Datasets by country · Carbon dioxide, Formaldehyde", "… · Carbon
   * dioxide +2". With none, every pollutant is shown and none is named.
   */
  function withPollutants(eyebrow: string, slugs: string[]): string {
    if (!slugs.length) return eyebrow;
    const names = slugs.map(exploreStore.parameterLabel);
    const pollutants =
      names.length <= 2
        ? names.join(', ')
        : t('explore_figures.pollutants_more', { first: names[0], count: names.length - 1 });
    return t('explore_figures.eyebrow_pollutants', { eyebrow, pollutants });
  }

  return {
    formatValue,
    formatYear,
    formatCount,
    formatCompact,
    formatShare,
    describeReference,
    withPollutants,
  };
}
