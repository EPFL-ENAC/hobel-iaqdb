<template>
  <div>
    <q-list>
      <q-item-label header class="q-pt-none">
        <span class="text-h6">
          <q-icon name="domain" class="q-pb-xs" />
          <span class="q-ml-sm">{{ t('plots.buildings_overview') }}</span>
        </span>
      </q-item-label>
    </q-list>
    <div class="text-caption text-bold q-ml-md">{{ t('plots.building_type') }}</div>
    <BuildingTypesChart :features="features" />
    <div class="text-caption text-bold q-ml-md q-mt-sm">{{ t('plots.building_country') }}</div>
    <BuildingCountriesChart :features="features" />
    <div class="text-caption text-bold q-ml-md q-mt-sm">{{ t('plots.building_ventilation') }}</div>
    <BuildingMechanicalVentilationsChart :features="features" />
    <q-list>
      <q-item-label header>
        <span class="text-h6">
          <q-icon name="living" class="q-pb-xs" />
          <span class="q-ml-sm">{{ t('plots.spaces_overview') }}</span>
        </span>
      </q-item-label>
    </q-list>
    <div class="text-caption text-bold q-ml-md q-mt-sm">{{ t('plots.space_type') }}</div>
    <SpaceTypesChart />
    <div class="text-caption text-bold q-ml-md q-mt-sm">{{ t('plots.space_ventilation_type') }}</div>
    <SpaceMechanicalVentilationsChart />
  </div>
</template>

<script setup lang="ts">
import type {
  Feature,
  GeoJsonProperties,
  Geometry,
} from 'geojson';
import BuildingTypesChart from 'src/components/plots/BuildingTypesChart.vue';
import BuildingCountriesChart from 'src/components/plots/BuildingCountriesChart.vue';
import BuildingMechanicalVentilationsChart from 'src/components/plots/BuildingMechanicalVentilationsChart.vue';
import SpaceTypesChart from 'src/components/plots/SpaceTypesChart.vue';
import SpaceMechanicalVentilationsChart from 'src/components/plots/SpaceMechanicalVentilationsChart.vue';
import type { BuildingsLayerManager } from 'src/layers/buildings';


const { t } = useI18n();
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
