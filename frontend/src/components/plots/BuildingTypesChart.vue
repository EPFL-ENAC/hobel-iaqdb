<template>
  <div v-if="option.series" :style="`height: ${(height || 0) + 150}px;`">
    <e-charts
      ref="chart"
      autoresize
      :init-options="initOptions"
      :option="option"
      :update-options="updateOptions"
      class="q-ma-sm"
      :loading="loading"
    />
  </div>
</template>

<script lang="ts">
export default defineComponent({
  name: 'BuildingTypesChart',
});
</script>
<script setup lang="ts">
import {
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
  TitleComponent,
  TooltipComponent,
} from 'echarts/components';
import { buildingTypeOptions } from 'src/utils/options';

use([
  SVGRenderer,
  TreemapChart,
  TitleComponent,
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
    title: {
      text: 'Building Types',
      left: 'center',
      textStyle: {
        fontSize: 12,
      },
    },
    tooltip: {
      trigger: 'item',
    },
    series: [
      {
        type: 'treemap',
        height: '60%',
        data: Object.entries(counts.value).map(([name, value]) => ({
          name: buildingTypeOptions.find((opt) => opt.value === name)?.label || name,
          value,
        })),
        label: {
          show: true,
          formatter: '{b}: {c}',
        },
      },
    ],
  };
  console.log(newOption);
  option.value = newOption;
  loading.value = false;
}
</script>
