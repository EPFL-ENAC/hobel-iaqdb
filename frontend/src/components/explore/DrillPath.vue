<template>
  <span class="drill-path">
    <button
      v-if="currentIndex > 0"
      type="button"
      class="drill-path__back"
      :aria-label="t('explore_figures.drill_back', { level: steps[currentIndex - 1]?.label })"
      @click.stop="emit('pop', currentIndex - 1)"
    >
      <q-icon name="arrow_back" size="14px" />
      <q-tooltip>{{ t('explore_figures.drill_back', { level: steps[currentIndex - 1]?.label }) }}</q-tooltip>
    </button>
    <span class="drill-path__current">{{ steps[currentIndex]?.label }}</span>
    <span v-if="steps.length > 1" class="drill-path__dots" :aria-label="t('explore_figures.drill_path')" role="list">
      <component
        :is="step.state === 'past' ? 'button' : 'span'"
        v-for="(step, i) in steps"
        :key="i"
        role="listitem"
        class="drill-path__dot"
        :class="`drill-path__dot--${step.state}`"
        :type="step.state === 'past' ? 'button' : undefined"
        :aria-label="step.label"
        :aria-current="step.state === 'current' ? 'step' : undefined"
        @click.stop="step.state === 'past' && emit('pop', i)"
      >
        <q-tooltip>{{ step.label }}</q-tooltip>
      </component>
    </span>
  </span>
</template>

<script lang="ts">
export interface DrillStep {
  label: string;
  /** gone through (a click goes back up to it), shown, or below */
  state: 'past' | 'current' | 'next';
}
</script>

<script setup lang="ts">
/**
 * Where a drill stands, on one line that never wraps: back up one level, the
 * level shown, then a dot per level of the path, named on hover.
 */
const props = defineProps<{ steps: DrillStep[] }>();
const emit = defineEmits<{ pop: [index: number] }>();
const { t } = useI18n();

const currentIndex = computed(() => Math.max(0, props.steps.findIndex((step) => step.state === 'current')));
</script>

<style scoped lang="scss">
.drill-path {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  white-space: nowrap;
}

.drill-path__back {
  display: inline-flex;
  padding: 2px;
  margin: -2px 0;
  border: 0;
  border-radius: 50%;
  background: none;
  color: $grey-10;
  cursor: pointer;

  &:hover {
    background: $grey-3;
  }
}

.drill-path__current {
  color: $grey-10;
}

.drill-path__dots {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.drill-path__dot {
  width: 7px;
  height: 7px;
  padding: 0;
  border: 1px solid $grey-6;
  border-radius: 50%;
  background: none;
}

.drill-path__dot--past {
  border-color: $grey-8;
  background: $grey-8;
  cursor: pointer;
}

.drill-path__dot--current {
  border-color: $figure-accent;
  background: $figure-accent;
}

.drill-path__back:focus-visible,
.drill-path__dot--past:focus-visible {
  outline: 2px solid $figure-accent;
  outline-offset: 2px;
}
</style>
