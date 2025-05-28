<template>
  <div>
    <BuildingTypesChart :features="features" class="q-mb-md"/>
    <BuildingCountriesChart :features="features" />
  </div>
</template>

<script lang="ts">
export default defineComponent({
  name: 'PlotsDrawer',
});
</script>
<script setup lang="ts">
import {
  Feature,
  GeoJsonProperties,
  Geometry,
} from 'geojson';
import BuildingTypesChart from 'src/components/plots/BuildingTypesChart.vue';
import BuildingCountriesChart from 'src/components/plots/BuildingCountriesChart.vue';
import type { BuildingsLayerManager } from 'src/layers/buildings';

const mapStore = useMapStore();

const features = ref<Feature<Geometry, GeoJsonProperties>[]>([]);

watch(
  () => mapStore.filtersApplied,
  () => {
    console.log('Filters updated, fetching buildings...');
    const manager = mapStore.getLayerManager('buildings') as BuildingsLayerManager;
    if (manager) {
      features.value = manager.filteredData ? [...manager.filteredData.features] : [];
      
    }
  },
  { immediate: true }
);


</script>
