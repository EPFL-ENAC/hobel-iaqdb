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
import { spaceTypeOptions } from 'src/utils/options';
import Gradient from 'javascript-color-gradient'

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

// ["#ffffcc","#ffefa5","#fedc7f","#febf5b","#fd9d43","#fc7034","#f23d26","#d91620","#b40325","#800026"]
const gradientArray = new Gradient()
  .setColorGradient('#800026', '#ffefa5')
  .setMidpoint(10)
  .getColors();

function initCounts() {
  catalogStore.countSpaces('type', true).then((results) => {
    counts.value = results.counts || [];
    initChartOptions();
  }).catch((error) => {
    console.error('Error fetching space type counts:', error);
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
          name: spaceTypeOptions.find((opt) => opt.value === entry.value)?.label || entry.value || 'NA',
          value: entry.count,
        })),
        label: {
          show: true,
          formatter: '{b}',
        },
        breadcrumb: {
          show: false
        }
      },
    ],
    color: gradientArray,
  };
  option.value = newOption;
  loading.value = false;
}
</script>
