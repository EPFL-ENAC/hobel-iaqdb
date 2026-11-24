<template>
  <div class="split-panels">
    <section v-for="panel in panels" :key="panel.id" class="split-panels__panel">
      <header class="split-panels__head">
        <span class="split-panels__group" :title="panel.label">{{ panel.label }}</span>
        <span class="split-panels__r" :class="{ 'split-panels__r--none': !panel.enough }">{{ panel.r }}</span>
      </header>
      <div class="split-panels__facts">
        <StudiesDialog
          v-if="panel.studies"
          :title="`${title} · ${panel.label}`"
          :method="method"
          :r="panel.bucket.fit?.r"
          :within="panel.bucket.within"
          :points-label="pointsLabel"
          >{{ panel.studies }}</StudiesDialog
        >
        <span v-for="fact in panel.facts" :key="fact"> · {{ fact }}</span>
      </div>
      <div v-if="panel.within" class="split-panels__within">
        {{ panel.within }}
      </div>
      <e-charts
        autoresize
        :init-options="initOptions"
        :option="panel.option"
        :update-options="updateOptions"
        :style="{ height: `${height}px` }"
      />
    </section>
  </div>
</template>

<script setup lang="ts">
/**
 * A relationship split by a dimension (#229): one small chart per group, in a
 * grid of at most three columns in the order of the buckets, on the axis ranges
 * the chart gives to all. Each group says its r, its studies (a link to their list), its
 * counts, and the r within each study.
 */
import ECharts from 'vue-echarts';
import type { EChartsOption } from 'echarts';
import { use } from 'echarts/core';
import { LineChart, ScatterChart } from 'echarts/charts';
import { SVGRenderer } from 'echarts/renderers';
import { GridComponent, MarkLineComponent, TooltipComponent } from 'echarts/components';
import StudiesDialog from '@/components/explore/StudiesDialog.vue';
import { initOptions, keyLabel, updateOptions } from '@/components/plots/charts';
import { useChartFormat } from '@/composables/useChartFormat';
import type { ExploreBucket } from '@/models';

use([SVGRenderer, ScatterChart, LineChart, GridComponent, MarkLineComponent, TooltipComponent]);

interface Props {
  /** the split dimension, for the group names */
  dimension: string;
  buckets: ExploreBucket[];
  method: 'pearson' | 'spearman';
  /** the pair, the title of the study list before the group */
  title: string;
  /** the scatter of one group */
  optionOf: (bucket: ExploreBucket) => EChartsOption;
  /** the counts of one group, after its studies */
  factsOf: (bucket: ExploreBucket) => string[];
  /** header of the column of the points of each study in the study list */
  pointsLabel?: string | undefined;
  /** height of each small chart */
  height?: number;
}

const props = withDefaults(defineProps<Props>(), {
  pointsLabel: undefined,
  height: 180,
});
const { t } = useI18n();
const { describeWithin } = useChartFormat();

const panels = computed(() =>
  props.buckets.map((bucket, i) => {
    const key = bucket.key[0] ?? null;
    const r = bucket.fit?.r;
    return {
      // keys are unique, null aside
      id: key ?? `null-${i}`,
      label: key === null ? t('plots.not_recorded') : keyLabel(props.dimension, key),
      bucket,
      enough: typeof r === 'number',
      r: typeof r === 'number' ? `r = ${r.toFixed(2)}` : t('plots.too_little_data'),
      studies: bucket.n_studies === undefined ? '' : t('plots.studies_count', bucket.n_studies),
      facts: props.factsOf(bucket),
      within: describeWithin(bucket.within),
      option: props.optionOf(bucket),
    };
  }),
);
</script>

<style scoped lang="scss">
// the charts side by side, at most three to a row: a column is a third of the
// row, or 240px when a third is narrower, so a narrow screen gets fewer
// columns. Empty columns stay empty, so the charts keep one size.
.split-panels {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(100%, max(240px, calc((100% - 2 * 24px) / 3))), 1fr));
  gap: 32px 24px;
  width: 100%;
}

.split-panels__panel {
  min-width: 0;
}

.split-panels__head {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  justify-content: space-between;
  gap: 4px 12px;
  font-size: 0.9375rem;
  color: $grey-10;
}

.split-panels__group {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 500;
}

.split-panels__r {
  font-variant-numeric: tabular-nums;
}

.split-panels__r--none {
  font-size: 0.8125rem;
  color: $grey-8;
}

.split-panels__facts,
.split-panels__within {
  margin-top: 2px;
  font-size: 0.8125rem;
  line-height: 1.5;
  color: $grey-8;
}
</style>
