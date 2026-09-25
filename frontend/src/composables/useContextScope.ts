/**
 * The pollutant and context menus of the statistics charts. Both offer only
 * what has data under the global filters: pollutants with records, contexts
 * with at least one known value for the chosen pollutant.
 *
 * Event based: the chart calls `refresh()` when it mounts and when the
 * filters are applied, and the `select*` handlers from its menus; each
 * resolves once the menus settled, so the chart loads its data after.
 */
import type { Ref } from 'vue';
import {
  benchmarkOf,
  isUnknownKey,
  keyLabel,
  refine,
  STATS_CONTEXTS,
} from '@/components/plots/charts';
import { exploreFilter, exploreRange } from '@/api/explore';
import { useExploreRequest } from '@/composables/useExploreQuery';
import { DEFAULT_PARAMETER } from '@/stores/explore';
import type { ExploreParams } from '@/models';

/** Options of the pollutant menu. */
export interface ParameterChoiceOptions {
  /** list only pollutants with a benchmark, for charts that compare to one */
  withBenchmark?: boolean;
}

/**
 * The pollutant a chart shows, one at a time: the menu lists the globally
 * selected pollutants (all when none is) that have records, and a benchmark
 * when `withBenchmark`.
 */
export function useParameterChoice({
  withBenchmark = false,
}: ParameterChoiceOptions = {}) {
  const exploreStore = useExploreStore();
  const parameter = ref<string | null>(null);
  const coverage = useExploreRequest('measurements');

  /** slugs with records under the filters; null until known */
  const available = computed(() => {
    const buckets = coverage.result.value?.buckets;
    if (!buckets) return null;
    return new Set(
      buckets.flatMap((b) => (b.key[0] && b.n_records ? [b.key[0]] : [])),
    );
  });

  const parameterOptions = computed(() => {
    const selected = new Set(exploreStore.parameters);
    const withData = available.value;
    return exploreStore.parameterOptions.filter(
      (opt) =>
        (!selected.size || selected.has(opt.value)) &&
        (!withData || withData.has(opt.value)) &&
        (!withBenchmark || !!benchmarkOf(exploreStore.schema, opt.value)),
    );
  });

  const parameterLabel = computed(() =>
    exploreStore.parameterLabel(parameter.value || ''),
  );

  /** keeps the choice while offered, else the default, else the first */
  function settle() {
    const values = parameterOptions.value.map((opt) => opt.value);
    if (parameter.value && values.includes(parameter.value)) return;
    parameter.value = values.includes(DEFAULT_PARAMETER)
      ? DEFAULT_PARAMETER
      : (values[0] ?? null);
  }

  /** Reload which pollutants have records, then settle the choice. */
  async function refresh(): Promise<void> {
    await coverage.load({
      agg: 'coverage',
      by: ['parameter'],
      filter: exploreFilter(),
      ...exploreRange(),
    });
    settle();
  }

  return { parameter, parameterOptions, parameterLabel, refresh };
}

/** Options of the context menu. */
export interface ContextChoiceOptions {
  /** adds an "All" entry (null), the initial choice */
  optional?: boolean;
  /** the initial choice when not optional */
  initial?: string;
  /** contexts left out, e.g. the dimension the chart already groups by */
  exclude?: string[];
  /**
   * a dimension the chart needs known: contexts and values are offered only
   * where some data has a known key of it, e.g. a ventilation type
   */
  requireKnown?: string;
}

/** Group-by of a menu query: the menu's dimension, then the one it needs known. */
function menuBy(key: string, requireKnown?: string): string[] {
  return requireKnown ? [key, requireKnown] : [key];
}

/** Whether a menu bucket counts: a known menu key, and a known required key. */
function counts(
  bucket: { key: (string | null)[] },
  requireKnown?: string,
): boolean {
  const key = bucket.key[0];
  if (key === null || key === undefined) return false;
  return !requireKnown || !isUnknownKey(bucket.key[1]);
}

/**
 * The context a chart compares or narrows to. The menu lists the contexts
 * with at least one known value for the pollutant. `optional` adds an "All"
 * entry (null); otherwise the choice starts on `initial`.
 */
export function useContextChoice(
  parameter: Ref<string | null>,
  {
    optional = false,
    initial = 'country',
    exclude = [],
    requireKnown,
  }: ContextChoiceOptions = {},
) {
  const { t } = useI18n();
  const exploreStore = useExploreStore();
  const context = ref<string | null>(optional ? null : initial);
  const probes = STATS_CONTEXTS.filter((key) => !exclude.includes(key)).map(
    (key) => [key, useExploreRequest('measurements')] as const,
  );

  /** context keys with a known value; null until every probe answered */
  const available = computed(() => {
    const keys = new Set<string>();
    for (const [key, probe] of probes) {
      const buckets = probe.result.value?.buckets;
      if (!buckets) return null;
      if (buckets.some((b) => counts(b, requireKnown))) keys.add(key);
    }
    return keys;
  });

  const contextOptions = computed(() => {
    const withData = available.value;
    const options = probes.flatMap(([key]) => {
      const dimension = exploreStore.dimension(key);
      if (!dimension || (withData && !withData.has(key))) return [];
      return [{ value: key, label: dimension.label }];
    });
    return optional
      ? [{ value: null, label: t('plots.no_context') }, ...options]
      : options;
  });

  const contextDimension = computed(() =>
    context.value ? exploreStore.dimension(context.value) : undefined,
  );

  /**
   * Reload which contexts have data for the pollutant; a context that lost
   * its data falls back to the first one offered.
   */
  async function refresh(): Promise<void> {
    const slug = parameter.value;
    await Promise.all(
      probes.map(([key, probe]) =>
        probe.load(
          slug && exploreStore.dimension(key)
            ? {
                agg: 'count',
                by: menuBy(key, requireKnown),
                parameters: [slug],
                grain: 'day',
                filter: exploreFilter(),
                ...exploreRange(),
              }
            : null,
        ),
      ),
    );
    const options = contextOptions.value;
    if (!options.some((opt) => opt.value === context.value))
      context.value = options[0]?.value ?? null;
  }

  return { context, contextOptions, contextDimension, refresh };
}

/**
 * Pollutant and an optional context value (e.g. country = SG) a chart is
 * narrowed to, on top of the global filters. The value menu lists the
 * context's values with data.
 */
export function useContextScope(
  options: ParameterChoiceOptions &
    Pick<ContextChoiceOptions, 'exclude' | 'requireKnown'> = {},
) {
  const { t } = useI18n();
  const parameters = useParameterChoice(options);
  const { parameter } = parameters;
  const contexts = useContextChoice(parameter, {
    optional: true,
    exclude: options.exclude ?? [],
    ...(options.requireKnown ? { requireKnown: options.requireKnown } : {}),
  });
  const { context, contextDimension } = contexts;
  const contextValue = ref<string | null>(null);
  const valuesRequest = useExploreRequest('measurements');

  const contextLabel = computed(
    () => contextDimension.value?.label || t('plots.context_value'),
  );

  const valueOptions = computed(() => {
    const dimension = contextDimension.value;
    if (!dimension) return [];
    const keys = new Set(
      (valuesRequest.result.value?.buckets || []).flatMap((b) =>
        counts(b, options.requireKnown) && b.key[0] ? [b.key[0]] : [],
      ),
    );
    return [...keys]
      .map((key) => ({ value: key, label: keyLabel(dimension.key, key) }))
      .sort((a, b) => a.label.localeCompare(b.label));
  });

  const valuesLoading = computed(() => valuesRequest.loading.value);

  /** the global filters, narrowed to the chosen context value */
  function scopedFilter(): ExploreParams {
    const base: ExploreParams = { filter: exploreFilter() };
    const dimension = contextDimension.value;
    if (!dimension || !contextValue.value) return base;
    return refine(base, dimension, contextValue.value);
  }

  /**
   * Context values with data for the pollutant, any year; a value that lost
   * its data is dropped.
   */
  async function refreshValues(): Promise<void> {
    if (!context.value || !parameter.value) {
      await valuesRequest.load(null);
      contextValue.value = null;
      return;
    }
    await valuesRequest.load({
      filter: exploreFilter(),
      agg: 'count',
      by: menuBy(context.value, options.requireKnown),
      parameters: [parameter.value],
      grain: 'day',
    });
    if (
      contextValue.value &&
      !valueOptions.value.some((o) => o.value === contextValue.value)
    )
      contextValue.value = null;
  }

  /** Reload every menu, pollutant first: the others depend on it. */
  async function refresh(): Promise<void> {
    await parameters.refresh();
    await contexts.refresh();
    await refreshValues();
  }

  async function selectParameter(value: string | null): Promise<void> {
    parameter.value = value;
    await contexts.refresh();
    await refreshValues();
  }

  async function selectContext(value: string | null): Promise<void> {
    context.value = value;
    contextValue.value = null;
    await refreshValues();
  }

  function selectValue(value: string | null): void {
    contextValue.value = value;
  }

  return {
    parameter,
    parameterOptions: parameters.parameterOptions,
    parameterLabel: parameters.parameterLabel,
    context,
    contextValue,
    contextOptions: contexts.contextOptions,
    contextDimension,
    contextLabel,
    valueOptions,
    valuesLoading,
    scopedFilter,
    refresh,
    selectParameter,
    selectContext,
    selectValue,
  };
}
