<template>
  <div>
    <q-input
      v-model="space.identifier"
      filled
      :label="$t('study.space.identifier') + ' *'"
      :hint="$t('study.space.identifier_hint')"
      :rules="[val => !!val || $t('required')]"
      class="q-mb-md"
    />

    <div class="row q-col-gutter-md q-mb-md">
      <div class="col">
        <q-select
          v-model="space.type"
          :options="spaceTypeOptions"
          filled
          emit-value
          map-options
          :label="$t('study.space.type') + ' *'"
          :hint="$t('study.space.type_hint')"
          :rules="[val => !!val || $t('required')]"
        />
      </div>
      <div class="col">
        <q-input
          v-model.number="space.floor_area"
          type="number"
          :min="0"
          filled
          :label="$t('study.space.floor_area')"
          :hint="$t('study.space.floor_area_hint')"
        />
      </div>
      <div class="col">
        <q-input
          v-model.number="space.space_volume"
          type="number"
          :min="0"
          filled
          :label="$t('study.space.space_volume')"
          :hint="$t('study.space.space_volume_hint')"
        />
      </div>
    </div>

    <div class="row q-col-gutter-md q-mb-md">
      <div class="col">
        <q-select
          v-model="space.occupancy"
          :options="occupancyOptions"
          filled
          emit-value
          map-options
          :label="$t('study.space.occupancy')"
          :hint="$t('study.space.occupancy_hint')"
          @update:model-value="onOccupancyChange"
        />
      </div>
      <div class="col">
        <q-input
          v-model.number="space.occupancy_density"
          type="number"
          :min="0"
          filled
          :label="$t('study.space.occupancy_density')"
          :hint="$t('study.space.occupancy_density_hint')"
          :disable="space.occupancy === 'unknown'"
        />
      </div>
    </div>

    <div class="text-bold q-mb-md">Air</div>
    <div class="row q-col-gutter-md">
      <div class="col">
        <q-select
          v-model="space.mechanical_ventilation_type"
          :options="mechanicalVentilationTypeOptions"
          filled
          emit-value
          map-options
          :label="$t('study.space.mechanical_ventilation_type')"
          :hint="$t('study.space.mechanical_ventilation_type_hint')"
        />
      </div>
      <div v-if="space.mechanical_ventilation_type === 'other'" class="col">
        <q-input
          v-model="space.other_mechanical_ventilation_type"
          filled
          :label="$t('study.space.other_mechanical_ventilation_type')"
          :hint="$t('study.space.other_mechanical_ventilation_type_hint')"
        />
      </div>
    </div>
    <div class="row q-col-gutter-md">
      <div class="col">
        <q-select
          v-model="space.cooling_type"
          :options="coolingTypeOptions"
          filled
          emit-value
          map-options
          :label="$t('study.space.cooling_type')"
          :hint="$t('study.space.cooling_type_hint')"
        />
      </div>
      <div v-if="space.cooling_type === 'other'" class="col">
        <q-input
          v-model="space.other_cooling_type"
          filled
          :label="$t('study.space.other_cooling_type')"
          :hint="$t('study.space.other_cooling_type_hint')"
        />
      </div>
      <div class="col">
        <q-select
          v-model="space.heating_type"
          :options="heatingTypeOptions"
          filled
          emit-value
          map-options
          :label="$t('study.space.heating_type')"
          :hint="$t('study.space.heating_type_hint')"
        />
      </div>
      <div v-if="space.heating_type === 'other'" class="col">
        <q-input
          v-model="space.other_heating_type"
          filled
          :label="$t('study.space.other_heating_type')"
          :hint="$t('study.space.other_heating_type_hint')"
        />
      </div>
    </div>
    <div class="row q-col-gutter-md q-mb-md">
      <div class="col">
        <q-select
          v-model="space.air_filtration"
          :options="yesNoOptions"
          filled
          emit-value
          map-options
          :label="$t('study.space.air_filtration')"
          :hint="$t('study.space.air_filtration_hint')"
        />
      </div>
      <div class="col">
      </div>
    </div>

    <div class="text-bold q-mt-md q-mb-md">Combustion</div>
    <div class="row q-col-gutter-md">
      <div class="col">
        <q-select
          v-model="space.combustion_sources"
          :options="yesNoOptions"
          filled
          emit-value
          map-options
          :label="$t('study.space.combustion_sources')"
          :hint="$t('study.space.combustion_sources_hint')"
          @update:model-value="onCombustionSourcesChange"
        />
      </div>
      <div class="col">
        <q-select
          v-model="space.major_combustion_sources"
          :options="majorCombustionSourcesOptions"
          filled
          emit-value
          map-options
          :label="$t('study.space.major_combustion_sources')"
          :hint="$t('study.space.major_combustion_sources_hint')"
          :disable="space.combustion_sources !== 'yes'"
        />
      </div>
      <div class="col">
        <q-select
          v-model="space.minor_combustion_sources"
          :options="minorCombustionSourcesOptions"
          filled
          emit-value
          map-options
          :label="$t('study.space.minor_combustion_sources')"
          :hint="$t('study.space.minor_combustion_sources_hint')"
          :disable="space.combustion_sources !== 'yes'"
        />
      </div>
    </div>

    <div class="text-bold q-mt-md q-mb-md">Other pollutants</div>
    <div class="row q-col-gutter-md">
      <div class="col">
        <q-select
          v-model="space.printers"
          :options="yesNoOptions"
          filled
          emit-value
          map-options
          :label="$t('study.space.printers')"
          :hint="$t('study.space.printers_hint')"
        />
      </div>
      <div class="col">
        <q-select
          v-model="space.carpets"
          :options="yesNoOptions"
          filled
          emit-value
          map-options
          :label="$t('study.space.carpets')"
          :hint="$t('study.space.carpets_hint')"
        />
      </div>
      <div class="col">
        <q-select
          v-model="space.pets"
          :options="yesNoOptions"
          filled
          emit-value
          map-options
          :label="$t('study.space.pets')"
          :hint="$t('study.space.pets_hint')"
        />
      </div>
    </div>
    <div class="row q-col-gutter-md q-mb-md">
      <div class="col">
        <q-select
          v-model="space.dampness"
          :options="yesNoOptions"
          filled
          emit-value
          map-options
          :label="$t('study.space.dampness')"
          :hint="$t('study.space.dampness_hint')"
        />
      </div>
      <div class="col">
        <q-select
          v-model="space.mold"
          :options="yesNoOptions"
          filled
          emit-value
          map-options
          :label="$t('study.space.mold')"
          :hint="$t('study.space.mold_hint')"
        />
      </div>
      <div class="col">
        <q-select
          v-model="space.detergents"
          :options="yesNoOptions"
          filled
          emit-value
          map-options
          :label="$t('study.space.detergents')"
          :hint="$t('study.space.detergents_hint')"
        />
      </div>
    </div>
  </div>
</template>

<script lang="ts">
export default defineComponent({
  name: 'SpaceForm',
});
</script>
<script setup lang="ts">
import {
  buildingSpaceTypeOptions,
  occupancyOptions,
  mechanicalVentilationTypeOptions,
  coolingTypeOptions,
  heatingTypeOptions,
  minorCombustionSourcesOptions,
  majorCombustionSourcesOptions,
  yesNoOptions,
} from 'src/utils/options';
import { Building, Space } from 'src/models';

interface Props {
  modelValue: Space;
  building: Building;
}
const props = defineProps<Props>();

const space = ref(props.modelValue);

const spaceTypeOptions = computed(() => {
  if (props.building.type) {
    return buildingSpaceTypeOptions[props.building.type];
  }
  return [];
});

watch(() => props.modelValue, (val) => {
  space.value = val;
});

watch(() => props.building.type, (val) => {
  if (!spaceTypeOptions.value.map((o) => o.value).includes(space.value.type)) {
    space.value.type = 'other';
  }
});

function onCombustionSourcesChange() {
  if (space.value.combustion_sources !== 'yes') {
    space.value.major_combustion_sources = undefined;
    space.value.minor_combustion_sources = undefined;
  }
}

function onOccupancyChange() {
  if (!space.value.occupancy || ['unknown', 'unoccupied'].includes(space.value.occupancy)) {
    space.value.occupancy_density = undefined;
  }
}
</script>
