<template>
  <q-dialog :maximized="$q.screen.lt.sm" v-model="showDialog" @hide="onHide">
    <q-card :style="$q.screen.lt.sm ? '' : 'width: 1000px; max-width: 80vw'">
      <q-card-actions v-if="$q.screen.lt.sm" align="right">
        <q-btn flat icon="close" color="primary" v-close-popup />
      </q-card-actions>
      <q-card-section>
        <study-stepper
          class="q-mt-md"
          dialog
          @step="onStep"
        />
      </q-card-section>
      <q-card-actions v-if="$q.screen.gt.xs" align="right">
        <q-btn
          flat
          :label="t('cancel')"
          color="secondary"
          v-close-popup
        />
        <q-btn
          :label="t('save')"
          color="primary"
          :disable="!lastStep"
          v-close-popup
          @click="onSave"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import StudyStepper from 'src/components/contribute/StudyStepper.vue';

interface Props {
  modelValue: boolean;
}
const props = defineProps<Props>();
const emit = defineEmits(['update:modelValue', 'save']);

const { t } = useI18n();

const showDialog = ref(props.modelValue);
const lastStep = ref(false);
const showUpload = ref(false);

watch(
  () => props.modelValue,
  (value) => {
    lastStep.value = false;
    showUpload.value = false;
    showDialog.value = value;
  },
);

function onHide() {
  emit('update:modelValue', false);
}

function onStep(step: number) {
  lastStep.value = step === 4;
}

function onSave() {
  emit('save');
}
</script>