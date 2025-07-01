<template>
  <div>
    <div class="q-mb-md q-pa-md bg-secondary text-white">
      <div v-if="isUpdate">
        You are currently editing the study draft
        <q-chip color="accent" icon-right="content_copy" :label="contrib.study.identifier" clickable @click="onCopy" text-color="white" />
      </div>
      <div v-else>
        <p class="text-bold">You are currently editing a new study.</p>
        Note that the study information are automatically saved in your browser: you can pause/resume the form at any time. The study draft will be permanently saved on the iAQ DB server once submitted only. 
      </div>
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
                accept=".xlsx,.xlsm"
                clearable
                color="black"
                @update:model-value="onExcelFileUpdated"
              />
            </div>
          </q-card-section>
        </q-card>
        <q-markdown no-heading-anchor-links :src="StepStudyMd" />
        <q-form ref="studyFormRef">
          <study-form class="q-mt-lg" />
        </q-form>
      </q-step>

      <q-step
        :name="2"
        title="Buildings and spaces information"
        icon="domain"
        :done="step > 2"
        :header-nav="step > 2"
      >
        <q-markdown no-heading-anchor-links :src="StepBuildingsMd" />
        <q-form ref="buildingsFormRef">
          <buildings-form class="q-mt-lg" />
        </q-form>
      </q-step>

      <q-step
        :name="3"
        title="Instruments"
        icon="domain"
        :done="step > 3"
        :header-nav="step > 3"
      >
        <q-markdown no-heading-anchor-links :src="StepInstrumentsMd" />
        <q-form ref="instrumentsFormRef">
          <instruments-form class="q-mt-lg" />
        </q-form>
      </q-step>

      <q-step
        :name="4"
        title="Upload datasets"
        icon="upload"
        :header-nav="step > 4"
      >
        <q-markdown no-heading-anchor-links :src="StepDatasetsMd" />

        <div v-show="false">
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
          color="secondary"
          :label="t('back')"
          class="on-left"
        />
        <q-btn
          v-if="step < 4"
          @click="onNextStep"
          :disable="!canNext"
          color="primary"
          :label="t('continue')"
        />
      </q-card-section>
    </q-card>
    <q-card v-else bordered class="bg-grey-4 stepper-nav">
      <q-card-section>
        <q-btn
          v-if="step > 1"
          flat
          @click="onPreviousStep"
          color="secondary"
          :label="t('back')"
          class="on-left"
        />
        <q-btn
          v-if="step < 4"
          @click="onNextStep"
          color="primary"
          :label="t('continue')"
        />
        <q-btn
          v-if="step === 4"
          color="primary"
          @click="onSubmit"
          :label="t('submit')"
        />
        <q-btn
          @click="onPause"
          flat
          color="secondary"
          :label="t('pause')"
          class="on-right"
        />
      </q-card-section>
    </q-card>
  </div>
</template>

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
import { copyToClipboard } from 'quasar';
import { notifyError, notifyInfo } from 'src/utils/notify';

interface Props {
  dialog?: boolean;
}
defineProps<Props>();
const emit = defineEmits(['pause', 'submit', 'step']);

const { t } = useI18n();
const contrib = useContributeStore();

const studyFormRef = ref();
const buildingsFormRef = ref();
const instrumentsFormRef = ref();
const excelFile = ref<File | null>(null);
const loading = ref(false);
const step = ref(1);

const isUpdate = computed(() => contrib.study.identifier && contrib.study.identifier !== '_draft');

const canNext = computed(() => {
  if (step.value === 1) {
    // study form validation
    const valid = studyFormRef.value?.validate();
    return contrib.inProgress;
  } else if (step.value === 2) {
    // buildings form validation
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
    // instruments form validation
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

function onSubmit() {
  emit('submit');
}

function onPreviousStep() {
  step.value -= 1;
  emit('step', step.value);
}

async function onNextStep() {
  if (step.value === 1) {
    // study validation
    let valid = true;
    if (!contrib.study.contributors || contrib.study.contributors.length === 0) {
      valid = false;
      notifyError('Please add at least one data contributor');
    }
    if (contrib.study.license !== 'PDDL') {
      valid = false;
      notifyError('study.license_error');
    }
    if (valid){
      valid = await studyFormRef.value?.validate();
      if (valid) {
        goNext();
      } else {
        notifyError('fix_validation_errors');
      }
    }
  } else if (step.value === 2) {
    // buildings validation
    if (contrib.study.buildings &&
      contrib.study.buildings.length > 0) {
      const valid = await buildingsFormRef.value?.validate();
      if (valid) {
        goNext();
      } else {
        notifyError('fix_validation_errors');
      }
    } else {
      notifyError('Please add at least one building');
    }
  } else if (step.value === 3) {
    // instruments validation
    if (contrib.study.instruments &&
      contrib.study.instruments.length > 0) {
      const valid = await instrumentsFormRef.value?.validate();
      if (valid) {
        goNext();
      } else {
        notifyError('fix_validation_errors');
      }
    } else {
      notifyError('Please add at least one instrument');
    }
  } else {
    goNext();
  }
}

function goNext() {
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
      .catch((err) => notifyError(err))
      .finally(() => (loading.value = false));
  }
}

function onCopy() {
  copyToClipboard(contrib.study.identifier);
  notifyInfo('Study ID copied to clipboard');
}
</script>
