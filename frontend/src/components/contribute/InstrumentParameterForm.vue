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
        />
      </div>
      <div class="col">
        <q-input
          v-model="parameter.analysis_method"
          filled
          :label="$t('study.parameter.analysis_method')"
          :hint="$t('study.parameter.analysis_method_hint')"
        />
      </div>
      <div class="col">
        <q-input
          v-model="parameter.measurement_uncertainty"
          filled
          :label="$t('study.parameter.measurement_uncertainty')"
          :hint="$t('study.parameter.measurement_uncertainty_hint')"
        />
      </div>
    </div>
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

watch(
  () => props.modelValue,
  (newValue) => {
    parameter.value = newValue;
  }
);
</script>
