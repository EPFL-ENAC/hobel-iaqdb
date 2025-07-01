<template>
  <div>
    <div v-if="catalogStore.study && props.showMap">
      <maplibre-map
        position
        :zoom="2"
        :max-zoom="16"
        height="400px"
        width="100%"
        @map:loaded="onMapLoaded"
      />
    </div>
    <q-table
      flat
      responsive
      :rows="buildings"
      :columns="columms"
      v-model:pagination="pagination"
      row-key="id"
    >
      <template v-slot:header="props">
        <q-tr :props="props">
          <q-th auto-width />
          <q-th
            v-for="col in props.cols"
            :key="col.name"
            :props="props"
          >
            {{ col.label }}
          </q-th>
        </q-tr>
      </template>

      <template v-slot:body="props">
        <q-tr :props="props">
          <q-td auto-width>
            <q-btn flat size="sm" color="accent" round dense @click="props.expand = !props.expand" :icon="props.expand ? 'remove' : 'add'" />
          </q-td>
          <q-td
            v-for="col in props.cols"
            :key="col.name"
            :props="props"
          >
            {{ col.value }}
          </q-td>
        </q-tr>
        <q-tr v-show="props.expand" :props="props">
          <q-td colspan="100%">
            <pre class="text-left">{{ props.row.spaces }}</pre>
          </q-td>
        </q-tr>
      </template>

      <template v-slot:body-cell-city="props">
        <q-td :props="props">
          <span :title="`${props.row.long}, ${props.row.lat}`">
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

<script setup lang="ts">
import MaplibreMap from 'src/components/MaplibreMap.vue';
import { Map } from 'maplibre-gl';
import type { Building, Space } from 'src/models';
import { outdoorEnvOptions } from 'src/utils/options';

interface Props {
  showMap?: boolean;
}
const props = withDefaults(defineProps<Props>(), {
  showMap: false,
});

const catalogStore = useCatalogStore();
const mapStore = useMapStore();
const { t } = useI18n();

const pagination = ref({
  sortBy: 'identifier',
  descending: false,
  page: 1,
  rowsPerPage: 25,
});

const buildings = computed(() => catalogStore.buildings || []);

const columms = computed(() => {
  return [
    {
      name: 'identifier',
      label: 'ID',
      align: 'left',
      sortable: true,
      field: 'identifier',
    },
    {
      name: 'city',
      label: t('study.building.city'),
      align: 'left',
      sortable: true,
      field: 'city',
    },
    {
      name: 'climate_zone',
      label: t('study.building.climate_zone'),
      align: 'left',
      sortable: true,
      field: 'climate_zone',
    },
    {
      name: 'outdoor_env',
      label: t('study.building.outdoor_env'),
      align: 'left',
      sortable: true,
      field: 'outdoor_env',
      format: (v: string) => {
        return outdoorEnvOptions.find((option) => option.value === v)?.label || v;
      },
    },
    {
      name: 'construction_renovation_years',
      label: t('study.building.construction_renovation_years'),
      align: 'left',
      sortable: true,
      field: (row: Building) => {
        return `${row.construction_year || '?'} ${row.renovation_year ? ' / ' + row.renovation_year : ''}`;
      },
    },
    {
      name: 'spaces',
      label: t('spaces'),
      align: 'left',
      sortable: true,
      field: 'spaces',
      format: (v: Space[]) => {
        return v?.length || 0;
      },
    },
  ];
});

function onMapLoaded(map: Map) {
  mapStore.initLayers(map).then(() => {
    if (catalogStore.study?.identifier) {
      mapStore.applyFilters({
        study_ids: [catalogStore.study?.identifier],
      });
    }
  });
}

</script>
