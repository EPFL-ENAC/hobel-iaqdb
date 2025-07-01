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

<script setup lang="ts">
import ECharts from 'vue-echarts';
import type { EChartsOption } from 'echarts';
import { use } from 'echarts/core';
import { BarChart } from 'echarts/charts';
import { SVGRenderer } from 'echarts/renderers';
import { initOptions, updateOptions } from 'src/components/plots/charts';
import {
  TitleComponent,
  GridComponent,
  TooltipComponent,
} from 'echarts/components';

use([
  SVGRenderer,
  BarChart,
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
  const months = [
    'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
  ];

  loading.value = true;
  const xAxisData = [];
  const data1 = [];
  const data2 = [];
  for (var i = 0; i < 12; i++) {
    xAxisData.push(months[i]);
    data1.push((Math.sin(i / 5) * (i / 5 - 10) + i / 6) * 5);
    data2.push((Math.cos(i / 5) * (i / 5 - 10) + i / 6) * 5);
  }
  const newOption: EChartsOption = {
    title: {
      text: 'Bar Chart Example',
    },
    legend: {
      data: ['bar', 'bar2']
    },
    toolbox: {
      // y: 'bottom',
      feature: {
        magicType: {
          type: ['stack']
        },
        dataView: {},
        saveAsImage: {
          pixelRatio: 2
        }
      }
    },
    tooltip: {},
    xAxis: {
      data: xAxisData,
      splitLine: {
        show: false
      }
    },
    yAxis: [{
      name: 'Concentration'
    }],
    series: [
      {
        name: 'bar',
        type: 'bar',
        data: data1,
        emphasis: {
          focus: 'series'
        },
        animationDelay: function (idx) {
          return idx * 10;
        }
      },
      {
        name: 'bar2',
        type: 'bar',
        data: data2,
        emphasis: {
          focus: 'series'
        },
        animationDelay: function (idx) {
          return idx * 10 + 100;
        }
      }
    ],
    animationEasing: 'elasticOut',
    animationDelayUpdate: function (idx) {
      return idx * 5;
    }
  };
  option.value = newOption;
  loading.value = false;
}
</script>
