<template>
  <div v-if="line" class="study-spread">
    <div class="study-spread__label">{{ t('explore_figures.pair.within') }}</div>
    <template v-if="rs.length">
      <div class="study-spread__strip" role="img" :aria-label="line">
        <span class="study-spread__zero" />
        <span v-for="(r, k) in rs" :key="k" class="study-spread__dot" :style="{ left: at(r) }" />
        <span v-if="median !== undefined" class="study-spread__median" :style="{ left: at(median) }" />
      </div>
      <div class="study-spread__scale" aria-hidden="true">
        <span>−1</span>
        <span>0</span>
        <span>1</span>
      </div>
    </template>
    <p class="study-spread__text">{{ line }}</p>
  </div>
</template>

<script setup lang="ts">
/**
 * The r inside each study behind a pooled r (#229): one dot per study on a
 * scale from −1 to 1, a bar at their median, and the same in words. A pooled
 * r far from the dots comes from the differences between the studies.
 */
import { useChartFormat } from '@/composables/useChartFormat';
import type { ExploreWithin } from '@/models';

interface Props {
  /** the studies behind the pooled r, by the method of the pooled r */
  within?: ExploreWithin | undefined;
}

const props = defineProps<Props>();
const { t } = useI18n();
const { describeWithin, rsWithin } = useChartFormat();

const rs = computed(() => rsWithin(props.within));
const median = computed(() => props.within?.median);
const line = computed(() => describeWithin(props.within));

/** the place of r on the strip, from −1 at the left to 1 at the right */
function at(r: number): string {
  return `${((r + 1) / 2) * 100}%`;
}
</script>

<style scoped lang="scss">
.study-spread {
  margin: 0 0 24px;
}

.study-spread__label {
  margin-bottom: 8px;
  font-size: 0.9375rem;
  color: $grey-8;
}

.study-spread__strip {
  position: relative;
  height: 16px;
  margin: 0 6px;
  border-bottom: 1px solid $grey-5;
}

.study-spread__zero {
  position: absolute;
  bottom: 0;
  left: 50%;
  height: 6px;
  border-left: 1px solid $grey-5;
}

.study-spread__dot {
  position: absolute;
  top: 3px;
  width: 9px;
  height: 9px;
  margin-left: -4.5px;
  border-radius: 50%;
  background: $figure-accent;
  opacity: 0.6;
}

.study-spread__median {
  position: absolute;
  top: -2px;
  bottom: -4px;
  margin-left: -1px;
  border-left: 2px solid $grey-10;
}

.study-spread__scale {
  display: flex;
  justify-content: space-between;
  margin-top: 2px;
  font-size: 0.75rem;
  color: $grey-7;
  font-variant-numeric: tabular-nums;
}

.study-spread__text {
  margin: 6px 0 0;
  font-size: 0.875rem;
  line-height: 1.4;
  color: $grey-9;
}
</style>
