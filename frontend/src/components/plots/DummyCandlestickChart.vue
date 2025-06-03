<template>
  <div v-if="option.series" :style="`height: ${(height || 0) + 200}px;`">
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
  name: 'DummyCandlestickChart',
});
</script>
<script setup lang="ts">
import ECharts from 'vue-echarts';
import type { EChartsOption } from 'echarts';
import { use } from 'echarts/core';
import { CandlestickChart } from 'echarts/charts';
import { SVGRenderer } from 'echarts/renderers';
import { initOptions, updateOptions } from 'src/components/plots/charts';
import {
  TitleComponent,
  GridComponent,
  TooltipComponent,
} from 'echarts/components';

use([
  SVGRenderer,
  CandlestickChart,
  TitleComponent,
  GridComponent,
  TooltipComponent,
]);

interface Props {
  height?: number;
}

defineProps<Props>();

const chart = shallowRef(null);
const option = ref<EChartsOption>({});
const loading = ref(false);

onMounted(() => {
  loading.value = true;
  setTimeout(() => {
    initChartOptions();
  }, 100);
});

function initChartOptions() {
  option.value = {};
  buildOptions();
}

function buildOptions() {
  loading.value = true;
  // make boxplots
  const newOption: EChartsOption = {
    title: {
      text: 'Candlestick Chart Example',
    },
    xAxis: {
      data: ['2017-10-24', '2017-10-25', '2017-10-26', '2017-10-27']
    },
    yAxis: {},
    series: [
      {
        type: 'candlestick',
        data: [
          [20, 34, 10, 38],
          [40, 35, 30, 50],
          [31, 38, 33, 44],
          [38, 15, 5, 42]
        ]
      }
    ]
  };
  option.value = newOption;
  loading.value = false;
}
</script>
