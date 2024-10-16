<template>
  <div>
    <div v-if="isUpdate" class="q-mb-md q-pa-md bg-secondary text-white">
      You are currently editing the study draft
      <q-badge class="q-pa-sm q-ml-sm" color="accent" :title="contrib.study.identifier">{{ contrib.study.identifier.split('-')[0] }}...</q-badge>
    </div>
    <q-stepper
      v-model="step"
      header-nav
      ref="stepper"
      color="primary"
      animated
      :style="dialog ? 'margin-bottom: 10px' : 'margin-bottom: 80px'"
    >
      <q-step
        :name="1"
        title="Study information"
        icon="settings"
        :done="step > 1"
        :header-nav="step > 1"
      >
        <q-card v-if="!isUpdate" class="q-mb-lg bg-warning">
          <q-card-section>
            <div class="row">
              <q-icon
                name="lightbulb"
                class="on-left"
                style="margin-top: 10px"
              />
              <div class="q-mt-sm">
                Tip: you can prepopulate the study, buildings, spaces etc. forms
                using an Excel file.
              </div>
              <q-btn
                label="Download Excel template"
                color="black"
                icon="download"
                size="sm"
                outline
                no-caps
                class="on-right"
                style="margin-top: 7px"
                @click="onDownloadExcelTemplate"
              />
            </div>
            <div class="row q-mt-md q-ml-md">
              <q-file
                outlined
                dense
                v-model="excelFile"
                label="Import from Excel"
                :disable="loading"
                :loading="loading"
                accept=".xlsx"
                clearable
                color="black"
                @update:model-value="onExcelFileUpdated"
              />
            </div>
          </q-card-section>
        </q-card>
        <q-markdown no-heading-anchor-links :src="StepStudyMd" />
        <study-form class="q-mt-lg" />
      </q-step>

      <q-step
        :name="2"
        title="Buildings and spaces information"
        icon="domain"
        :done="step > 2"
        :header-nav="step > 2"
      >
        <q-markdown no-heading-anchor-links :src="StepBuildingsMd" />
        <buildings-form class="q-mt-lg" />
      </q-step>

      <q-step
        :name="3"
        title="Instruments"
        icon="domain"
        :done="step > 3"
        :header-nav="step > 3"
      >
        <q-markdown no-heading-anchor-links :src="StepInstrumentsMd" />
        <instruments-form class="q-mt-lg" />
      </q-step>

      <q-step
        :name="4"
        title="Upload datasets"
        icon="upload"
        :header-nav="step > 4"
      >
        <q-markdown no-heading-anchor-links :src="StepDatasetsMd" />

        <div>
          <q-btn
            label="Download Dictionary Reference"
            color="black"
            icon="download"
            size="sm"
            outline
            no-caps
            class="q-mt-md"
            @click="onDownloadDictionaryReference"
          />
        </div>

        <datasets-form class="q-mt-lg" />
      </q-step>
    </q-stepper>

    <q-card v-if="dialog" flat>
      <q-card-section>
        <q-btn
          v-if="step > 1"
          flat
          @click="onPreviousStep"
          color="primary"
          label="Back"
          class="on-left"
        />
        <q-btn
          v-if="step < 4"
          @click="onNextStep"
          :disable="!canNext"
          color="primary"
          label="Continue"
        />
      </q-card-section>
    </q-card>
    <q-card v-else bordered class="bg-grey-4 stepper-nav">
      <q-card-section>
        <q-btn
          v-if="step > 1"
          flat
          @click="onPreviousStep"
          color="primary"
          label="Back"
          class="on-left"
        />
        <q-btn
          v-if="step < 4"
          @click="onNextStep"
          :disable="!canNext"
          color="primary"
          label="Continue"
        />
        <q-btn
          v-if="step === 4"
          color="primary"
          @click="onFinish"
          label="Finish"
        />
        <q-btn
          @click="onPause"
          flat
          color="secondary"
          label="Pause"
          class="on-right"
        />
      </q-card-section>
    </q-card>
  </div>
</template>

<script lang="ts">
export default defineComponent({
  components: { BuildingsForm, DatasetsForm },
  name: 'StudyStepper',
});
</script>
<script setup lang="ts">
import StepStudyMd from 'src/assets/step-study.md';
import StepBuildingsMd from 'src/assets/step-buildings.md';
import StepInstrumentsMd from 'src/assets/step-instruments.md';
import StepDatasetsMd from 'src/assets/step-datasets.md';
import StudyForm from 'src/components/contribute/StudyForm.vue';
import BuildingsForm from 'src/components/contribute/BuildingsForm.vue';
import InstrumentsForm from 'src/components/contribute/InstrumentsForm.vue';
import DatasetsForm from 'src/components/contribute/DatasetsForm.vue';
import { baseUrl } from 'src/boot/api';

interface Props {
  dialog?: boolean;
}
defineProps<Props>();
const emit = defineEmits(['pause', 'finish', 'step']);

const contrib = useContributeStore();

const excelFile = ref<File | null>(null);
const loading = ref(false);
const step = ref(1);

const isUpdate = computed(() => contrib.study.identifier && contrib.study.identifier !== '_draft');

const canNext = computed(() => {
  if (step.value === 1) {
    // TODO study validation
    return contrib.inProgress;
  } else if (step.value === 2) {
    // TODO buildings validation
    return (
      contrib.study.buildings &&
      contrib.study.buildings.length > 0 &&
      contrib.study.buildings.every(
        (b) =>
          b.identifier &&
          b.spaces &&
          b.spaces.length > 0 &&
          b.spaces.every((s) => s.identifier),
      )
    );
  } else if (step.value === 3) {
    // TODO instruments validation
    return (
      contrib.study.instruments &&
      contrib.study.instruments.length > 0 &&
      contrib.study.instruments.every(
        (i) =>
          i.identifier &&
          i.parameters &&
          i.parameters.length > 0 &&
          i.parameters.every((p) => p.physical_parameter),
      )
    );
  }
  return false;
});

function onPause() {
  emit('pause');
}

function onFinish() {
  emit('finish');
}

function onPreviousStep() {
  step.value -= 1;
  emit('step', step.value);
}

function onNextStep() {
  step.value += 1;
  emit('step', step.value);
}

function onDownloadExcelTemplate() {
  window.open(`${baseUrl}/contribute/study-template`);
}

function onDownloadDictionaryReference() {
  window.open(`${baseUrl}/contribute/dataset-dictionary`);
}

function onExcelFileUpdated() {
  if (excelFile.value) {
    loading.value = true;
    contrib
      .readExcel(excelFile.value)
      .then(() => (step.value = 1))
      .catch((err) => console.error(err))
      .finally(() => (loading.value = false));
  }
}
</script>
