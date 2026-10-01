<template>
  <q-dialog :maximized="$q.screen.lt.sm" v-model="showDialog" @hide="onHide" @show="onShow">
    <q-card :style="$q.screen.lt.sm ? '' : 'width: 600px; max-width: 90vw'">
      <q-card-section>
        <div class="text-h6">{{ t('explore_download.title') }}</div>
      </q-card-section>
      <q-separator />
      <q-card-section>
        <div class="text-help q-mb-md">{{ t('explore_download.intro') }}</div>
        <q-banner dense rounded class="bg-orange-1 text-orange-10 q-mb-md">
          <template v-slot:avatar>
            <q-icon name="lock_clock" />
          </template>
          {{
            estimated?.n_embargoed_studies
              ? t('explore_download.embargo_count', { count: estimated.n_embargoed_studies })
              : t('explore_download.embargo')
          }}
        </q-banner>
        <q-spinner-dots v-if="estimating" size="md" />
        <template v-else-if="estimated">
          <div v-if="estimated.n_records === 0" class="text-negative">
            {{ t('explore_download.nothing') }}
          </div>
          <div v-else-if="tooLarge" class="text-negative">
            {{ t('explore_download.too_large', { max: formatNumber(estimated.max_records) }) }}
          </div>
          <div v-else>
            {{
              t('explore_download.estimate', {
                records: formatNumber(estimated.n_records),
                datasets: estimated.n_datasets,
              })
            }}
          </div>
        </template>
        <q-form ref="formRef" class="q-mt-md q-gutter-sm" @submit="onSubmit">
          <q-input
            v-model="email"
            type="email"
            filled
            :label="t('explore_download.email')"
            :hint="t('explore_download.email_hint')"
            :rules="[required, isEmail]"
            lazy-rules
          />
          <q-input
            v-model="title"
            filled
            maxlength="200"
            :label="t('explore_download.name')"
            :hint="t('explore_download.name_hint')"
            :rules="[required]"
            lazy-rules
          />
          <q-input
            v-model="description"
            filled
            type="textarea"
            autogrow
            maxlength="2000"
            :label="t('explore_download.description')"
            :hint="t('explore_download.description_hint')"
            :rules="[required]"
            lazy-rules
          />
        </q-form>
      </q-card-section>
      <q-card-actions align="right">
        <q-btn flat :label="t('explore_download.cancel')" color="secondary" v-close-popup />
        <q-btn
          unelevated
          :label="t('explore_download.submit')"
          color="primary"
          :loading="submitting"
          :disable="!canSubmit"
          @click="formRef?.submit()"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { useQuasar, type QForm } from 'quasar';
import type { DownloadEstimate, DownloadSelection } from '@/models';
import { downloadSelection, estimate, request } from '@/api/download';
import { notifyError, notifySuccess } from '@/utils/notify';

interface DialogProps {
  modelValue: boolean;
}

const props = defineProps<DialogProps>();
const emit = defineEmits(['update:modelValue']);

const { t } = useI18n();
const $q = useQuasar();

const showDialog = ref(props.modelValue);
const formRef = ref<QForm>();
const selection = ref<DownloadSelection>({});
const estimated = ref<DownloadEstimate>();
const estimating = ref(false);
const submitting = ref(false);
const email = ref('');
const title = ref('');
const description = ref('');

const tooLarge = computed(() => !!estimated.value && estimated.value.n_records > estimated.value.max_records);
const canSubmit = computed(() => !!estimated.value && estimated.value.n_records > 0 && !tooLarge.value);

watch(
  () => props.modelValue,
  (value) => {
    showDialog.value = value;
  },
);

function required(value: string) {
  return !!value?.trim() || t('explore_download.required');
}

function isEmail(value: string) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim()) || t('explore_download.email_invalid');
}

function formatNumber(value: number) {
  return value.toLocaleString();
}

function onShow() {
  // the selection is taken when the dialog opens, as the estimate shows it
  selection.value = downloadSelection();
  estimated.value = undefined;
  estimating.value = true;
  estimate(selection.value)
    .then((result) => (estimated.value = result))
    .catch(notifyError)
    .finally(() => (estimating.value = false));
}

function onSubmit() {
  submitting.value = true;
  request({
    ...selection.value,
    email: email.value.trim(),
    title: title.value.trim(),
    description: description.value.trim(),
  })
    .then(() => {
      notifySuccess(t('explore_download.requested', { email: email.value.trim() }));
      title.value = '';
      description.value = '';
      showDialog.value = false;
    })
    .catch(notifyError)
    .finally(() => (submitting.value = false));
}

function onHide() {
  emit('update:modelValue', false);
}
</script>
