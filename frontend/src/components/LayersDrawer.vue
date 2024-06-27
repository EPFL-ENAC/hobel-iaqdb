<template>
  <q-list>
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
        class="q-mt-xs q-pl-xs q-pr-xs float-right "/>
    </q-item-label>
    <q-item>
      <q-item-section>
        <q-select
          v-model="filtersStore.climateZones"
          :options="climateOptions"
          :label="$t('climate_zones')"
          :hint="$t('climate_zones_hint')"
          multiple
          use-chips
          emit-value
          clearable
          @update:model-value="onUpdatedFilter"
          />
      </q-item-section>
    </q-item>
    <q-item>
      <q-item-section>
        <span>{{ $t('altitudes') }}</span>
        <q-range
          v-model="filtersStore.altitudes"
          :min="0"
          :max="2500"
          :step="100"
          label
          snap
          color="primary"
          @change="onUpdatedFilter"
        />
        <span class="text-help">{{ $t('altitudes_help') }}</span>
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
  </q-list>
</template>

<script lang="ts">
export default defineComponent({
  name: 'LayersDrawer',
});
</script>
<script setup lang="ts">
const mapStore = useMapStore();
const helpStore = useHelpStore();
const filtersStore = useFiltersStore();

const climateOptions = [
  { value: 'Af ', label: 'Tropical, rainforest',},
  { value: 'Am ', label: 'Tropical, monsoon',},
  { value: 'Aw ', label: 'Tropical, savannah',},
  { value: 'BWh', label: 'Arid, desert, hot',},
  { value: 'BWk', label: 'Arid, desert, cold',},
  { value: 'BSh', label: 'Arid, steppe, hot',},
  { value: 'BSk', label: 'Arid, steppe, cold',},
  { value: 'Csa', label: 'Temperate, dry summer, hot summer',},
  { value: 'Csb', label: 'Temperate, dry summer, warm summer',},
  { value: 'Csc', label: 'Temperate, dry summer, cold summer',},
  { value: 'Cwa', label: 'Temperate, dry winter, hot summer',},
  { value: 'Cwb', label: 'Temperate, dry winter, warm summer',},
  { value: 'Cwc', label: 'Temperate, dry winter, cold summer',},
  { value: 'Cfa', label: 'Temperate, no dry season, hot summer',},
  { value: 'Cfb', label: 'Temperate, no dry season, warm summer',},
  { value: 'Cfc', label: 'Temperate, no dry season, cold summer',},
  { value: 'Dsa', label: 'Cold, dry summer, hot summer',},
  { value: 'Dsb', label: 'Cold, dry summer, warm summer',},
  { value: 'Dsc', label: 'Cold, dry summer, cold summer',},
  { value: 'Dsd', label: 'Cold, dry summer, very cold winter',},
  { value: 'Dwa', label: 'Cold, dry winter, hot summer',},
  { value: 'Dwb', label: 'Cold, dry winter, warm summer',},
  { value: 'Dwc', label: 'Cold, dry winter, cold summer',},
  { value: 'Dwd', label: 'Cold, dry winter, very cold winter',},
  { value: 'Dfa', label: 'Cold, no dry season, hot summer',},
  { value: 'Dfb', label: 'Cold, no dry season, warm summer',},
  { value: 'Dfc', label: 'Cold, no dry season, cold summer',},
  { value: 'Dfd', label: 'Cold, no dry season, very cold winter',},
  { value: 'ET ', label: 'Polar, tundra',},
  { value: 'EF ', label: 'Polar, frost',},
];


const clusterColors = [
  {
    color: 'cyan-5',
    label: '< 100'
  },  
  {
    color: 'yellow-6',
    label: '100 - 750'
  },
  {
    color: 'pink-3',
    label: '> 750'
  }
]

function onToggleLayer(layerId: string) {
  mapStore.applyLayerVisibility(layerId);
  onUpdatedFilter();
}

function onResetFilters() {
  filtersStore.reset();
  onUpdatedFilter();
}

function onUpdatedFilter() {
  mapStore.applyFilters(filtersStore.asParams());
}
</script>