<template>
  <div>
    <q-stepper
      v-model="step"
      header-nav
      ref="stepper"
      color="primary"
      animated
      style="margin-bottom: 80px"
    >
      <q-step
        :name="1"
        title="Study information"
        icon="settings"
        :done="step > 1"
        :header-nav="step > 1"
      >
        <q-card class="q-mb-lg bg-warning">
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
        <datasets-form class="q-mt-lg" />
      </q-step>
    </q-stepper>

    <q-card bordered class="bg-grey-4 stepper-nav">
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
          :disable="!contrib.inProgress"
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

const emit = defineEmits(['pause', 'finish']);

const contrib = useContributeStore();

const excelFile = ref<File | null>(null);
const loading = ref(false);
const step = ref(1);

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
}

function onNextStep() {
  step.value += 1;
}

function onDownloadExcelTemplate() {
  window.open(
    'https://epflch.sharepoint.com/:x:/r/sites/ENAC-IT/Documents%20partages/Research%20IT/Advanced%20Services/0002%20%E2%80%93%20PILOT%20iAQ/Pilot_iAQ_Shared/Data/Metadata/Metadata_entry_form.xlsx?d=w057cb00af74445bdb7a4dca02ae52df1&csf=1&web=1&e=vgUhs1',
  );
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
