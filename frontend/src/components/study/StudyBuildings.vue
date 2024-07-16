<template>
  <div>
    <maplibre-map
      position
      :zoom="2"
      height="400px"
      width="100%"
      @map:loaded="onMapLoaded"
      @map:click="onMapClick" />
    <q-table
      flat
      :rows="buildings"
      :columns="columms"
      v-model:pagination="pagination"
      row-key="_id"
      >
      <template v-slot:body-cell-city="props">
        <q-td :props="props">
          <span :title="`${props.row.location[0]}, ${props.row.location[1]}`">
            {{ props.row.city }}, {{ props.row.country }}
          </span>
        </q-td>
      </template>
      <template v-slot:body-cell-climate_zone="props">
        <q-td :props="props">
          <q-badge :label="props.row.climate_zone" />
        </q-td>
      </template>
    </q-table>
  </div>
</template>


<script lang="ts">
export default defineComponent({
  name: 'StudyBuildings',
});
</script>
<script setup lang="ts">
import MaplibreMap from 'src/components/MaplibreMap.vue';
import { Map } from 'maplibre-gl';

const catalogStore = useCatalogStore();
const mapStore = useMapStore();

const pagination = ref({
  sortBy: '_id',
  descending: false,
  page: 1,
  rowsPerPage: 10,
  rowsNumber: 0,
});

const buildings = computed(() => catalogStore.buildings);

const columms = computed(() => {
  return [
    {
      name: 'identifier',
      label: 'ID',
      align: 'left',
      field: 'identifier'
    },
    {
      name: 'city',
      label: 'City',
      align: 'left',
      field: 'city',
    },
    {
      name: 'climate_zone',
      label: 'Climate zone',
      align: 'left',
      field: 'climate_zone'
    },
    {
      name: 'outdoor_env',
      label: 'Outdoor env.',
      align: 'left',
      field: 'outdoor_env'
    },
    {
      name: 'renovation_year',
      label: 'Renovation year',
      align: 'left',
      field: 'renovation_year'
    },
  ];
})

function onMapLoaded(map: Map) {
  mapStore.initLayers(map).then(() => {
    mapStore.applyFilters({
      study_ids: [catalogStore.study?._id]
    });
  });
}
</script>