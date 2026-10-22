/**
 * The drill of a metadata count chart, whatever draws it: the request per
 * level, the drill stack, what a click on a bucket does, and the level shown
 * with its result, set together once a level has loaded.
 */
import type { ShallowRef } from 'vue';
import { exploreFilter } from '@/api/explore';
import {
  hasGlobalFilter,
  keyLabel,
  onBucketClick,
  refine,
  selectedFilterKeys,
} from '@/components/plots/charts';
import { useDrillStack } from '@/composables/useDrillStack';
import { useExploreRequest } from '@/composables/useExploreQuery';
import type {
  ExploreBucket,
  ExploreDimension,
  ExploreEntity,
  ExploreParams,
  ExploreResult,
} from '@/models';

export interface MetadataDrillProps {
  /** catalog entity counted per key */
  entity: ExploreEntity;
  /**
   * Dimension keys from /stats/schema, the levels a click goes down through:
   * the chart opens on the first, a click on the last one opens the bucket's
   * catalog view (a study opens its page).
   */
  path: string[];
  /**
   * `drill`: a click goes down the path, level by level; `filter`: a click
   * pushes the bucket key into the global filters, so the map, the lists and
   * every chart re-query. The keys already selected in the global filters
   * are highlighted; `none`: the chart is read-only.
   */
  click: 'drill' | 'filter' | 'none';
  /** count only entities that contain the selected parameters */
  withParameters: boolean;
}

export interface DrillLevel {
  params: ExploreParams;
  dimension: ExploreDimension;
  label: string;
}

export interface DrillShown {
  level: DrillLevel;
  result: ExploreResult;
}

export function useMetadataDrill(props: MetadataDrillProps) {
  const { t } = useI18n();
  const router = useRouter();
  const filtersStore = useFiltersStore();
  const exploreStore = useExploreStore();

  const { result, loading, error, empty, load } = useExploreRequest('metadata');
  const shown: ShallowRef<DrillShown | null> = shallowRef(null);
  /** `stack[0]` is the chart as mounted */
  const { stack, current, show, popTo } = useDrillStack<DrillLevel, ExploreResult>({
    fetch: (level) => load(level?.params ?? null),
    paint: (level, value) => (shown.value = { level, result: value }),
    clear: () => (shown.value = null),
  });

  /** whether a click on the current level does anything */
  const clickable = computed(() => {
    const dimension = current.value?.dimension;
    if (!dimension || props.click === 'none') return false;
    if (props.click === 'filter') return hasGlobalFilter(dimension.filter_path);
    return !!dimension.filter_path;
  });

  /** whether a click on the current level drills, rather than navigates */
  const drills = computed(
    () => props.click === 'drill' && stack.value.length < props.path.length,
  );

  /** In `filter` mode, the keys of this dimension already in the global filters. */
  const selectedKeys = computed<Set<string>>(() => {
    void filtersStore.updates;
    if (props.click !== 'filter') return new Set();
    return new Set(selectedFilterKeys(current.value?.dimension.filter_path));
  });

  /** The dimensions of the path, those a click cannot reach left out. */
  const chain = computed<ExploreDimension[]>(() =>
    (props.click === 'drill' ? props.path : props.path.slice(0, 1)).flatMap(
      (key) => exploreStore.dimension(key) ?? [],
    ),
  );

  onMounted(() => void restart());
  // applying the filters (or the parameters) restarts the drill from the top
  filtersStore.$onAction(({ name, after }) => {
    if (name === 'notifyUpdate') after(() => void restart());
  });

  /** Rebuild the first level from the current filters and load it. */
  function restart(): Promise<void> {
    const first = props.path[0];
    const dimension = first ? exploreStore.dimension(first) : undefined;
    if (!first || !dimension) return show([]);
    const params: ExploreParams = {
      entity: props.entity,
      by: [first],
      filter: exploreFilter(),
    };
    if (props.withParameters && exploreStore.parameters.length)
      params.parameters = [...exploreStore.parameters];
    return show([{ params, dimension, label: dimension.label }]);
  }

  function label(
    dimension: ExploreDimension,
    key: string | null | undefined,
  ): string {
    if (key === null || key === undefined) return t('plots.unknown');
    return keyLabel(dimension.key, key);
  }

  /** Click a bucket of the current level, labelled `name` in the next one. */
  function select(bucket: ExploreBucket, name: string): void {
    const level = current.value;
    if (!clickable.value || !level) return;
    if (props.click === 'filter') {
      // the filters store bumps `updates`, which restarts the chart from the root
      onBucketClick(
        { kind: 'filter', dimension: level.dimension, params: level.params },
        bucket,
      );
      return;
    }
    if (!drills.value) {
      onBucketClick(
        { kind: 'navigate', dimension: level.dimension, params: level.params, router },
        bucket,
      );
      return;
    }
    const key = bucket.key[0];
    const dimension = exploreStore.dimension(props.path[stack.value.length] || '');
    if (key === null || key === undefined || !dimension) return;
    const next = refine(level.params, level.dimension, key);
    next.by = [dimension.key];
    void show([...stack.value, { params: next, dimension, label: name }]);
  }

  return {
    result,
    loading,
    error,
    empty,
    stack,
    current,
    shown,
    chain,
    clickable,
    drills,
    selectedKeys,
    popTo,
    label,
    select,
  };
}
