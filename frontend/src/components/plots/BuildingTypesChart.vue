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
import type {
  Feature,
  GeoJsonProperties,
  Geometry,
} from 'geojson';
import ECharts from 'vue-echarts';
import type { EChartsOption } from 'echarts';
import { use } from 'echarts/core';
import { TreemapChart } from 'echarts/charts';
import { SVGRenderer } from 'echarts/renderers';
import { initOptions, updateOptions } from 'src/components/plots/charts';
import {
  TooltipComponent,
} from 'echarts/components';
import { buildingTypeOptions } from 'src/utils/options';
import Gradient from 'javascript-color-gradient'

use([
  SVGRenderer,
  TreemapChart,
  TooltipComponent,
]);

interface Props {
  features?: Feature<Geometry, GeoJsonProperties>[];
  height?: number;
}

const props = defineProps<Props>();

const chart = shallowRef(null);
const option = ref<EChartsOption>({});
const loading = ref(false);

const counts = computed(() => {
  return props.features?.reduce((acc, feature) => {
    const type = feature.properties?.building_type;
    acc[type] = (acc[type] || 0) + 1;
    return acc;
  }, {} as { [key: string]: number }) || {};
});

const gradientArray = new Gradient()
  .setColorGradient('#00441b', '#b7e2b1')
  .setMidpoint(buildingTypeOptions.length)
  .getColors();

watch(
  () => props.features,
  () => {
    initChartOptions();
  }
);

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
        data: Object.entries(counts.value).map(([name, value]) => ({
          name: buildingTypeOptions.find((opt) => opt.value === name)?.label || name,
          value,
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
