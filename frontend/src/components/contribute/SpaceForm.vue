<template>
  <div>
    <q-input
      v-model="space.identifier"
      filled
      :label="$t('study.space.identifier')"
      :hint="$t('study.space.identifier_hint')"
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
          :label="$t('study.space.type')"
          :hint="$t('study.space.type_hint')"
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
          v-model="space.ventilation_strategy"
          :options="ventilationOptions"
          filled
          emit-value
          map-options
          :label="$t('study.space.ventilation_strategy')"
          :hint="$t('study.space.ventilation_strategy_hint')"
        />
      </div>
      <div class="col">
        <q-input
          v-model.number="space.ventilation_rate"
          type="number"
          filled
          :label="$t('study.space.ventilation_rate')"
          :hint="$t('study.space.ventilation_rate_hint')"
        />
      </div>
    </div>
    <div class="row q-col-gutter-md">
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
          v-model="space.cooling_strategy"
          :options="ventilationOptions"
          filled
          emit-value
          map-options
          :label="$t('study.space.cooling_strategy')"
          :hint="$t('study.space.cooling_strategy_hint')"
        />
      </div>
      <div class="col">
        <q-select
          v-model="space.heating_strategy"
          :options="ventilationOptions"
          filled
          emit-value
          map-options
          :label="$t('study.space.heating_strategy')"
          :hint="$t('study.space.heating_strategy_hint')"
        />
      </div>
      <div class="col">
        <q-select
          v-model="space.standalone_air_filtration"
          :options="yesNoOptions"
          filled
          emit-value
          map-options
          :label="$t('study.space.standalone_air_filtration')"
          :hint="$t('study.space.standalone_air_filtration_hint')"
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
        />
      </div>
      <div class="col">
        <q-select
          v-model="space.major_combustion_sources"
          :options="yesNoOptions"
          filled
          emit-value
          map-options
          :label="$t('study.space.major_combustion_sources')"
          :hint="$t('study.space.major_combustion_sources_hint')"
        />
      </div>
      <div class="col">
        <q-select
          v-model="space.small_combustion_sources"
          :options="yesNoOptions"
          filled
          emit-value
          map-options
          :label="$t('study.space.small_combustion_sources')"
          :hint="$t('study.space.small_combustion_sources_hint')"
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
          v-model="space.visible_dampness"
          :options="yesNoOptions"
          filled
          emit-value
          map-options
          :label="$t('study.space.visible_dampness')"
          :hint="$t('study.space.visible_dampness_hint')"
        />
      </div>
      <div class="col">
        <q-select
          v-model="space.visible_mold"
          :options="yesNoOptions"
          filled
          emit-value
          map-options
          :label="$t('study.space.visible_mold')"
          :hint="$t('study.space.visible_mold_hint')"
        />
      </div>
      <div class="col">
        <q-select
          v-model="space.cleaning_with_detergents"
          :options="yesNoOptions"
          filled
          emit-value
          map-options
          :label="$t('study.space.cleaning_with_detergents')"
          :hint="$t('study.space.cleaning_with_detergents_hint')"
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
import { spaceTypeOptions, occupancyOptions, ventilationOptions, yesNoOptions } from 'src/utils/options';
import { Building, Space } from 'src/models';

interface Props {
  modelValue: Space;
  building: Building;
}
const props = defineProps<Props>();

const contrib = useContributeStore();

const space = ref(props.modelValue);

function onAddPeriod() {
  contrib.addPeriod(props.building.identifier, space.value.identifier);
}

function onDeletePeriod(i: number) {
  contrib.deletePeriod(props.building.identifier, space.value.identifier, i);
}
</script>