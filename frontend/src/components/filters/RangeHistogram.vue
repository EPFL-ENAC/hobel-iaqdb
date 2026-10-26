<template>
  <div class="range-histogram">
    <div class="range-histogram__bars" aria-hidden="true">
      <span
        v-for="bin in bars"
        :key="bin.start"
        class="range-histogram__bar"
        :class="{ 'range-histogram__bar--out': !inRange(bin.start) }"
        :style="`height: ${bin.height}%;`"
        :title="bin.title"
      />
    </div>
    <q-range
      :model-value="modelValue"
      :min="min"
      :max="max"
      :step="step"
      color="grey-10"
      track-size="2px"
      thumb-size="16px"
      class="range-histogram__slider"
      @update:model-value="(value) => value && emit('update:modelValue', { min: value.min, max: value.max })"
    />
    <div class="range-histogram__labels">
      <span>{{ label(modelValue.min) }}</span>
      <span class="range-histogram__caption">{{ caption }}</span>
      <span>{{ label(modelValue.max) }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * A range over a histogram: the bars say how much each band holds, those
 * outside the range greyed, and the slider under them picks the range.
 */
interface Props {
  modelValue: { min: number; max: number };
  min: number;
  max: number;
  step?: number;
  /** band lower bound → amount; bands are `width` wide */
  bins: Map<number, number>;
  width: number;
  /** under the slider, between its ends, e.g. "All years" */
  caption?: string;
  format?: ((value: number) => string) | undefined;
}

const props = withDefaults(defineProps<Props>(), { step: 1, caption: '', format: undefined });
const emit = defineEmits<{ 'update:modelValue': [value: { min: number; max: number }] }>();

/** every band from min to max, empty ones included */
const bars = computed(() => {
  const starts: number[] = [];
  for (let start = Math.floor(props.min / props.width) * props.width; start < props.max; start += props.width)
    starts.push(start);
  const top = Math.max(1, ...starts.map((s) => props.bins.get(s) ?? 0));
  return starts.map((start) => {
    const value = props.bins.get(start) ?? 0;
    // a band with something stays visible however small
    return { start, height: value ? Math.max(3, (value / top) * 100) : 0, title: `${label(start)}: ${value.toLocaleString()}` };
  });
});

function inRange(start: number): boolean {
  return start + props.width > props.modelValue.min && start <= props.modelValue.max;
}

function label(value: number): string {
  return props.format ? props.format(value) : String(value);
}
</script>

<style scoped lang="scss">
.range-histogram__bars {
  display: flex;
  align-items: flex-end;
  gap: 2px;
  height: 56px;
  padding: 0 8px;
  border-bottom: 1px solid $grey-4;
}

.range-histogram__bar {
  flex: 1;
  background: $figure-accent;
  transition: background-color 0.15s;
}

.range-histogram__bar--out {
  background: $figure-muted;
}

.range-histogram__slider {
  margin-top: 8px;
}

.range-histogram__labels {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  font-size: 0.75rem;
  color: $grey-8;
}

.range-histogram__caption {
  text-align: center;
}
</style>
