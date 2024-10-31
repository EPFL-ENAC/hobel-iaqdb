<template>
  <div>
    <div class="row q-col-gutter-md q-mb-md">
      <div class="col">
        <q-select
          v-model="parameter.physical_parameter"
          :options="physicalParameterOptions"
          filled
          emit-value
          map-options
          :label="$t('study.parameter.physical_parameter') + ' *'"
          :hint="$t('study.parameter.physical_parameter_hint')"
          :rules="[val => !!val || $t('required')]"
          @update:model-value="onPhysicalParameterChange"
        />
      </div>
      <div class="col">
        <q-input
          v-model="parameter.analysis_method"
          filled
          :label="$t('study.parameter.analysis_method')"
          :hint="$t('study.parameter.analysis_method_hint')"
          :disable="knownPhysicalParameters"
        />
      </div>
      <div class="col">
        <q-input
          v-model="parameter.measurement_uncertainty"
          filled
          :label="$t('study.parameter.measurement_uncertainty')"
          :hint="$t('study.parameter.measurement_uncertainty_hint')"
          :disable="knownPhysicalParameters"
        />
      </div>
    </div>
    <q-input
      v-model="parameter.note"
      filled
      type="textarea"
      :label="$t('study.parameter.note')"
      :hint="$t('study.parameter.note_hint')"
    />
  </div>
</template>

<script lang="ts">
export default defineComponent({
  name: 'InstrumentParameterForm',
});
</script>
<script setup lang="ts">
import { Instrument, InstrumentParameter } from 'src/models';
import { physicalParameterOptions } from 'src/utils/options';

interface Props {
  modelValue: InstrumentParameter;
  instrument: Instrument;
}
const props = defineProps<Props>();

const parameter = ref(props.modelValue);

const knownPhysicalParameters = computed(() =>
  ['air temperature', 'relative humidity'].includes(parameter.value.physical_parameter)
);

watch(
  () => props.modelValue,
  (newValue) => {
    parameter.value = newValue;
  }
);

function onPhysicalParameterChange() {
  if (knownPhysicalParameters.value) {
    parameter.value.analysis_method = '';
    parameter.value.measurement_uncertainty = '';
  }
}
</script>
