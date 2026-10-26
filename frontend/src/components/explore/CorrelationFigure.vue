<template>
  <ChartCard :eyebrow="eyebrow" :title="title">
    <template #controls>
      <span>{{ t('explore_figures.correlation.method') }}</span>
      <FigureToggle :model-value="method" :options="methodOptions" @update:model-value="onMethod" />
      <q-select
        :model-value="selected"
        :options="parameterOptions"
        :loading="coverage.loading.value"
        multiple
        emit-value
        map-options
        dense
        outlined
        options-dense
        :display-value="t('explore_figures.correlation.pollutants', { count: selected.length })"
        class="correlation-figure__pollutants"
        @update:model-value="onParameters"
        @popup-hide="onPopupHide"
      />
    </template>
    <FigureFrame
      :height="height"
      :loading="loading"
      :error="error"
      :empty="emptyMessage"
      :slow="t('explore_figures.correlation.slow')"
    >
      <div class="correlation-figure__matrix" :style="gridStyle" role="table">
        <template v-for="(row, j) in order" :key="row">
          <span class="correlation-figure__label" :style="`grid-row: ${j + 1}; grid-column: 1;`" role="rowheader">{{
            shortParameterName(row)
          }}</span>
          <button
            v-for="(col, i) in order"
            :key="col"
            type="button"
            class="correlation-figure__cell"
            :class="{
              'correlation-figure__cell--self': row === col,
              'correlation-figure__cell--strongest': isStrongest(row, col),
            }"
            :style="cellStyle(row, col, i, j)"
            :disabled="row === col || cellOf(row, col)?.r === null"
            @click="exploreStore.showPair(col, row)"
          >
            {{ row === col ? '–' : formatR(cellOf(row, col)?.r ?? null) }}
            <q-tooltip v-if="row !== col">
              <div>
                <b>{{ shortParameterName(col) }} × {{ shortParameterName(row) }}</b>
              </div>
              <div>{{ describe(row, col) }}</div>
            </q-tooltip>
          </button>
        </template>
        <span
          v-for="(col, i) in order"
          :key="`x-${col}`"
          class="correlation-figure__label correlation-figure__label--x"
          :style="`grid-row: ${order.length + 1}; grid-column: ${i + 2};`"
          >{{ shortParameterName(col) }}</span
        >
      </div>
    </FigureFrame>
  </ChartCard>
</template>

<script setup lang="ts">
/**
 * How the pollutants move together: one cell per pair, the correlation of
 * their hourly means in the same space at the same hour, teal when they rise
 * together, red when one falls as the other rises. The strongest pair is
 * outlined; a click on a cell plots the pair.
 */
import ChartCard from '@/components/explore/ChartCard.vue';
import FigureFrame from '@/components/explore/FigureFrame.vue';
import FigureToggle from '@/components/explore/FigureToggle.vue';
import { shortParameterName } from '@/components/plots/charts';
import { exploreFilter, exploreRange } from '@/api/explore';
import { useParametersWithRecords } from '@/composables/useContextScope';
import { useExploreRequest } from '@/composables/useExploreQuery';

interface Props {
  eyebrow: string;
  title: string;
  /** height of the matrix: its cells share it, however many pollutants */
  height?: number;
}

type Method = 'pearson' | 'spearman';

withDefaults(defineProps<Props>(), { height: 380 });
const { t, locale } = useI18n();
const filtersStore = useFiltersStore();
const exploreStore = useExploreStore();

/** the endpoint caps a matrix at 10 parameters (45 cells) */
const MAX_PARAMETERS = 10;
/** the pollutants the matrix opens on, when they have data */
const DEFAULT_SET = ['co2', 'relative_humidity', 'no2', 'pm2_5', 'pm10'];

const selected = ref<string[]>([]);
/** picked in the menu since the last load */
const picked = ref(false);
const method = ref<Method>('spearman');

const coverage = useParametersWithRecords();
const parameterOptions = coverage.options;
const { result, loading, error, empty, load } = useExploreRequest('relationships');

const methodOptions = computed<{ value: Method; label: string }[]>(() => [
  { value: 'pearson', label: t('plots.pearson') },
  { value: 'spearman', label: t('plots.spearman') },
]);

const emptyMessage = computed(() => {
  if (selected.value.length < 2) return t('explore_figures.correlation.pick_two');
  return empty.value ? t('plots.no_data') : '';
});

/** the axis order: as the matrix returned it */
const order = computed(() => result.value?.meta.parameters || []);

/** r and paired hours of each pair, both orders */
const cells = computed(() => {
  const map = new Map<string, { r: number | null; n: number }>();
  for (const bucket of result.value?.buckets || []) {
    const [a, b] = bucket.key;
    if (!a || !b) continue;
    const cell = { r: bucket.n ? (bucket.fit?.r ?? null) : null, n: bucket.n };
    map.set(`${a}|${b}`, cell);
    map.set(`${b}|${a}`, cell);
  }
  return map;
});

function cellOf(a: string, b: string) {
  return cells.value.get(`${a}|${b}`);
}

/** the pair with the largest |r| */
const strongest = computed(() => {
  let best: { key: string; r: number } | null = null;
  for (const [key, cell] of cells.value)
    if (cell.r !== null && (!best || Math.abs(cell.r) > Math.abs(best.r))) best = { key, r: cell.r };
  return best?.key ?? null;
});

function isStrongest(a: string, b: string): boolean {
  const key = strongest.value;
  return !!key && (key === `${a}|${b}` || key === `${b}|${a}`);
}

const gridStyle = computed(() => {
  const n = order.value.length;
  return `grid-template-columns: auto repeat(${n}, minmax(0, 1fr)); grid-template-rows: repeat(${n}, minmax(0, 1fr)) auto;`;
});

/** teal as they rise together, red as one falls; the stronger, the deeper */
function cellStyle(a: string, b: string, i: number, j: number): string {
  const place = `grid-row: ${j + 1}; grid-column: ${i + 2};`;
  const r = a === b ? null : (cellOf(a, b)?.r ?? null);
  if (r === null) return place;
  const depth = 0.12 + 0.88 * Math.abs(r);
  const color = r >= 0 ? `rgba(74, 163, 154, ${depth})` : `rgba(229, 57, 43, ${depth * 0.6})`;
  const text = Math.abs(r) > 0.6 ? 'white' : 'inherit';
  return `${place} background: ${color}; color: ${text};`;
}

/** .28, -.21: two decimals without the leading zero */
function formatR(r: number | null): string {
  if (r === null) return '–';
  return r.toFixed(2).replace(/^(-?)0\./, '$1.');
}

function describe(a: string, b: string): string {
  const cell = cellOf(a, b);
  if (!cell || cell.r === null) return t('plots.no_common_hours');
  return `r = ${cell.r.toFixed(2)} · ${t('plots.paired_hours_count', { count: cell.n.toLocaleString(locale.value) })}`;
}

function reload(): void {
  picked.value = false;
  void load(
    selected.value.length >= 2
      ? {
          agg: 'matrix',
          parameters: [...selected.value],
          method: method.value,
          filter: exploreFilter(),
          ...exploreRange(),
        }
      : null,
  );
}

/**
 * Pollutants with data, then the selection: keeps the pollutants that still
 * have data; with fewer than two, the page's selection or the default set,
 * filled up from the pollutants with data.
 */
async function settle(): Promise<void> {
  await coverage.refresh();
  const offered = new Set(parameterOptions.value.map((opt) => opt.value));
  const kept = selected.value.filter((slug) => offered.has(slug));
  if (kept.length >= 2) {
    selected.value = kept;
    return;
  }
  const global = exploreStore.parameters.filter((slug) => offered.has(slug));
  if (global.length >= 2) {
    selected.value = global.slice(0, MAX_PARAMETERS);
    return;
  }
  const defaults = DEFAULT_SET.filter((slug) => offered.has(slug));
  const start = defaults.length >= 2 ? defaults : [...new Set([...defaults, ...offered])];
  selected.value = start.slice(0, MAX_PARAMETERS);
}

/** Settle the pollutants, then load: on mount and when the filters are applied. */
async function refresh(): Promise<void> {
  await settle();
  reload();
}

function onMethod(value: Method): void {
  method.value = value;
  reload();
}

function onParameters(value: string[] | null): void {
  // past the cap, the last pick is dropped
  selected.value = (value || []).slice(0, MAX_PARAMETERS);
  picked.value = true;
}

/** one load once the menu closes, not one per pick */
function onPopupHide(): void {
  if (picked.value) reload();
}

onMounted(() => void refresh());
filtersStore.$onAction(({ name, after }) => {
  if (name === 'notifyUpdate') after(() => void refresh());
});
</script>

<style scoped lang="scss">
.correlation-figure__pollutants {
  min-width: 160px;

  :deep(.q-field__control) {
    border-radius: 2px;
  }
}

.correlation-figure__matrix {
  display: grid;
  gap: 8px;
  font-size: 0.875rem;
  color: $grey-10;
}

.correlation-figure__label {
  align-self: center;
  padding-right: 8px;
  font-size: 0.8125rem;
  text-align: right;
  white-space: nowrap;
}

.correlation-figure__label--x {
  padding: 8px 0 0;
  text-align: center;
}

.correlation-figure__cell {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 0;
  padding: 0;
  border: 2px solid transparent;
  background: $figure-track;
  font: inherit;
  font-variant-numeric: tabular-nums;
  color: inherit;
  cursor: pointer;

  &:disabled {
    cursor: default;
  }

  &:not(:disabled):hover {
    border-color: $grey-6;
  }
}

.correlation-figure__cell--self {
  background: $figure-muted;
  color: $grey-7;
}

.correlation-figure__cell--strongest {
  border-color: $grey-10;
}
</style>
