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
import type { EChartsOption, LineSeriesOption } from 'echarts';
import { use } from 'echarts/core';
import { LineChart } from 'echarts/charts';
import { SVGRenderer } from 'echarts/renderers';
import { initOptions, updateOptions } from 'src/components/plots/charts';
import {
  TitleComponent,
  GridComponent,
  TooltipComponent,
} from 'echarts/components';

use([
  SVGRenderer,
  LineChart,
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
  const names = [
  'Orange',
  'Tomato',
  'Apple',
  'Sakana',
  'Banana',
  'Iwashi',
  'Snappy Fish',
  'Lemon',
  'Pasta'
];
const years = ['2001', '2002', '2003', '2004', '2005', '2006'];
const shuffle = (array: unknown[]) => {
  let currentIndex = array.length;
  let randomIndex = 0;
  while (currentIndex > 0) {
    randomIndex = Math.floor(Math.random() * currentIndex);
    currentIndex--;
    [array[currentIndex], array[randomIndex]] = [
      array[randomIndex],
      array[currentIndex]
    ];
  }
  return array;
};
const generateRankingData = () => {
  const map = new Map();
  const defaultRanking = Array.from({ length: names.length }, (_, i) => i + 1);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  for (const _ of years) {
    const shuffleArray = shuffle(defaultRanking);
    names.forEach((name, i) => {
      map.set(name, (map.get(name) || []).concat(shuffleArray[i]));
    });
  }
  return map;
};
const generateSeriesList = () => {
  const seriesList: LineSeriesOption[] = [];
  const rankingMap = generateRankingData();
  rankingMap.forEach((data, name) => {
    const series = {
      name,
      symbolSize: 20,
      type: 'line',
      smooth: true,
      emphasis: {
        focus: 'series'
      },
      endLabel: {
        show: true,
        formatter: '{a}',
        distance: 20
      },
      lineStyle: {
        width: 4
      },
      data
    };
    seriesList.push(series as LineSeriesOption);
  });
  return seriesList;
};

const newOption: EChartsOption = {
    title: {
      text: 'Bump Chart Example',
    },
    tooltip: {
      trigger: 'item'
    },
    grid: {
      left: 30,
      right: 110,
      bottom: 30,
      containLabel: true
    },
    toolbox: {
      feature: {
        saveAsImage: {}
      }
    },
    xAxis: {
      type: 'category',
      splitLine: {
        show: true
      },
      axisLabel: {
        margin: 30,
        fontSize: 16
      },
      boundaryGap: false,
      data: years
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        margin: 30,
        fontSize: 16,
        formatter: '#{value}'
      },
      inverse: true,
      interval: 1,
      min: 1,
      max: names.length
    },
    series: generateSeriesList()
  };
  option.value = newOption;
  loading.value = false;
}
</script>
