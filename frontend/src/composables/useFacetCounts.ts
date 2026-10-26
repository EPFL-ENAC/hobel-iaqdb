/**
 * Counts behind the filter dialog: datasets per value of a dimension under
 * the draft, every filter applied but the facet's own, so each value says
 * what picking it would leave. Reloads as the draft changes.
 */
import { exploreFilter, exploreRange } from '@/api/explore';
import { without, type FilterDraft } from '@/composables/useFilterDraft';
import { useExploreQuery } from '@/composables/useExploreQuery';
import type { ExploreBucket, ExploreParams } from '@/models';

export interface FacetOptions {
  /** dimension keys; the counts are keyed by the first, or by all joined with "|" */
  by: string[];
  /** the draft fields the facet sets, left out of its own counts */
  own: (keyof FilterDraft)[];
  /** `datasets` (default): datasets per value; `records`: measured records per value */
  count?: 'datasets' | 'records';
}

export function facetParams(draft: FilterDraft, { by, own, count = 'datasets' }: FacetOptions): ExploreParams {
  const scope = without(draft, own);
  const parameters = own.includes('parameters') || !scope.parameters.length ? {} : { parameters: [...scope.parameters] };
  if (count === 'records')
    return { agg: 'count', by, grain: 'day', filter: exploreFilter(scope), ...exploreRange(scope), ...parameters };
  return { entity: 'datasets', by, filter: exploreFilter(scope), ...parameters };
}

function keyOf(bucket: ExploreBucket, width: number): string | null {
  if (width === 1) return bucket.key[0] ?? null;
  return bucket.key.some((k) => k === null) ? null : bucket.key.join('|');
}

export function useFacetCounts(draft: FilterDraft, options: FacetOptions) {
  const route = options.count === 'records' ? 'measurements' : 'metadata';
  const query = useExploreQuery(route, () => facetParams(draft, options));

  /** value → count; null for the entities that do not say */
  const counts = computed(() => {
    const map = new Map<string | null, number>();
    for (const bucket of query.result.value?.buckets || []) {
      const key = keyOf(bucket, options.by.length);
      const value = options.count === 'records' ? (bucket.n_records ?? 0) : bucket.n;
      map.set(key, (map.get(key) ?? 0) + value);
    }
    return map;
  });

  /** the share of entities that say: 1 when every one has a value */
  const filled = computed(() => {
    let known = 0;
    let all = 0;
    for (const [key, n] of counts.value) {
      all += n;
      if (key !== null && key !== 'unknown') known += n;
    }
    return all ? known / all : null;
  });

  return { counts, filled, loading: query.loading, error: query.error };
}
