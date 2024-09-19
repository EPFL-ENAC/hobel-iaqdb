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
          color="accent"
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
      </q-card-section>
      <q-card-actions v-if="$q.screen.gt.xs" align="right">
        <q-btn
          flat
          :label="$t('close')"
          color="primary"
          v-close-popup
          @click="onClose"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script lang="ts">
export default defineComponent({
  name: 'StudyUploadDialog',
});
</script>
<script setup lang="ts">
import { copyToClipboard } from 'quasar';
import { notifySuccess } from 'src/utils/notify';

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

const progressLabel = computed(() => (progress.value * 100).toFixed(0) + '%');

watch(
  () => props.modelValue,
  (value) => {
    showDialog.value = value;
    progress.value = 0;
    buffer.value = 0;
    status.value = '';
    if (value) {
      doSave();
    }
  },
);

function onHide() {
  emit('update:modelValue', false);
}

function onClose() {
  emit('close');
}

async function doSave() {
  progress.value = 0;
  buffer.value = 0.25;
  status.value = 'Uploading study, buildings and instruments...';
  await contrib.saveOrUpdateDraft();
  progress.value = 0.5;
  buffer.value = 0.75;
  status.value = '[fake] Uploading data files...';
  await sleep(1000);
  progress.value = 0.75;
  buffer.value = 1;
  await sleep(1000);
  progress.value = 1;
  await sleep(2000);
  status.value = 'Done';
}

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function onCopy() {
  copyToClipboard(contrib.study.identifier);
  notifySuccess('Study ID copied to clipboard');
}
</script>
