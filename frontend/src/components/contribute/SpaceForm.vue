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

    <div class="row q-col-gutter-md">
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
        <q-select
          v-model="space.occupancy"
          :options="occupancyOptions"
          filled
          emit-value
          map-options
          :label="$t('study.space.occupancy')"
          :hint="$t('study.space.occupancy_hint')"
        />
      </div>
    </div>

    <div class="text-bold q-mb-md">Air</div>
    <div class="row q-col-gutter-md">
      <div class="col">
        <q-select
          v-model="space.ventilation_status"
          :options="ventilationStatusOptions"
          filled
          emit-value
          map-options
          :label="$t('study.space.ventilation_status')"
          :hint="$t('study.space.ventilation_status_hint')"
        />
      </div>
      <div class="col">
        <q-select
          v-model="space.ventilation_type"
          :options="ventilationTypeOptions"
          filled
          emit-value
          map-options
          :label="$t('study.space.ventilation_type')"
          :hint="$t('study.space.ventilation_type_hint')"
        />
      </div>
      <div class="col">
        <q-select
          v-model="space.windows_status"
          :options="windowsStatusOptions"
          filled
          emit-value
          map-options
          :label="$t('study.space.windows_status')"
          :hint="$t('study.space.windows_status_hint')"
        />
      </div>
    </div>
    <div class="row q-col-gutter-md q-mb-md">
      <div class="col">
        <q-input
          v-model.number="space.ventilation_rate"
          type="number"
          filled
          :label="$t('study.space.ventilation_rate')"
          :hint="$t('study.space.ventilation_rate_hint')"
        />
      </div>
      <div class="col">
        <q-input
          v-model.number="space.air_change_rate"
          type="number"
          filled
          :label="$t('study.space.air_change_rate')"
          :hint="$t('study.space.air_change_rate_hint')"
        />
      </div>
      <div class="col">
        <q-input
          v-model.number="space.particle_filtration_rating"
          type="number"
          filled
          :label="$t('study.space.particle_filtration_rating')"
          :hint="$t('study.space.particle_filtration_rating_hint')"
        />
      </div>
    </div>
    <div class="row q-col-gutter-md">
      <div class="col">
        <q-select
          v-model="space.cooling_status"
          :options="coolingStatusOptions"
          filled
          emit-value
          map-options
          :label="$t('study.space.cooling_status')"
          :hint="$t('study.space.cooling_status_hint')"
        />
      </div>
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
      <div class="col">
        <q-select
          v-model="space.heating_status"
          :options="heatingStatusOptions"
          filled
          emit-value
          map-options
          :label="$t('study.space.heating_status')"
          :hint="$t('study.space.heating_status_hint')"
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
  ventilationStatusOptions,
  ventilationTypeOptions,
  windowsStatusOptions,
  coolingStatusOptions,
  coolingTypeOptions,
  heatingStatusOptions,
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
</script>
