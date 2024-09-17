<template>
  <q-list>
    <q-item-label header>
      <span class="text-h6">
        <q-icon name="filter_alt" class="q-pb-xs"/>
        <span class="q-ml-sm">{{ $t('filters') }}</span>
      </span>
      <q-btn
        flat
        no-caps
        color="primary"
        size="12px"
        icon="restart_alt"
        :label="$t('reset_filters')"
        @click="onResetFilters" 
        class="q-mt-none q-mr-lg q-pl-xs q-pr-xs float-right "/>
    </q-item-label>
    <q-item>
      <q-item-section>
        <div class="text-grey-8">{{ $t('timeframe') }}</div>
        <q-range
          v-model="timeframe"
          :min="2000"
          :max="2025"
          :step="1"
          label
          snap
          color="primary"
          class="q-pr-sm"
        />
        <div class="text-hint">{{ $t('timeframe_help') }}</div>
        <q-select
          v-model="buildingTypes"
          :options="buildingTypeOptions"
          :label="$t('study.building.type')"
          :hint="$t('study.building.type_hint')"
          multiple
          use-chips
          emit-value
          map-options
          clearable
          dense
          @update:model-value="onUpdatedFilter"
        />
        <q-select
          v-model="populations"
          :options="populationOptions"
          :label="$t('study.building.population')"
          :hint="$t('study.building.population_hint')"
          multiple
          use-chips
          emit-value
          map-options
          clearable
          dense
          @update:model-value="onUpdatedFilter"
        />
        <q-select
          v-model="outdoorEnvs"
          :options="outdoorEnvOptions"
          :label="$t('study.building.outdoor_env')"
          :hint="$t('study.building.outdoor_env_hint')"
          multiple
          use-chips
          emit-value
          map-options
          clearable
          dense
          @update:model-value="onUpdatedFilter"
        />
        <q-select
          v-model="filtersStore.climateZones"
          :options="climateOptions"
          :label="$t('climate_zones')"
          :hint="$t('climate_zones_hint')"
          multiple
          use-chips
          emit-value
          clearable
          dense
          @update:model-value="onUpdatedFilter"
        />
        <div class="q-mt-md text-grey-8">{{ $t('altitudes') }}</div>
        <q-range
          v-model="filtersStore.altitudes"
          :min="0"
          :max="2500"
          :step="100"
          label
          snap
          color="primary"
          @change="onUpdatedFilter"
          class="q-pr-sm"
        />
        <div class="text-hint">{{ $t('altitudes_help') }}</div>
        <q-select
          v-model="filtersStore.ventilations"
          :options="ventilationTypeOptions"
          :label="$t('ventilations')"
          :hint="$t('ventilations_hint')"
          multiple
          use-chips
          emit-value
          map-options
          clearable
          dense
          @update:model-value="onUpdatedFilter"
        />
        <q-select
          v-model="vocs"
          :options="vocOptions"
          :label="$t('voc')"
          :hint="$t('voc_hint')"
          multiple
          use-chips
          emit-value
          map-options
          clearable
          dense
          @update:model-value="onUpdatedFilter"
        />
      </q-item-section>
    </q-item>

    <template v-if="isMapPage">
      <q-item-label header class="text-h6">
        <q-icon name="layers" class="q-pb-xs"/>
        <span class="q-ml-sm">{{ $t('layers') }}</span>
      </q-item-label>
      <q-item
        v-for="layer in mapStore.layerSelections"
        :key="layer.id"
        class="q-pl-sm q-pr-sm"
      >
        <q-item-section>
          <q-checkbox
            v-model="layer.visible"
            :label="$t(`layer.${layer.id}`)" 
            @click="onToggleLayer(layer.id)"
          />
        </q-item-section> 
        <q-item-section avatar>
          <q-btn 
            flat
            round
            icon="help_outline"
            @click="helpStore.toggleHelp(layer.id)"
          />
        </q-item-section>
      </q-item>
    
      <q-item-label header class="text-h6">
        <q-icon name="info" class="q-pb-xs"/>
        <span class="q-ml-sm">{{ $t('legends') }}</span>
      </q-item-label>
      <q-item-label>
        <span class="q-ml-md">{{ $t('number_of_buildings') }}</span>
      </q-item-label>
      <q-item v-for="cluster in clusterColors" :key="cluster.color">
        <q-item-section avatar>
          <q-avatar :color="cluster.color" text-color="black" />
        </q-item-section>
        <q-item-section>{{ $t(cluster.label) }}</q-item-section>
      </q-item>
      <q-item-label class=" q-mt-md">
        <span class="q-ml-md">{{ $t('climate_zones') }}</span>
      </q-item-label>
      <q-item>
        <div class="row">
          <div v-for="zone in climateZonesColors" :key="zone.color" :title="zone.title" class="col-4">
            <q-icon name="square" :style="`color: ${zone.color}`" size="sm"/>
            <span class="q-pl-md">{{ zone.label }}</span>
          </div>
        </div>
      </q-item>
    </template>
  </q-list>
</template>

<script lang="ts">
export default defineComponent({
  name: 'LayersDrawer',
});
</script>
<script setup lang="ts">
import { climateOptions, ventilationOptions, buildingTypeOptions, populationOptions, outdoorEnvOptions, vocOptions } from 'src/utils/options';

const mapStore = useMapStore();
const helpStore = useHelpStore();
const filtersStore = useFiltersStore();
const route = useRoute();

// mock filters
const timeframe = ref({
  min: 2000,
  max: 2025
});
const buildingTypes = ref([]);
const populations = ref([]);
const outdoorEnvs = ref([]);
const vocs = ref([]);

const isMapPage = computed(() => route.path === '/map')

const clusterColors = [
  {
    color: 'cyan-5',
    label: '< 10'
  },  
  {
    color: 'yellow-6',
    label: '1 - 20'
  },
  {
    color: 'pink-3',
    label: '> 20'
  }
]

const climateZonesColors = [
  { color: '#0000fe', label: 'Af', title: 'Tropical, rainforest' },
  { color: '#0077fe', label: 'Am', title: 'Tropical, monsoon' },
  { color: '#46aafa', label: 'Aw', title: 'Tropical, savannah' },
  { color: '#ff0000', label: 'BWh', title: 'Arid, desert, hot' },
  { color: '#ff9696', label: 'BWk', title: 'Arid, desert, cold' },
  { color: '#f4a400', label: 'BSh', title: 'Arid, steppe, hot' },
  { color: '#fedb63', label: 'BSk', title: 'Arid, steppe, cold' },
  { color: '#ffff00', label: 'Csa', title: 'Temperate, dry summer, hot summer' },
  { color: '#c8c800', label: 'Csb', title: 'Temperate, dry summer, warm summer' },
  { color: '#959500', label: 'Csc', title: 'Temperate, dry summer, cold summer' },
  { color: '#96ff96', label: 'Cwa', title: 'Temperate, dry winter, hot summer' },
  { color: '#63c763', label: 'Cwb', title: 'Temperate, dry winter, warm summer' },
  { color: '#319531', label: 'Cwc', title: 'Temperate, dry winter, cold summer' },
  { color: '#c8ff50', label: 'Cfa', title: 'Temperate, no dry season, hot summer' },
  { color: '#63fe31', label: 'Cfb', title: 'Temperate, no dry season, warm summer' },
  { color: '#32c800', label: 'Cfc', title: 'Temperate, no dry season, cold summer' },
  { color: '#fe00fe', label: 'Dsa', title: 'Cold, dry summer, hot summer' },
  { color: '#c800c8', label: 'Dsb', title: 'Cold, dry summer, warm summer' },
  { color: '#963196', label: 'Dsc', title: 'Cold, dry summer, cold summer' },
  { color: '#966496', label: 'Dsd', title: 'Cold, dry summer, very cold winter' },
  { color: '#aaafff', label: 'Dwa', title: 'Cold, dry winter, hot summer' },
  { color: '#5977db', label: 'Dwb', title: 'Cold, dry winter, warm summer' },
  { color: '#4b50b4', label: 'Dwc', title: 'Cold, dry winter, cold summer' },
  { color: '#320087', label: 'Dwd', title: 'Cold, dry winter, very cold winter' },
  { color: '#00ffff', label: 'Dfa', title: 'Cold, no dry season, hot summer' },
  { color: '#37c8ff', label: 'Dfb', title: 'Cold, no dry season, warm summer' },
  { color: '#007d7d', label: 'Dfc', title: 'Cold, no dry season, cold summer' },
  { color: '#00455e', label: 'Dfd', title: 'Cold, no dry season, very cold winter' },
  { color: '#b3b3b3', label: 'ET', title: 'Polar, tundra' },
  { color: '#656565', label: 'EF', title: 'Polar, frost' },
]

function onToggleLayer(layerId: string) {
  mapStore.applyLayerVisibility(layerId);
  onUpdatedFilter();
}

function onResetFilters() {
  filtersStore.reset();
  // mock filters
  timeframe.value = {
    min: 2000,
    max: 2025
  };
  buildingTypes.value = [];
  populations.value = [];
  outdoorEnvs.value = [];
  vocs.value = [];
  onUpdatedFilter();
}

function onUpdatedFilter() {
  filtersStore.notifyUpdate();
}
</script>