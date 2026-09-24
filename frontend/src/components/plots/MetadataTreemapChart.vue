<template>
  <div>
    <div v-if="error" class="text-negative text-caption q-ml-md">{{ t('plots.error') }}: {{ error }}</div>
    <div v-else-if="empty" class="text-grey text-caption q-ml-md">{{ t('plots.no_data') }}</div>
    <div v-else-if="option.series" :style="`height: ${(height || 0) + 50}px;`">
      <e-charts
        ref="chart"
        autoresize
        :init-options="initOptions"
        :option="option"
        :update-options="updateOptions"
        class="q-mr-sm"
        :loading="loading"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import ECharts from 'vue-echarts';
import type { EChartsOption } from 'echarts';
import { use } from 'echarts/core';
import { TreemapChart } from 'echarts/charts';
import { SVGRenderer } from 'echarts/renderers';
import { TooltipComponent } from 'echarts/components';
import Gradient from 'javascript-color-gradient';
import { initOptions, toSeries, updateOptions } from '@/components/plots/charts';
import { exploreFilter } from '@/api/explore';
import { useExploreQuery } from '@/composables/useExploreQuery';
import type { ExploreEntity, ExploreParams } from '@/models';
import type { OptionItem } from '@/utils/options';

use([SVGRenderer, TreemapChart, TooltipComponent]);

interface Props {
  /** catalog entity counted per key */
  entity: ExploreEntity;
  /** dimension key from /stats/schema */
  by: string;
  /** value -> label of the dimension keys */
  options: OptionItem[];
  /** gradient ends */
  colors: [string, string];
  height?: number;
}

const props = defineProps<Props>();
const { t } = useI18n();
const mapStore = useMapStore();

const chart = shallowRef(null);
const option = ref<EChartsOption>({});

// re-query whenever the map filters are applied
const params = computed<ExploreParams>(() => {
  void mapStore.filtersApplied;
  return { entity: props.entity, by: [props.by], filter: exploreFilter() };
});
const { result, loading, error, empty } = useExploreQuery('metadata', () => params.value);

const gradientArray = computed(() =>
  new Gradient().setColorGradient(props.colors[0], props.colors[1]).setMidpoint(Math.max(props.options.length, 10)).getColors(),
);

watch(result, (value) => {
  if (!value) {
    option.value = {};
    return;
  }
  const [series] = toSeries(value);
  option.value = {
    tooltip: { trigger: 'item' },
    series: [
      {
        type: 'treemap',
        height: '90%',
        width: '90%',
        data: (series?.data || []).map((point) => ({
          name: point.key === null ? t('plots.unknown') : props.options.find((opt) => opt.value === point.key)?.label || point.key,
          value: point.value,
        })),
        label: { show: true, formatter: '{b}' },
        breadcrumb: { show: false },
      },
    ],
    color: gradientArray.value,
  };
});
</script>
