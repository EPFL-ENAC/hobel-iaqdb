<template>
  <div v-if="option.series" :style="`height: ${(height || 0) + 50}px;`">
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
</template>

<script lang="ts">
export default defineComponent({
  name: 'BuildingMechanicalVentilationsChart',
});
</script>
<script setup lang="ts">
import type { GroupByCount } from 'src/models';
import ECharts from 'vue-echarts';
import type { EChartsOption } from 'echarts';
import { use } from 'echarts/core';
import { TreemapChart } from 'echarts/charts';
import { SVGRenderer } from 'echarts/renderers';
import { initOptions, updateOptions } from 'src/components/plots/charts';
import {
  TooltipComponent,
} from 'echarts/components';
import { mechanicalVentilationTypeOptions } from 'src/utils/options';

use([
  SVGRenderer,
  TreemapChart,
  TooltipComponent,
]);

const mapStore = useMapStore();
const catalogStore = useCatalogStore();

interface Props {
  height?: number;
}

defineProps<Props>();

const chart = shallowRef(null);
const option = ref<EChartsOption>({});
const loading = ref(false);
const counts = ref<GroupByCount[]>([]);

onMounted(() => {
  initCounts();
});

watch(
  () => mapStore.filtersApplied,
  () => {
    initCounts();
  }
);

function initCounts() {
  catalogStore.countSpaces('mechanical_ventilation_type', false).then((results) => {
    counts.value = results.counts || [];
    initChartOptions();
  }).catch((error) => {
    console.error('Error fetching mechanical ventilation counts:', error);
  });
}

function initChartOptions() {
  option.value = {};
  buildOptions();
}

function buildOptions() {
  loading.value = true;
  // make treemap
  const newOption: EChartsOption = {
    tooltip: {
      trigger: 'item',
    },
    series: [
      {
        type: 'treemap',
        height: '90%',
        width: '90%',
        data: counts.value.map((entry) => ({
          name: mechanicalVentilationTypeOptions.find((opt) => opt.value === entry.value)?.label || entry.value || 'NA',
          value: entry.count,
        })),
        label: {
          show: true,
          formatter: '{b}: {c}',
        },
        breadcrumb: {
          show: false
        }
      },
    ],
  };
  option.value = newOption;
  loading.value = false;
}
</script>
