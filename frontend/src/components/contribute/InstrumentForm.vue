<template>
  <div>
    <q-input
      v-model="instrument.identifier"
      filled
      :label="$t('study.instrument.identifier')"
      :hint="$t('study.instrument.identifier_hint')"
      class="q-mb-md"
    />

    <div class="row q-col-gutter-md q-mb-md">
      <div class="col">
        <q-input
          v-model="instrument.manufacturer"
          filled
          :label="$t('study.instrument.manufacturer')"
          :hint="$t('study.instrument.manufacturer_hint')"
        />
      </div>
      <div class="col">
        <q-input
          v-model="instrument.model"
          filled
          :label="$t('study.instrument.model')"
          :hint="$t('study.instrument.model_hint')"
        />
      </div>
    </div>

    <div class="row q-col-gutter-md q-mb-md">
      <div class="col">
        <q-select
          v-model="instrument.equipment_grade_rating"
          :options="equipmentGradeOptions"
          filled
          emit-value
          map-options
          :label="$t('study.instrument.equipment_grade')"
          :hint="$t('study.instrument.equipment_grade_hint')"
        />
      </div>
      <div class="col">
        <q-select
          v-model="instrument.placement"
          :options="placementOptions"
          filled
          emit-value
          map-options
          :label="$t('study.instrument.placement')"
          :hint="$t('study.instrument.placement_hint')"
        />
      </div>
    </div>
  </div>
</template>


<script lang="ts">
export default defineComponent({
  name: 'InstrumentForm',
});
</script>
<script setup lang="ts">
import { equipmentGradeOptions, placementOptions } from 'src/utils/options';
import { Instrument } from 'src/models';

interface Props {
  modelValue: Instrument;
}
const props = defineProps<Props>();

const instrument = ref(props.modelValue);

</script>