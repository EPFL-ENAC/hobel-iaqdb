<template>
  <q-dialog v-model="showDialog" persistent @hide="onHide">
    <q-card>
      <q-card-section v-if="props.title">
        <div class="text-h6">{{ props.title }}</div>
      </q-card-section>

      <q-separator v-if="props.title" />

      <q-card-section class="q-pa-lg">
        <span>{{ props.text }}</span>
      </q-card-section>

      <q-card-actions align="right">
        <q-btn flat :label="t('cancel')" color="secondary" @click="onCancel" v-close-popup />
        <q-btn flat :label="t('confirm')" color="primary" @click="onConfirm" v-close-popup />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
interface DialogProps {
  modelValue: boolean;
  title?: string;
  text: string;
}

const props = defineProps<DialogProps>();
const emit = defineEmits(['update:modelValue', 'confirm', 'cancel']);

const { t } = useI18n();

const showDialog = ref(props.modelValue);

watch(
  () => props.modelValue,
  (value) => {
    showDialog.value = value;
  }
);

function onHide() {
  emit('update:modelValue', false);
}

function onCancel() {
  emit('cancel', true);
}

function onConfirm() {
  emit('confirm', true);
}
</script>