<template>
  <div class="range-list">
    <component
      :is="row.clickable ? 'button' : 'div'"
      v-for="row in rows"
      :key="row.key"
      class="range-list__row"
      :class="{ 'range-list__row--clickable': row.clickable }"
      :type="row.clickable ? 'button' : undefined"
      @click="row.clickable && emit('select', row)"
    >
      <div class="range-list__line">
        <span class="range-list__label" :title="row.label">{{ row.label }}</span>
        <span v-if="row.sublabel" class="range-list__sublabel" :title="row.sublabel">· {{ row.sublabel }}</span>
        <span class="range-list__value">{{ row.value }}</span>
      </div>
      <div class="range-list__track">
        <span class="range-list__range" :style="`left: ${at(row.low)}%; width: ${at(row.high) - at(row.low)}%;`" />
        <span class="range-list__dot" :style="`left: ${at(row.mid)}%;`" />
        <span v-if="typeof reference === 'number'" class="range-list__reference" :style="`left: ${at(reference)}%;`" />
        <q-tooltip v-if="row.tooltip">
          <div v-for="(line, i) in row.tooltip" :key="i">{{ line }}</div>
        </q-tooltip>
      </div>
    </component>
    <div v-for="i in fillers" :key="`filler-${i}`" class="range-list__row range-list__filler" aria-hidden="true">
      <div class="range-list__line">&nbsp;</div>
      <div class="range-list__track" />
    </div>
    <!-- the scale under the tracks, hidden without rows: the list keeps its height -->
    <div
      v-if="ticks.length || axisTitle"
      class="range-list__scale"
      :style="`visibility: ${rows.length ? 'visible' : 'hidden'};`"
      aria-hidden="true"
    >
      <div class="range-list__ticks">
        <span
          v-for="(tick, i) in ticks"
          :key="tick"
          class="range-list__tick"
          :class="{ 'range-list__tick--first': i === 0, 'range-list__tick--last': i === ticks.length - 1 }"
          :style="`left: ${at(tick)}%;`"
          >{{ tickText(tick) }}</span
        >
      </div>
      <div v-if="axisTitle" class="range-list__axis-title">{{ axisTitle }}</div>
    </div>
  </div>
</template>

<script lang="ts">
export interface RangeRow {
  key: string;
  label: string;
  /** after the label, e.g. "37 datasets" */
  sublabel: string;
  /** what the line ends with, e.g. the median */
  value: string;
  /** the range drawn on the track, and the dot inside it */
  low: number;
  mid: number;
  high: number;
  /** lines said on hover */
  tooltip?: string[];
  /** a click on the row emits `select` */
  clickable?: boolean;
}
</script>

<script setup lang="ts">
/**
 * Ranges on one scale, a row per group: the label and its value on a line,
 * under it a track with the range, a dot at its middle and a tick at the
 * reference; the scale's ticks and its title under the last track.
 */
import { drawRanges } from '@/components/explore/figureDrawings';
import { useImagePart } from '@/components/explore/figureImage';

interface Props {
  rows: RangeRow[];
  /** the scale's bounds */
  min: number;
  max: number;
  /** drawn as a tick across each track */
  reference?: number | null | undefined;
  /** blank rows are added up to this many, so the list keeps its height */
  minRows?: number | undefined;
  /** values written under the tracks, between `min` and `max` */
  ticks?: number[] | undefined;
  formatTick?: ((value: number) => string) | undefined;
  /** what the scale measures, with its unit, e.g. "Daily mean (ppm)" */
  axisTitle?: string | undefined;
}

const props = withDefaults(defineProps<Props>(), {
  reference: null,
  minRows: 0,
  ticks: () => [],
  formatTick: undefined,
  axisTitle: '',
});
const emit = defineEmits<{ select: [row: RangeRow] }>();

const fillers = computed(() => Math.max(0, props.minRows - props.rows.length));

function tickText(value: number): string {
  return props.formatTick ? props.formatTick(value) : value.toLocaleString();
}

/** a value's place on the scale, in percent, held inside it */
function at(value: number): number {
  if (props.max === props.min) return 0;
  return Math.min(100, Math.max(0, ((value - props.min) / (props.max - props.min)) * 100));
}

useImagePart((width) =>
  drawRanges(
    {
      rows: props.rows.map((row) => ({
        label: row.label,
        sublabel: row.sublabel,
        value: row.value,
        low: at(row.low) / 100,
        mid: at(row.mid) / 100,
        high: at(row.high) / 100,
      })),
      reference: typeof props.reference === 'number' ? at(props.reference) / 100 : null,
      ticks: props.ticks.map((tick) => ({ at: at(tick) / 100, text: tickText(tick) })),
      axisTitle: props.axisTitle,
    },
    width,
  ),
);
</script>

<style scoped lang="scss">
.range-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
  font-size: 0.9375rem;
  color: $grey-10;
}

.range-list__row {
  // reset when the row is a button
  display: block;
  width: 100%;
  min-width: 0;
  margin: 0;
  padding: 0;
  border: 0;
  background: none;
  font: inherit;
  color: inherit;
  text-align: inherit;
}

.range-list__row--clickable {
  cursor: pointer;

  &:hover .range-list__label {
    text-decoration: underline;
  }

  &:hover .range-list__dot {
    background: $figure-accent-strong;
  }

  &:focus-visible {
    outline: 2px solid $figure-accent-strong;
    outline-offset: 4px;
  }
}

// one line, never wider than the card: the sublabel gives way first, then
// the label, both cut with "…"; the value always shows in full
.range-list__line {
  display: flex;
  align-items: baseline;
  gap: 6px;
  min-width: 0;
  margin-bottom: 10px;
  line-height: 1.4;
}

.range-list__label,
.range-list__sublabel {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.range-list__label {
  flex: 0 1 auto;
}

.range-list__sublabel {
  flex: 0 1000 auto;
  font-size: 0.75rem;
  color: $grey-7;
}

.range-list__value {
  flex: none;
  margin-left: auto;
  padding-left: 12px;
  font-variant-numeric: tabular-nums;
}

.range-list__track {
  position: relative;
  height: 6px;
  background: $figure-track;
}

.range-list__range {
  position: absolute;
  top: 0;
  bottom: 0;
  background: rgba(74, 163, 154, 0.7);
}

.range-list__dot {
  position: absolute;
  top: 50%;
  width: 14px;
  height: 14px;
  margin: -7px 0 0 -7px;
  border-radius: 50%;
  background: $figure-accent;
  z-index: 1;
}

.range-list__reference {
  position: absolute;
  top: -7px;
  bottom: -7px;
  width: 0;
  margin-left: -1px;
  border-left: 2px solid $figure-gap;
  z-index: 2;
}

.range-list__filler {
  visibility: hidden;
}

// closer to the last track than the rows are to each other
.range-list__scale {
  margin-top: -8px;
  font-size: 0.75rem;
  color: $grey-7;
}

.range-list__ticks {
  position: relative;
  height: 16px;
}

// centred on its value; the first and last stay inside the track's ends
.range-list__tick {
  position: absolute;
  top: 0;
  transform: translateX(-50%);
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
}

.range-list__tick--first {
  transform: none;
}

.range-list__tick--last {
  transform: translateX(-100%);
}

.range-list__axis-title {
  margin-top: 4px;
  text-align: right;
}
</style>
