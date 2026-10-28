<template>
  <div class="distribution-table" :style="gridStyle">
    <!-- a blank line without a header: the table keeps its height -->
    <span class="distribution-table__head" style="grid-column: 3">{{ shareHeader || '\u00a0' }}</span>

    <!-- the scale's gridlines and reference lines, across every row; none without rows -->
    <div v-if="rows.length" class="distribution-table__overlay" aria-hidden="true">
      <span v-for="tick in ticks" :key="`tick-${tick}`" class="distribution-table__grid" :style="`left: ${at(tick)}%;`" />
      <span
        v-for="line in lines"
        :key="line.kind"
        class="distribution-table__line"
        :class="`distribution-table__line--${line.kind}`"
        :style="`left: ${at(line.value)}%;`"
      />
    </div>

    <template v-for="(row, i) in rows" :key="row.key">
      <div class="distribution-table__label" :style="`grid-row: ${i + 2};`">
        <div class="distribution-table__name" :title="row.label">{{ row.label }}</div>
        <div v-if="row.sublabel" class="distribution-table__sublabel">{{ row.sublabel }}</div>
      </div>
      <div class="distribution-table__plot" :style="`grid-row: ${i + 2};`">
        <span
          class="distribution-table__whisker"
          :style="`left: ${at(row.stats.p05)}%; width: ${at(row.stats.p95) - at(row.stats.p05)}%;`"
        />
        <span
          class="distribution-table__box"
          :style="`left: ${at(row.stats.p25)}%; width: ${at(row.stats.p75) - at(row.stats.p25)}%;`"
        />
        <span class="distribution-table__median" :style="`left: ${at(row.stats.p50)}%;`" />
        <q-tooltip v-if="row.tooltip" class="distribution-table__tooltip">
          <div v-for="(line, i) in row.tooltip" :key="i">{{ line }}</div>
        </q-tooltip>
      </div>
      <div class="distribution-table__share" :style="`grid-row: ${i + 2};`">
        <span class="distribution-table__track">
          <span v-if="row.share !== null" class="distribution-table__fill" :style="`width: ${row.share * 100}%;`" />
        </span>
        <span class="distribution-table__percent">{{ row.share === null ? '–' : shareText(row.share) }}</span>
      </div>
    </template>
    <div
      v-for="i in fillers"
      :key="`filler-${i}`"
      class="distribution-table__label"
      :style="`grid-row: ${rows.length + i + 1};`"
      aria-hidden="true"
    >
      &nbsp;
    </div>

    <!-- hidden, not removed, without rows: the table keeps its height -->
    <div
      class="distribution-table__axis"
      :style="`grid-row: ${rows.length + fillers + 2}; visibility: ${rows.length ? 'visible' : 'hidden'};`"
      aria-hidden="true"
    >
      <span v-for="tick in ticks" :key="tick" :style="`left: ${at(tick)}%;`">{{ tickText(tick) }}</span>
    </div>
  </div>
</template>

<script lang="ts">
import type { ExploreStats } from '@/models';

export interface DistributionRow {
  key: string;
  label: string;
  /** under the label, e.g. "19 datasets" */
  sublabel: string;
  stats: ExploreStats;
  /** 0..1, null when unknown */
  share: number | null;
  /** lines said on hover */
  tooltip?: string[];
}
</script>

<script setup lang="ts">
/**
 * Box plots on one scale, a row per group: whiskers from the 5th to the
 * 95th percentile, the box over the middle half, a tick at the median; the
 * reference and the database median run across every row, and each row
 * ends with its share at or below the reference.
 */
interface Props {
  rows: DistributionRow[];
  /** the scale: the first and last ticks are its bounds */
  ticks: number[];
  /** the reference, drawn solid */
  reference?: number | null;
  /** the median of the whole database, drawn dashed */
  median?: number | null;
  shareHeader?: string;
  /** blank rows are added up to this many, so the table keeps its height */
  minRows?: number | undefined;
  formatTick?: ((value: number) => string) | undefined;
  formatShare?: ((value: number) => string) | undefined;
}

const props = withDefaults(defineProps<Props>(), {
  reference: null,
  median: null,
  shareHeader: '',
  minRows: 0,
  formatTick: undefined,
  formatShare: undefined,
});

function tickText(value: number): string {
  return props.formatTick ? props.formatTick(value) : value.toLocaleString();
}

function shareText(value: number): string {
  return props.formatShare ? props.formatShare(value) : `${Math.round(value * 100)}%`;
}

const ROW_HEIGHT = 64;

const fillers = computed(() => Math.max(0, props.minRows - props.rows.length));

/** explicit rows: the overlay spans them by line number */
const gridStyle = computed(() => {
  const count = props.rows.length + fillers.value;
  return `grid-template-rows: auto repeat(${count}, ${ROW_HEIGHT}px) auto; --rows: ${count};`;
});

const lines = computed(() => [
  ...(props.median === null ? [] : [{ kind: 'median', value: props.median }]),
  ...(props.reference === null ? [] : [{ kind: 'reference', value: props.reference }]),
]);

/** a value's place on the scale, in percent, held inside it */
function at(value: number): number {
  const low = props.ticks[0] ?? 0;
  const high = props.ticks[props.ticks.length - 1] ?? 1;
  if (high === low) return 0;
  return Math.min(100, Math.max(0, ((value - low) / (high - low)) * 100));
}
</script>

<style scoped lang="scss">
.distribution-table {
  display: grid;
  grid-template-columns: minmax(0, 16%) minmax(0, 1fr) minmax(0, 24%);
  column-gap: 32px;
  font-size: 0.9375rem;
  color: $grey-10;
}

.distribution-table__head {
  grid-row: 1;
  padding-bottom: 12px;
  font-size: 0.6875rem;
  color: $grey-7;
}

.distribution-table__overlay {
  position: relative;
  grid-column: 2;
  grid-row: 2 / span var(--rows);
  pointer-events: none;
}

.distribution-table__grid,
.distribution-table__line {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 0;
}

.distribution-table__grid {
  border-left: 1px solid $grey-3;
}

.distribution-table__line--median {
  border-left: 1px dashed $grey-7;
  z-index: 2;
}

.distribution-table__line--reference {
  border-left: 2px solid $figure-gap;
  z-index: 2;
}

.distribution-table__label {
  grid-column: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-width: 0;
}

.distribution-table__name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.distribution-table__sublabel {
  font-size: 0.8125rem;
  color: $grey-7;
}

.distribution-table__plot {
  position: relative;
  grid-column: 2;
  z-index: 1;
}

.distribution-table__whisker {
  position: absolute;
  top: 50%;
  height: 0;
  border-top: 1px solid $figure-accent;
}

.distribution-table__box {
  position: absolute;
  top: calc(50% - 13px);
  height: 26px;
  border: 1px solid $figure-accent;
  background: $figure-accent-tint;
  // the whisker runs behind the box
  z-index: 1;
}

.distribution-table__median {
  position: absolute;
  top: calc(50% - 13px);
  height: 26px;
  border-left: 2px solid $grey-10;
  margin-left: -1px;
  z-index: 3;
}

.distribution-table__share {
  grid-column: 3;
  display: flex;
  align-items: center;
  gap: 12px;
}

.distribution-table__track {
  flex: 1;
  height: 18px;
  background: $figure-muted;
}

.distribution-table__fill {
  display: block;
  height: 100%;
  background: $figure-accent;
}

.distribution-table__percent {
  width: 3.5em;
  font-variant-numeric: tabular-nums;
}

.distribution-table__axis {
  position: relative;
  grid-column: 2;
  height: 32px;
  font-size: 0.75rem;
  color: $grey-7;

  span {
    position: absolute;
    top: 12px;
    transform: translateX(-50%);
    white-space: nowrap;
  }
}
</style>
