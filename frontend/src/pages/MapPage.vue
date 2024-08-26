<template>
  <q-page>
    <maplibre-map
      position
      geocoder
      :zoom="2"
      @map:loaded="onMapLoaded"
      style="
        position: absolute;
        top: 0;
        bottom: 0;
        height: 100%;
        width: 100%;
        z-index: 0;
      "
    />
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
