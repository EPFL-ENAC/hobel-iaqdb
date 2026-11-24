 /**
 * Number and label formatting shared by the charts, in the current locale.
 */
import type { Benchmark } from '@/components/plots/charts';
import type { ExploreWithin } from '@/models';

export function useChartFormat() {
  const { t, locale } = useI18n();

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

  /** "800 ppm", marked "(placeholder)" while the reference is a stand-in */
  function describeReference(b: Benchmark): string {
    const value = `${formatValue(b.value)} ${b.unit}`;
    return b.placeholder ? `${value} (${t('plots.placeholder').toLowerCase()})` : value;
  }

  /**
   * The r inside each study (#229) in one line: their median and range, out
   * of the studies behind the pooled r. Empty below two studies, as the r of
   * a single study is the pooled r.
   */
  /** The r of the studies of `within` that have one, ascending. */
  function rsWithin(within: ExploreWithin | undefined): number[] {
    return within?.studies.flatMap((study) => (study.r === undefined ? [] : [study.r])) ?? [];
  }

  /** The r within each study behind a pooled r, in one line; none below two studies. */
  function describeWithin(within: ExploreWithin | undefined): string {
    const total = within?.studies.length ?? 0;
    if (total < 2) return '';
    const rs = rsWithin(within);
    const first = rs[0];
    const last = rs[rs.length - 1];
    if (first === undefined || last === undefined) return t('plots.within_none');
    if (rs.length === 1) return t('plots.within_one', { total, r: first.toFixed(2) });
    return t('plots.within', {
      count: rs.length,
      total,
      median: within?.median?.toFixed(2) ?? '–',
      min: first.toFixed(2),
      max: last.toFixed(2),
    });
  }


  return {
    formatValue,
    formatYear,
    formatCount,
    formatCompact,
    formatShare,
    describeReference,
    describeWithin,
    rsWithin,
  };
}
