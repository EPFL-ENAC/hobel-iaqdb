<template>
  <q-page>
    <div class="grid">
      <div>
        <q-tabs
          v-model="tab"
          inline-label
          dense
          class="text-grey"
          active-color="secondary"
          indicator-color="secondary"
          align="justify"
          @update:model-value="onTabChange"
        >
          <q-tab name="map" icon="map" :label="$t('buildings')" />
          <q-tab name="list" icon="list" :label="$t('studies')" />
        </q-tabs>
        <q-separator />
      </div>
      <div>
        <maplibre-map
          v-show="mapStore.showMap"
          position
          geocoder
          :zoom="2"
          @map:loaded="onMapLoaded"
          style="
            position: absolute;
            top: 37px;
            bottom: 0;
            width: 100%;
            z-index: 0;
          "
        />
        <study-list v-show="!mapStore.showMap" />
      </div>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import MaplibreMap from 'components/MaplibreMap.vue';
import StudyList from 'src/components/StudyList.vue';
import { Map } from 'maplibre-gl';

const tab = ref('map');
const mapStore = useMapStore();
const filtersStore = useFiltersStore();

onMounted(() => {
  if (!mapStore.showMap) {
    tab.value = 'list';
  } else {
    tab.value = 'map';
    // delay showing the map until the map store is initialized
    // this is necessary to avoid flickering when the map is loaded
    setTimeout(() => {
        mapStore.showMap = true;
    }, 100);
  }
});

watch(
  () => filtersStore.updates,
  () => {
    mapStore.applyFilters(filtersStore.asParams());
  },
);

function onMapLoaded(map: Map) {
  mapStore.initLayers(map).then(() => {
    mapStore.applyFilters(filtersStore.asParams());
  });
}

function onTabChange(newTab: string) {
  mapStore.showMap = newTab === 'map';
  //if (showMap.value) {
  //  mapStore.applyFilters(filtersStore.asParams());
  //}
}
</script>

<style scoped>
.grid {
  display: grid;
  grid-template-rows: auto 1fr;
  height: 100%;
}
</style>