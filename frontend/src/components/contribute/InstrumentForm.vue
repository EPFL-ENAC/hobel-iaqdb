<template>
  <div>
    <q-input
      v-model="instrument.identifier"
      filled
      :label="t('study.instrument.identifier')"
      :hint="t('study.instrument.identifier_hint')"
      class="q-mb-md"
    />

    <div class="row q-col-gutter-md q-mb-md">
      <div class="col">
        <q-input
          v-model="instrument.manufacturer"
          filled
          :label="t('study.instrument.manufacturer')"
          :hint="t('study.instrument.manufacturer_hint')"
        />
      </div>
      <div class="col">
        <q-input
          v-model="instrument.model"
          filled
          :label="t('study.instrument.model')"
          :hint="t('study.instrument.model_hint')"
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
          :label="t('study.instrument.equipment_grade')"
          :hint="t('study.instrument.equipment_grade_hint')"
        />
      </div>
      <div class="col">
        <q-select
          v-model="instrument.placement"
          :options="placementOptions"
          filled
          emit-value
          map-options
          :label="t('study.instrument.placement')"
          :hint="t('study.instrument.placement_hint')"
        />
      </div>
    </div>
    <div class="text-bold q-mb-md">Measurement parameters</div>
    <q-card flat bordered class="q-mb-md bg-grey-2">
      <q-card-section>
        <div
          v-if="!instrument.parameters || instrument.parameters?.length === 0"
          class="text-help"
        >
          No parameters defined yet.
        </div>
        <q-list separator>
          <template v-for="(param, i) in instrument.parameters" :key="param.id">
            <q-item class="q-pl-none q-pr-none">
              <q-item-section>
                <q-expansion-item
                  dense
                  label="..."
                  header-class="text-bold text-secondary"
                >
                  <template v-slot:header>
                    {{ `${getInstrumentParameterLabel(i)}` }}
                  </template>
                  <instrument-parameter-form
                    v-model="instrument.parameters[i]"
                    :instrument="instrument"
                    class="q-mt-md"
                  />
                </q-expansion-item>
              </q-item-section>
              <q-item-section side>
                <div>
                  <q-btn
                    rounded
                    dense
                    flat
                    :title="t('duplicate')"
                    icon="content_copy"
                    size="sm"
                    @click="onDuplicateParameter(i)"
                  />
                  <q-btn
                    rounded
                    dense
                    flat
                    color="negative"
                    :title="t('delete')"
                    icon="delete"
                    size="sm"
                    @click="onDeleteParameter(i)"
                  />
                </div>
              </q-item-section>
            </q-item>
          </template>
        </q-list>
      </q-card-section>
      <q-card-actions class="bg-grey-3 q-pa-md">
        <q-btn
          @click="onAddParameter"
          color="secondary"
          label="Add Parameter"
          icon="add"
          size="sm"
        />
      </q-card-actions>
    </q-card>
  </div>
</template>

<script setup lang="ts">
import InstrumentParameterForm from './InstrumentParameterForm.vue';
import {
  equipmentGradeOptions,
  placementOptions,
  physicalParameterOptions,
} from 'src/utils/options';
import { Instrument } from 'src/models';
import { notifyInfo } from 'src/utils/notify';

const { t } = useI18n();
const contrib = useContributeStore();

interface Props {
  modelValue: Instrument;
}
const props = defineProps<Props>();

const instrument = ref(props.modelValue);

watch(() => props.modelValue, (value) => {
  instrument.value = value;
});

function getInstrumentParameterLabel(i: number) {
  if (!instrument.value.parameters) return i;
  const val = instrument.value.parameters[i].physical_parameter;
  return physicalParameterOptions.find((o) => o.value === val)?.label || val;
}

function onDuplicateParameter(i: number) {
  if (!instrument.value.parameters) return;
  contrib.addInstrumentParameter(instrument.value.identifier, instrument.value.parameters[i]);
  notifyInfo('Instrument parameter duplicated');
}

function onAddParameter() {
  contrib.addInstrumentParameter(instrument.value.identifier);
  notifyInfo('New instrument parameter added');
}

function onDeleteParameter(i: number) {
  contrib.deleteInstrumentParameter(instrument.value.identifier, i);
  notifyInfo('Instrument parameter deleted');
}
</script>
