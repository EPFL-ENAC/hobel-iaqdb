<template>
  <div>
    <q-input
      v-model="period.identifier"
      filled
      :label="$t('study.period.identifier')"
      :hint="$t('study.period.identifier_hint')"
      class="q-mb-md"
    />

    <div class="text-bold q-mb-md">Time range</div>
    <div class="row q-col-gutter-md q-mb-md">
      <div class="col">
        <q-input
          v-model="period.start_date"
          filled
          :label="$t('study.period.start_date')"
          :hint="$t('study.period.start_date_hint')">
          <template v-slot:append>
            <q-icon name="event" class="cursor-pointer">
              <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                <q-date v-model="period.start_date" mask="YYYY-MM-DD">
                  <div class="row items-center justify-end">
                    <q-btn v-close-popup label="Close" color="primary" flat />
                  </div>
                </q-date>
              </q-popup-proxy>
            </q-icon>
          </template>
        </q-input>
      </div>
      <div class="col">
        <q-input
          v-model="period.end_date"
          filled
          :label="$t('study.period.end_date')"
          :hint="$t('study.period.end_date_hint')">
          <template v-slot:append>
            <q-icon name="event" class="cursor-pointer">
              <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                <q-date v-model="period.end_date" mask="YYYY-MM-DD">
                  <div class="row items-center justify-end">
                    <q-btn v-close-popup label="Close" color="primary" flat />
                  </div>
                </q-date>
              </q-popup-proxy>
            </q-icon>
          </template>
        </q-input>
      </div>
    </div>

    <div class="text-bold q-mb-md">Air</div>
    <div class="row q-col-gutter-md">
      <div class="col">
        <q-select
          v-model="period.ventilation_strategy"
          :options="ventilationOptions"
          filled
          emit-value
          map-options
          :label="$t('study.period.ventilation_strategy')"
          :hint="$t('study.period.ventilation_strategy_hint')"
        />
      </div>
      <div class="col">
        <q-input
          v-model.number="period.ventilation_rate"
          type="number"
          filled
          :label="$t('study.period.ventilation_rate')"
          :hint="$t('study.period.ventilation_rate_hint')"
        />
      </div>
    </div>
    <div class="row q-col-gutter-md">
      <div class="col">
        <q-input
          v-model.number="period.air_change_rate"
          type="number"
          filled
          :label="$t('study.period.air_change_rate')"
          :hint="$t('study.period.air_change_rate_hint')"
        />
      </div>
      <div class="col">
        <q-input
          v-model.number="period.particle_filtration_rating"
          type="number"
          filled
          :label="$t('study.period.particle_filtration_rating')"
          :hint="$t('study.period.particle_filtration_rating_hint')"
        />
      </div>
    </div>
    <div class="row q-col-gutter-md">
      <div class="col">
        <q-select
          v-model="period.cooling_strategy"
          :options="ventilationOptions"
          filled
          emit-value
          map-options
          :label="$t('study.period.cooling_strategy')"
          :hint="$t('study.period.cooling_strategy_hint')"
        />
      </div>
      <div class="col">
        <q-select
          v-model="period.heating_strategy"
          :options="ventilationOptions"
          filled
          emit-value
          map-options
          :label="$t('study.period.heating_strategy')"
          :hint="$t('study.period.heating_strategy_hint')"
        />
      </div>
      <div class="col">
        <q-select
          v-model="period.standalone_air_filtration"
          :options="yesNoOptions"
          filled
          emit-value
          map-options
          :label="$t('study.period.standalone_air_filtration')"
          :hint="$t('study.period.standalone_air_filtration_hint')"
        />
      </div>
    </div>

    <div class="text-bold q-mt-md q-mb-md">Combustion</div>
    <div class="row q-col-gutter-md">
      <div class="col">
        <q-select
          v-model="period.combustion_sources"
          :options="yesNoOptions"
          filled
          emit-value
          map-options
          :label="$t('study.period.combustion_sources')"
          :hint="$t('study.period.combustion_sources_hint')"
        />
      </div>
      <div class="col">
        <q-select
          v-model="period.major_combustion_sources"
          :options="yesNoOptions"
          filled
          emit-value
          map-options
          :label="$t('study.period.major_combustion_sources')"
          :hint="$t('study.period.major_combustion_sources_hint')"
        />
      </div>
      <div class="col">
        <q-select
          v-model="period.small_combustion_sources"
          :options="yesNoOptions"
          filled
          emit-value
          map-options
          :label="$t('study.period.small_combustion_sources')"
          :hint="$t('study.period.small_combustion_sources_hint')"
        />
      </div>
    </div>

    <div class="text-bold q-mt-md q-mb-md">Other pollutants</div>
    <div class="row q-col-gutter-md">
      <div class="col">
        <q-select
          v-model="period.printers"
          :options="yesNoOptions"
          filled
          emit-value
          map-options
          :label="$t('study.period.printers')"
          :hint="$t('study.period.printers_hint')"
        />
      </div>
      <div class="col">
        <q-select
          v-model="period.carpets"
          :options="yesNoOptions"
          filled
          emit-value
          map-options
          :label="$t('study.period.carpets')"
          :hint="$t('study.period.carpets_hint')"
        />
      </div>
      <div class="col">
        <q-select
          v-model="period.pets"
          :options="yesNoOptions"
          filled
          emit-value
          map-options
          :label="$t('study.period.pets')"
          :hint="$t('study.period.pets_hint')"
        />
      </div>
    </div>
    <div class="row q-col-gutter-md q-mb-md">
      <div class="col">
        <q-select
          v-model="period.visible_dampness"
          :options="yesNoOptions"
          filled
          emit-value
          map-options
          :label="$t('study.period.visible_dampness')"
          :hint="$t('study.period.visible_dampness_hint')"
        />
      </div>
      <div class="col">
        <q-select
          v-model="period.visible_mold"
          :options="yesNoOptions"
          filled
          emit-value
          map-options
          :label="$t('study.period.visible_mold')"
          :hint="$t('study.period.visible_mold_hint')"
        />
      </div>
      <div class="col">
        <q-select
          v-model="period.cleaning_with_detergents"
          :options="yesNoOptions"
          filled
          emit-value
          map-options
          :label="$t('study.period.cleaning_with_detergents')"
          :hint="$t('study.period.cleaning_with_detergents_hint')"
        />
      </div>
    </div>

  </div>
</template>


<script lang="ts">
export default defineComponent({
  name: 'PeriodForm',
});
</script>
<script setup lang="ts">
import { spaceTypeOptions, occupancyOptions, ventilationOptions, yesNoOptions } from 'src/utils/options';
import { Period } from 'src/models';

interface Props {
  modelValue: Period;
}
const props = defineProps<Props>();

const period = ref(props.modelValue);
</script>