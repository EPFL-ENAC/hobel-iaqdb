<template>
  <div>
    <q-input
      v-model="dataset.name"
      filled
      :label="t('study.dataset.name')"
      :hint="t('study.dataset.name_hint')"
      class="q-mb-md"
    />
    <q-input
      v-model="dataset.description"
      filled
      type="textarea"
      :label="t('study.dataset.description')"
      :hint="t('study.dataset.description_hint')"
      class="q-mb-md"
    />
    <div v-if="dataset.folder.children">
      <template v-for="child in dataset.folder.children" :key="child.path">
        <q-input
          v-model="child.name"
          filled
          readonly
          :label="t('study.dataset.file')"
          :hint="t('study.dataset.file_hint')"
          class="q-mb-md">
          <template v-slot:after>
          <q-btn
            flat
            dense
            round
            icon="edit"
            :disable="uploading"
            :title="t('edit')"
            color="primary"
            @click="onShowDataFile"
          />
          <q-btn
            flat
            dense
            round
            icon="download"
            :disable="uploading"
            :loading="child.path in downloads"
            :percentage="downloads[child.path]"
            :title="t('download')"
            color="primary"
            @click="onDownload(child)"
          />
        </template>
      </q-input>
      </template>
    </div>
    <div class="text-outline text-grey-8">
      {{ t('study.dataset.dictionary') }}
    </div>
    <div class="text-hint">
      {{ t('study.dataset.dictionary_hint') }}
    </div>
    <dataset-variables-form v-model="dataset" />
    <data-file-dialog v-model="showDataFile" update @add="onUpdateDataFile"/>
  </div>
</template>

<script setup lang="ts">
import { isAxiosError } from 'axios';
import DatasetVariablesForm from '@/components/contribute/DatasetVariablesForm.vue';
import DataFileDialog from '@/components/contribute/DataFileDialog.vue';
import type { Dataset, FileNode } from '@/models';
import type { DataFile } from '@/components/models';
import { notifyError } from '@/utils/notify';

const contrib = useContributeStore();

interface Props {
  modelValue: Dataset;
}
const props = defineProps<Props>();

const { t } = useI18n();

const showDataFile = ref(false);
const uploading = ref(false);
/** Percentage received of the files being downloaded, by path. */
const downloads = ref<Record<string, number>>({});

const dataset = ref(props.modelValue);

watch(() => props.modelValue, (val) => {
  dataset.value = val;
});

async function onDownload(file: FileNode) {
  downloads.value[file.path] = 0;
  try {
    await contrib.downloadFile(file, (percentage) => {
      downloads.value[file.path] = percentage;
    });
  } catch (error) {
    // the error body is a blob, as the file would be: no detail to show
    const status = isAxiosError(error) ? error.response?.status : undefined;
    if (status === 403) notifyError('study.dataset.download_forbidden');
    else if (status === 404) notifyError('study.dataset.download_not_found');
    else notifyError(error);
  } finally {
    delete downloads.value[file.path];
  }
}

function onShowDataFile() {
  showDataFile.value = true;
}

async function onUpdateDataFile(dataFile: DataFile) {
  uploading.value = true;
  try {
    dataset.value = await contrib.updateDataset(dataset.value, dataFile);
  } catch (error) {
    notifyError(error);
  } finally {
    uploading.value = false;
  }
}

</script>