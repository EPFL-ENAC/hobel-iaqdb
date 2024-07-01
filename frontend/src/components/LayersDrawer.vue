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
          class="q-pr-sm"
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
  { value: 'Af ', label: '[Af]  Tropical, rainforest',},
  { value: 'Am ', label: '[Am]  Tropical, monsoon',},
  { value: 'Aw ', label: '[Aw]  Tropical, savannah',},
  { value: 'BWh', label: '[BWh] Arid, desert, hot',},
  { value: 'BWk', label: '[BWk] Arid, desert, cold',},
  { value: 'BSh', label: '[BSh] Arid, steppe, hot',},
  { value: 'BSk', label: '[BSk] Arid, steppe, cold',},
  { value: 'Csa', label: '[Csa] Temperate, dry summer, hot summer',},
  { value: 'Csb', label: '[Csb] Temperate, dry summer, warm summer',},
  { value: 'Csc', label: '[Csc] Temperate, dry summer, cold summer',},
  { value: 'Cwa', label: '[Cwa] Temperate, dry winter, hot summer',},
  { value: 'Cwb', label: '[Cwb] Temperate, dry winter, warm summer',},
  { value: 'Cwc', label: '[Cwc] Temperate, dry winter, cold summer',},
  { value: 'Cfa', label: '[Cfa] Temperate, no dry season, hot summer',},
  { value: 'Cfb', label: '[Cfb] Temperate, no dry season, warm summer',},
  { value: 'Cfc', label: '[Cfc] Temperate, no dry season, cold summer',},
  { value: 'Dsa', label: '[Dsa] Cold, dry summer, hot summer',},
  { value: 'Dsb', label: '[Dsb] Cold, dry summer, warm summer',},
  { value: 'Dsc', label: '[Dsc] Cold, dry summer, cold summer',},
  { value: 'Dsd', label: '[Dsd] Cold, dry summer, very cold winter',},
  { value: 'Dwa', label: '[Dwa] Cold, dry winter, hot summer',},
  { value: 'Dwb', label: '[Dwb] Cold, dry winter, warm summer',},
  { value: 'Dwc', label: '[Dwc] Cold, dry winter, cold summer',},
  { value: 'Dwd', label: '[Dwd] Cold, dry winter, very cold winter',},
  { value: 'Dfa', label: '[Dfa] Cold, no dry season, hot summer',},
  { value: 'Dfb', label: '[Dfb] Cold, no dry season, warm summer',},
  { value: 'Dfc', label: '[Dfc] Cold, no dry season, cold summer',},
  { value: 'Dfd', label: '[Dfd] Cold, no dry season, very cold winter',},
  { value: 'ET ', label: '[ET]  Polar, tundra',},
  { value: 'EF ', label: '[EF]  Polar, frost',},
];

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
  onUpdatedFilter();
}

function onUpdatedFilter() {
  mapStore.applyFilters(filtersStore.asParams());
}
</script>