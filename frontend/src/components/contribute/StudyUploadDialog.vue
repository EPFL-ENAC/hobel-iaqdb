<template>
  <q-dialog :maximized="$q.screen.lt.sm" v-model="showDialog" @hide="onHide">
    <q-card :style="$q.screen.lt.sm ? '' : 'width: 500px; max-width: 80vw'">
      <q-card-actions v-if="$q.screen.lt.sm" align="right">
        <q-btn flat icon="close" color="primary" v-close-popup />
      </q-card-actions>
      <q-card-section>
        <div class="q-mt-md text-help">
          {{ status }}
        </div>
        <q-linear-progress
          size="25px"
          :value="progress"
          :buffer="buffer"
          :color="color"
          stripe
        >
          <div class="absolute-full flex flex-center">
            <q-badge color="white" text-color="accent" :label="progressLabel" />
          </div>
        </q-linear-progress>
        <div v-if="status === 'Done'" class="q-mt-md">
          <div>
            Thanks for your contribution! A reviewer will verify your submission,
            and you will get a notification when the study is online.
          </div>
          <div class="q-mt-md">
            <div class="q-mb-sm">
              Please copy this study ID and keep it for future reference:
            </div>
            <q-chip color="secondary" icon-right="content_copy" :label="contrib.study.identifier" clickable @click="onCopy" text-color="white" />
          </div>
        </div>
        <div v-if="status === 'Error'" class="q-mt-md">
          An error occurred while uploading the study. Please verify your data or try again later.
        </div>
      </q-card-section>
      <q-card-actions v-if="$q.screen.gt.xs" align="right">
        <q-btn
          flat
          :label="t('close')"
          color="primary"
          v-close-popup
          @click="onClose"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { useQuasar } from 'quasar';
import { copyToClipboard } from 'quasar';
import { notifyError, notifyInfo } from 'src/utils/notify';

const $q = useQuasar();
const { t } = useI18n();
const contrib = useContributeStore();

interface Props {
  modelValue: boolean;
}
const props = defineProps<Props>();
const emit = defineEmits(['update:modelValue', 'cancel', 'close']);

const showDialog = ref(props.modelValue);
const progress = ref(0);
const buffer = ref(0);
const status = ref('');
const color = ref('accent');

const progressLabel = computed(() => (progress.value * 100).toFixed(0) + '%');

watch(
  () => props.modelValue,
  (value) => {
    showDialog.value = value;
    progress.value = 0;
    buffer.value = 0;
    status.value = '';
    if (value) {
      void doSave();
    }
  },
);

function onHide() {
  emit('update:modelValue', false);
}

function onClose() {
  if (progress.value < 1) {
    emit('cancel');
  } else {
    emit('close');
  }
}

async function doSave() {
  progress.value = 0;
  color.value = 'accent';
  buffer.value = 0.25;
  status.value = 'Uploading study, buildings and instruments...';
  try {
    await contrib.saveOrUpdateDraft();
    progress.value = 1;
    status.value = 'Done';
  } catch (error) {
    color.value = 'negative';
    status.value = 'Error';
    notifyError(error);
  }
}

function onCopy() {
  copyToClipboard(contrib.study.identifier).then(() => {
    notifyInfo('Study ID copied to clipboard');
  }).catch((error) => {
    notifyError(error);
  });
}
</script>
