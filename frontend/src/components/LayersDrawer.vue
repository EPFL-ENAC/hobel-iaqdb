<template>
  <q-list>
    <q-item-label header>
      <span class="text-h6">
        <q-icon name="filter_alt" class="q-pb-xs" />
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
        class="q-mt-none q-mr-lg q-pl-xs q-pr-xs float-right"
      />
    </q-item-label>
    <q-item>
      <q-item-section>
        <q-tabs
          v-model="tab"
          dense
          class="text-grey filters"
          no-caps
          active-color="secondary"
          indicator-color="secondary"
          align="justify"
          narrow-indicator
        >
          <q-tab name="pollutants" :label="$t('pollutants')"/>
          <q-tab name="geography" :label="$t('geography')" />
          <q-tab name="buildings" :label="$t('buildings')" />
        </q-tabs>
        <q-separator />
        <q-tab-panels v-model="tab" animated>
          <q-tab-panel name="pollutants" class="q-pa-none">
            <q-select
              v-model="particles"
              :options="particleOptions"
              :label="$t('particles')"
              multiple
              use-chips
              emit-value
              map-options
              dense
              @update:model-value="onUpdatedFilter"
            />
            <q-select
              v-model="vocs"
              :options="vocOptions"
              :label="$t('voc')"
              multiple
              use-chips
              emit-value
              map-options
              dense
              @update:model-value="onUpdatedFilter"
            />
            <q-select
              v-model="inorganicGases"
              :options="inorganicGasesOptions"
              :label="$t('inorganic_gases')"
              multiple
              use-chips
              emit-value
              map-options
              dense
              @update:model-value="onUpdatedFilter"
            />
            <q-select
              v-model="biocontaminants"
              :options="biocontaminantsOptions"
              :label="$t('biocontaminants')"
              multiple
              use-chips
              emit-value
              map-options
              dense
              @update:model-value="onUpdatedFilter"
            />
            <q-select
              v-model="otherPollutants"
              :options="otherPollutantsOptions"
              :label="$t('other_pollutants')"
              multiple
              use-chips
              emit-value
              map-options
              dense
              @update:model-value="onUpdatedFilter"
            />
          </q-tab-panel>
          <q-tab-panel name="geography" class="q-pa-none">
            <q-select
              v-model="filtersStore.countries"
              :options="studyCountries"
              :label="$t('countries')"
              multiple
              use-chips
              emit-value
              map-options
              dense
              @update:model-value="onUpdatedFilter"
            />
            <q-select
              v-model="filtersStore.cities"
              :options="studyCities"
              :label="$t('cities')"
              multiple
              use-chips
              emit-value
              map-options
              dense
              @update:model-value="onUpdatedFilter"
            />
            <div class="q-mt-md text-grey-8">{{ $t('altitudes') }}</div>
            <div class="q-pl-md q-pr-md">
              <q-range
                v-model="filtersStore.altitudes"
                :min="DEFAULT_ALTITUDES.min"
                :max="DEFAULT_ALTITUDES.max"
                :step="100"
                label
                snap
                color="primary"
                class="q-pr-sm"
                @change="onUpdatedFilter"
              />
            </div>
            <q-select
              v-model="filtersStore.climate_zones"
              :options="climateOptions"
              :label="$t('climate_zones')"
              :hint="$t('climate_zones_hint')"
              multiple
              use-chips
              emit-value
              dense
              @update:model-value="onUpdatedFilter"
            />
            
          </q-tab-panel>
          <q-tab-panel name="buildings" class="q-pa-none">
            <q-select
              v-model="filtersStore.building_types"
              :options="buildingTypeOptions"
              :label="$t('study.building.type')"
              multiple
              use-chips
              emit-value
              map-options
              dense
              @update:model-value="onUpdatedFilter"
            />
            <div class="q-mt-md text-grey-8">{{ $t('study.building.construction_year') }}</div>
            <div class="q-pl-md q-pr-md">
              <q-range
                v-model="filtersStore.construction_years"
                :min="DEFAULT_CONSTRUCTION_YEARS.min"
                :max="DEFAULT_CONSTRUCTION_YEARS.max"
                :step="1"
                label
                snap
                color="primary"
                class="q-pr-sm"
                @change="onUpdatedFilter"
              />
            </div>
            <q-select
              v-model="filtersStore.outdoor_envs"
              :options="outdoorEnvOptions"
              :label="$t('study.building.outdoor_env')"
              multiple
              use-chips
              emit-value
              map-options
              dense
              @update:model-value="onUpdatedFilter"
            />
            <q-select
              v-model="filtersStore.age_groups"
              :options="ageGroupOptions"
              :label="$t('study.building.age_group')"
              multiple
              use-chips
              emit-value
              map-options
              dense
              @update:model-value="onUpdatedFilter"
            />
            <q-select
              v-model="filtersStore.socioeconomic_status"
              :options="socioeconomicStatusOptions"
              :label="$t('study.building.socioeconomic_status')"
              multiple
              use-chips
              emit-value
              map-options
              dense
              @update:model-value="onUpdatedFilter"
            />
            <q-select
              v-model="filtersStore.mechanical_ventilation_types"
              :options="mechanicalVentilationTypeOptions"
              :label="$t('ventilations')"
              multiple
              use-chips
              emit-value
              map-options
              dense
              @update:model-value="onUpdatedFilter"
            />
          </q-tab-panel>
        </q-tab-panels>
      </q-item-section>
    </q-item>

    <template v-if="isMapPage">
      <q-item-label header class="text-h6">
        <q-icon name="info" class="q-pb-xs" />
        <span class="q-ml-sm">{{ $t('legends') }}</span>
      </q-item-label>
      <q-item-label>
        <span class="q-ml-md">{{ $t('studies') }}</span>
      </q-item-label>
      <q-item v-for="summary in studySummaries" :key="summary.id">
        <q-item-section avatar>
          <q-avatar size="xs" text-color="black" :style="`background-color: ${summary.color}`" />
        </q-item-section>
        <q-item-section :title="summary.name">{{ truncateString(summary.name, 30) }}</q-item-section>
      </q-item>
      <q-item-label>
        <span class="q-ml-md">{{ $t('number_of_buildings') }}</span>
      </q-item-label>
      <q-item v-for="cluster in clusterColors" :key="cluster.color">
        <q-item-section avatar>
          <q-avatar size="sm" :color="cluster.color" text-color="black" />
        </q-item-section>
        <q-item-section>{{ $t(cluster.label) }}</q-item-section>
      </q-item>
      <q-item-label class="q-mt-md">
        <span class="q-ml-md">{{ $t('climate_zones') }}</span>
      </q-item-label>
      <template v-for="layer in mapStore.layerSelections" :key="layer.id">
        <q-item
          v-if="layer.id === 'climate-zones'"
          class="q-pl-sm q-pr-sm"
        >
          <q-item-section>
            <q-checkbox
              v-model="layer.visible"
              :label="$t(`layer.show_${layer.id}`)"
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
      </template>
      <q-item>
        <div class="row">
          <div
            v-for="zone in climateZonesColors"
            :key="zone.color"
            :title="zone.title"
            class="col-4"
          >
            <q-icon name="square" :style="`color: ${zone.color}`" size="sm" />
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
import { DEFAULT_CONSTRUCTION_YEARS, DEFAULT_ALTITUDES } from 'src/stores/filters';
import {
  climateOptions,
  mechanicalVentilationTypeOptions,
  buildingTypeOptions,
  ageGroupOptions,
  socioeconomicStatusOptions,
  outdoorEnvOptions,
  vocOptions,
  particleOptions,
  inorganicGasesOptions,
  biocontaminantsOptions,
  otherPollutantsOptions,
  countryOptions,
} from 'src/utils/options';
import type { StudySummary } from 'src/models';
import { truncateString } from 'src/utils/strings';
import { fileURLToPath } from 'url';

const mapStore = useMapStore();
const catalogStore = useCatalogStore();
const helpStore = useHelpStore();
const filtersStore = useFiltersStore();
const route = useRoute();

const tab = ref('geography');
const particles = ref([]);
const inorganicGases = ref([]);
const biocontaminants = ref([]);
const otherPollutants = ref([]);
const vocs = ref([]);
const studySummaries = ref<StudySummary[]>([]);

const isMapPage = computed(() => route.path === '/map');

const studyCountries = computed(() => {
  return countryOptions.filter((country) => {
    return studySummaries.value.some((study) => study.countries.includes(country.value));
  });
});

const studyCities = computed(() => {
  return studySummaries.value.reduce((cities, study) => {
    // if some countries are selected, filter cities by those countries
    study.cities.forEach((city) => {
      if (!cities.includes(city) && (!filtersStore.countries?.length || filtersStore.countries.some((c) => city.endsWith(`, ${c}`)))) {
        cities.push(city);
      }
    });
    return cities;
  }, [] as string[]).sort((a, b) => a.localeCompare(b));
});


const clusterColors = [
  {
    color: 'cyan-5',
    label: '< 10',
  },
  {
    color: 'yellow-6',
    label: '1 - 20',
  },
  {
    color: 'pink-3',
    label: '> 20',
  },
];

const climateZonesColors = [
  { color: '#0000fe', label: 'Af', title: 'Tropical, rainforest' },
  { color: '#0077fe', label: 'Am', title: 'Tropical, monsoon' },
  { color: '#46aafa', label: 'Aw', title: 'Tropical, savannah' },
  { color: '#ff0000', label: 'BWh', title: 'Arid, desert, hot' },
  { color: '#ff9696', label: 'BWk', title: 'Arid, desert, cold' },
  { color: '#f4a400', label: 'BSh', title: 'Arid, steppe, hot' },
  { color: '#fedb63', label: 'BSk', title: 'Arid, steppe, cold' },
  {
    color: '#ffff00',
    label: 'Csa',
    title: 'Temperate, dry summer, hot summer',
  },
  {
    color: '#c8c800',
    label: 'Csb',
    title: 'Temperate, dry summer, warm summer',
  },
  {
    color: '#959500',
    label: 'Csc',
    title: 'Temperate, dry summer, cold summer',
  },
  {
    color: '#96ff96',
    label: 'Cwa',
    title: 'Temperate, dry winter, hot summer',
  },
  {
    color: '#63c763',
    label: 'Cwb',
    title: 'Temperate, dry winter, warm summer',
  },
  {
    color: '#319531',
    label: 'Cwc',
    title: 'Temperate, dry winter, cold summer',
  },
  {
    color: '#c8ff50',
    label: 'Cfa',
    title: 'Temperate, no dry season, hot summer',
  },
  {
    color: '#63fe31',
    label: 'Cfb',
    title: 'Temperate, no dry season, warm summer',
  },
  {
    color: '#32c800',
    label: 'Cfc',
    title: 'Temperate, no dry season, cold summer',
  },
  { color: '#fe00fe', label: 'Dsa', title: 'Cold, dry summer, hot summer' },
  { color: '#c800c8', label: 'Dsb', title: 'Cold, dry summer, warm summer' },
  { color: '#963196', label: 'Dsc', title: 'Cold, dry summer, cold summer' },
  {
    color: '#966496',
    label: 'Dsd',
    title: 'Cold, dry summer, very cold winter',
  },
  { color: '#aaafff', label: 'Dwa', title: 'Cold, dry winter, hot summer' },
  { color: '#5977db', label: 'Dwb', title: 'Cold, dry winter, warm summer' },
  { color: '#4b50b4', label: 'Dwc', title: 'Cold, dry winter, cold summer' },
  {
    color: '#320087',
    label: 'Dwd',
    title: 'Cold, dry winter, very cold winter',
  },
  { color: '#00ffff', label: 'Dfa', title: 'Cold, no dry season, hot summer' },
  { color: '#37c8ff', label: 'Dfb', title: 'Cold, no dry season, warm summer' },
  { color: '#007d7d', label: 'Dfc', title: 'Cold, no dry season, cold summer' },
  {
    color: '#00455e',
    label: 'Dfd',
    title: 'Cold, no dry season, very cold winter',
  },
  { color: '#b3b3b3', label: 'ET', title: 'Polar, tundra' },
  { color: '#656565', label: 'EF', title: 'Polar, frost' },
];

onMounted(() => {
  catalogStore.loadStudySummaries(0, 1000).then((res) => {
    studySummaries.value = res.data;
  });
});

function onToggleLayer(layerId: string) {
  mapStore.applyLayerVisibility(layerId);
  onUpdatedFilter();
}

function onResetFilters() {
  filtersStore.reset();
  vocs.value = [];
  particles.value = [];
  inorganicGases.value = [];
  biocontaminants.value = [];
  otherPollutants.value = [];
  onUpdatedFilter();
}

function onUpdatedFilter() {
  filtersStore.notifyUpdate();
}
</script>
