<template>
  <q-page class="row items-center justify-evenly">
    <maplibre-map
      position
      geocoder
      :zoom="2"
      @map:loaded="onMapLoaded" />
  </q-page>
</template>

<script setup lang="ts">
import MaplibreMap from 'components/MaplibreMap.vue';
import { Map } from 'maplibre-gl';

const mapStore = useMapStore();
const filtersStore = useFiltersStore();

watch(() => filtersStore.updates, () => {
  mapStore.applyFilters(filtersStore.asParams());
});

function onMapLoaded(map: Map) {
  mapStore.initLayers(map).then(() => {
    mapStore.applyFilters(filtersStore.asParams());
  });
}

</script>
