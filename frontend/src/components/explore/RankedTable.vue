<template>
  <div
    v-if="layout === 'inline'"
    class="ranked-table"
    role="table"
    :style="`grid-template-columns: ${templateColumns};`"
  >
    <div class="ranked-table__row ranked-table__head" role="row">
      <span class="ranked-table__label" role="columnheader"
        ><slot name="label-header">{{ labelHeader }}</slot></span
      >
      <span class="ranked-table__track" role="columnheader">{{ barHeader }}</span>
      <span class="ranked-table__value" role="columnheader">{{ valueHeader }}</span>
      <span v-for="column in columns" :key="column.key" class="ranked-table__value" role="columnheader">{{
        column.header
      }}</span>
    </div>
    <component
      :is="entry.row?.clickable ? 'button' : 'div'"
      v-for="entry in entries"
      :key="entry.key"
      class="ranked-table__row"
      :class="{
        'ranked-table__row--clickable': entry.row?.clickable,
        'ranked-table__row--summary': entry.summary,
      }"
      role="row"
      :type="entry.row?.clickable ? 'button' : undefined"
      :title="entry.title"
      @click="entry.row?.clickable && emit('select', entry.row)"
    >
      <span class="ranked-table__label" role="rowheader" :title="entry.label">{{ entry.label }}</span>
      <span class="ranked-table__track" role="cell">
        <span class="ranked-table__bar" :class="entry.barClass" :style="entry.barStyle" />
      </span>
      <span class="ranked-table__value" role="cell">{{ entry.value }}</span>
      <span v-for="(cell, i) in entry.cells" :key="i" class="ranked-table__value" role="cell">{{ cell }}</span>
    </component>
    <div v-for="i in fillers" :key="`filler-${i}`" class="ranked-table__row ranked-table__filler" aria-hidden="true">
      <span class="ranked-table__label">&nbsp;</span>
      <span class="ranked-table__track"><span class="ranked-table__bar" /></span>
      <span class="ranked-table__value">&nbsp;</span>
      <span v-for="column in columns" :key="column.key" class="ranked-table__value">&nbsp;</span>
    </div>
  </div>
  <div v-else class="ranked-stack" role="table">
    <div class="ranked-stack__line ranked-table__head" role="row">
      <span role="columnheader"><slot name="label-header">{{ labelHeader }}</slot></span>
      <span class="ranked-stack__values">
        <span role="columnheader">{{ valueHeader }}</span>
        <span v-for="column in columns" :key="column.key" role="columnheader">{{ column.header }}</span>
      </span>
    </div>
    <component
      :is="entry.row?.clickable ? 'button' : 'div'"
      v-for="entry in entries"
      :key="entry.key"
      class="ranked-stack__row"
      :class="{
        'ranked-table__row--clickable': entry.row?.clickable,
        'ranked-table__row--summary': entry.summary,
      }"
      role="row"
      :type="entry.row?.clickable ? 'button' : undefined"
      :title="entry.title"
      @click="entry.row?.clickable && emit('select', entry.row)"
    >
      <span class="ranked-stack__line">
        <span class="ranked-table__label ranked-stack__label" role="rowheader">{{ entry.label }}</span>
        <span class="ranked-stack__values">
          <span class="ranked-table__value" role="cell">{{ entry.value }}</span>
          <span v-for="(cell, i) in entry.cells" :key="i" class="ranked-table__value" role="cell">{{ cell }}</span>
        </span>
      </span>
      <span class="ranked-stack__track" aria-hidden="true">
        <span class="ranked-table__bar" :class="entry.barClass" :style="entry.barStyle" />
      </span>
    </component>
    <div v-for="i in fillers" :key="`filler-${i}`" class="ranked-stack__row ranked-table__filler" aria-hidden="true">
      <span class="ranked-stack__line"><span>&nbsp;</span></span>
      <span class="ranked-stack__track"><span class="ranked-table__bar" /></span>
    </div>
  </div>
</template>

<script setup lang="ts" generic="T">
/**
 * Rows of horizontal bars on one scale, each with its value and extra cells,
 * then optionally one hatched row standing for the rows left out.
 */
import type { RankedColumn, RankedRow, RankedSummary } from '@/components/explore/ranked';

interface Props {
  /** in the order shown */
  rows: RankedRow<T>[];
  /** a line above the rows standing for all of them */
  summary?: RankedSummary | null | undefined;
  /** the rows summed into the hatched row; none when absent */
  other?: { rows: RankedRow<T>[]; value: number } | null;
  labelHeader?: string;
  barHeader?: string;
  valueHeader?: string;
  /** cells after the value */
  columns?: RankedColumn<T>[];
  /** keys of the rows drawn in the accent colour; all of them when absent */
  highlighted?: string[] | undefined;
  /** label of the summed row, "Other" by default */
  otherLabel?: string;
  formatValue?: ((value: number) => string) | undefined;
  /** in the inline layout, the share of the width the labels get; longer ones are cut short */
  labelWidth?: string | undefined;
  /** blank lines are added up to this many, so the table keeps its height */
  minRows?: number | undefined;
  /**
   * `inline` (default): label, bar and values side by side, labels aligned
   * on the bar; `stacked`: label and values on a line, the bar on a track
   * below, for narrow figures
   */
  layout?: 'inline' | 'stacked' | undefined;
}

const props = withDefaults(defineProps<Props>(), {
  other: null,
  summary: null,
  labelHeader: '',
  barHeader: '',
  valueHeader: '',
  columns: () => [],
  highlighted: undefined,
  otherLabel: '',
  formatValue: undefined,
  layout: 'inline',
  minRows: 0,
  labelWidth: '30%',
});
const emit = defineEmits<{ select: [row: RankedRow<T>] }>();
const { t } = useI18n();

const max = computed(() =>
  Math.max(0, ...props.rows.map((row) => row.value), props.other?.value ?? 0, props.summary?.value ?? 0),
);

const highlightedKeys = computed(() => (props.highlighted ? new Set(props.highlighted) : null));

const templateColumns = computed(() =>
  // the label column has a set share, whatever the labels: the bars always get the same room
  [props.labelWidth, 'minmax(48px, 1fr)', 'auto', ...props.columns.map(() => 'auto')].join(' '),
);

/** A line of the table: a row, or the hatched one standing for the rest. */
interface Entry {
  key: string;
  label: string;
  value: string;
  cells: string[];
  barStyle: Record<string, string>;
  barClass: Record<string, boolean>;
  title: string | undefined;
  summary: boolean;
  /** absent on the hatched line */
  row: RankedRow<T> | undefined;
}

function barStyle(value: number, color: string | undefined): Record<string, string> {
  return color ? { width: widthOf(value), background: color } : { width: widthOf(value) };
}

const entries = computed<Entry[]>(() => {
  const lines: Entry[] = [];
  const summary = props.summary;
  if (summary)
    lines.push({
      // row keys are data keys, which never start with a space
      key: ' summary',
      label: summary.label,
      value: summary.value === null ? '' : display(summary.value),
      cells: props.columns.map((column) => (props.rows.length ? column.format(props.rows) : '')),
      barStyle: barStyle(summary.value ?? 0, summary.color),
      barClass: { 'ranked-table__bar--blank': summary.value === null },
      title: summary.title,
      summary: true,
      row: undefined,
    });
  for (const row of props.rows)
    lines.push({
      key: row.key,
      label: row.label,
      value: display(row.value),
      cells: props.columns.map((column) => column.format([row])),
      barStyle: barStyle(row.value, row.color),
      barClass: { 'ranked-table__bar--muted': !row.color && !isHighlighted(row) },
      title: row.title,
      summary: false,
      row,
    });
  const other = props.other;
  if (other)
    lines.push({
      key: ' other',
      label: props.otherLabel || t('ranked_bars.other'),
      value: display(other.value),
      cells: props.columns.map((column) => column.format(other.rows)),
      barStyle: barStyle(other.value, undefined),
      barClass: {
        'ranked-table__bar--other': true,
        // grey when the rows it stands for have colours of their own, or
        // are all left out of the highlight
        'ranked-table__bar--other-muted': other.rows.some((row) => row.color) || !other.rows.some(isHighlighted),
      },
      title: t('ranked_bars.other_hint', other.rows.length),
      summary: false,
      row: undefined,
    });
  return lines;
});

// the summary line is on top of `minRows`, not one of them
const fillers = computed(() => Math.max(0, props.minRows - entries.value.filter((entry) => !entry.summary).length));

function display(value: number): string {
  return props.formatValue ? props.formatValue(value) : value.toLocaleString();
}

function widthOf(value: number): string {
  return max.value > 0 ? `${(value / max.value) * 100}%` : '0';
}

function isHighlighted(row: RankedRow<T>): boolean {
  return !highlightedKeys.value || highlightedKeys.value.has(row.key);
}
</script>

<style scoped lang="scss">
.ranked-table {
  display: grid;
  column-gap: 20px;
  font-size: 0.9375rem;
  color: $grey-10;
}

.ranked-table__row {
  display: grid;
  grid-column: 1 / -1;
  grid-template-columns: subgrid;
  align-items: center;
  padding: 6px 0;
  // reset when the row is a button
  margin: 0;
  border: 0;
  background: none;
  font: inherit;
  color: inherit;
  text-align: inherit;
}

.ranked-table__head {
  // stays in view when the table scrolls, as in the full list dialog
  position: sticky;
  top: 0;
  z-index: 1;
  background: white;
  padding-bottom: 8px;
  font-size: 0.6875rem;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: $grey-7;
}

// the line standing for every row, set apart from them
.ranked-table__row--summary {
  margin-bottom: 8px;
  padding-bottom: 12px;
  border-bottom: 1px solid $grey-4;

  .ranked-table__value {
    font-weight: 600;
  }
}

.ranked-table__row--clickable {
  cursor: pointer;

  &:hover .ranked-table__bar:not(.ranked-table__bar--muted) {
    background: $figure-accent-strong;
  }

  &:hover .ranked-table__label {
    text-decoration: underline;
  }

  &:focus-visible {
    outline: 2px solid $figure-accent-strong;
    outline-offset: 2px;
  }
}

.ranked-table__head .ranked-table__label {
  // the drill path's focus rings and tooltips are not clipped
  overflow: visible;
}

.ranked-table__label {
  text-align: right;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ranked-table__track {
  display: block;
  min-width: 0;
}

.ranked-table__head .ranked-table__track {
  text-align: left;
}

.ranked-table__bar {
  display: block;
  height: 18px;
  min-width: 2px;
  background: $figure-accent;
  transition:
    width 0.3s,
    background-color 0.15s;
}

.ranked-table__bar--muted {
  background: $figure-muted;
}

// the hatch keeps the accent: the rows it sums are data like the others
.ranked-table__bar--other {
  background: repeating-linear-gradient(-45deg, $figure-accent 0 2px, $figure-accent-tint 2px 5px);
}

.ranked-table__bar--other-muted {
  background: repeating-linear-gradient(-45deg, #9e9e9e 0 2px, #f5f5f5 2px 5px);
}

.ranked-stack {
  display: flex;
  flex-direction: column;
  gap: 14px;
  font-size: 0.9375rem;
  color: $grey-10;
}

.ranked-stack__row {
  display: flex;
  flex-direction: column;
  gap: 6px;
  // reset when the row is a button
  width: 100%;
  margin: 0;
  padding: 0;
  border: 0;
  background: none;
  font: inherit;
  color: inherit;
  text-align: inherit;
}

.ranked-stack__line {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 16px;
}

.ranked-table__filler,
.ranked-table__bar--blank {
  visibility: hidden;
}

.ranked-stack__label {
  min-width: 0;
  text-align: left;
  color: $grey-9;
}

.ranked-stack__values {
  display: flex;
  gap: 16px;
}

.ranked-stack__track {
  display: block;
  background: $figure-track;
}

.ranked-stack__track .ranked-table__bar--muted {
  background: #bdbdbd;
}

.ranked-table__value {
  text-align: right;
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
}
</style>
