<template>
  <div>
    <div v-if="datasetCount === 0" class="q-mb-md text-help">
      No datasets defined yet.
      <div class="q-mt-md">
        <q-btn
          color="secondary"
          icon="add"
          label="Add dataset"
          :disable="uploading"
          @click="onShowDataFile"
        />
        <q-spinner-dots v-if="uploading" size="md" class="q-ml-md"/>
      </div>
    </div>
    <div v-else>
      <div class="row q-gutter-md">
        <div class="col" style="max-width: 200px;">
          <div class="q-mb-md q-mt-sm">
            <div v-for="(dataset, i) in contrib.study.datasets" :key="i">
              <q-btn
                flat
                no-caps
                :label="dataset.name"
                :title="dataset.name"
                :disable="uploading"
                align="left"
                size="12px"
                class="full-width ellipsis"
                :class="`${selected === i ? 'bg-light-blue-1' : ''}`"
                @click="selected = i"
              />
            </div>
          </div>
          <q-btn
            @click="onShowDataFile"
            :disable="uploading"
            color="secondary"
            label="Add dataset"
            icon="add"
            size="sm"
            class="full-width"
          />

        </div>
        <div class="col" v-if="selected !== null && contrib.study.datasets">
          <q-spinner-dots v-if="uploading" size="md" class="q-ml-md"/>
          <div v-else>
            <div class="text-bold">
              <q-toolbar>
                <q-icon name="description" class="q-mr-xs" size="sm"/>
                {{ contrib.study.datasets[selected]?.name }}
                <q-space />
                <q-btn
                  v-if="selected !== null"
                  rounded
                  dense
                  flat
                  color="negative"
                  :title="t('delete')"
                  icon="delete"
                  class="q-ml-xs"
                  @click="onDelete(selected)"
                />
                <q-btn
                  v-if="selected !== null"
                  rounded
                  dense
                  flat
                  size="sm"
                  :title="t('previous')"
                  icon="arrow_back_ios"
                  class="on-right"
                  :disable="selected === 0"
                  @click="selected = selected !== null ? selected - 1 : null"
                />
                <q-btn
                  v-if="selected !== null"
                  rounded
                  dense
                  flat
                  size="sm"
                  :title="t('next')"
                  icon="arrow_forward_ios"
                  class="q-ml-xs"
                  :disable="selected === datasetCount - 1"
                  @click="selected = selected !== null ? selected + 1 : null"
                />
              </q-toolbar>
            </div>
            <q-separator class="q-mb-md"/>
            <dataset-form v-model="selectedDataset" />
          </div>
        </div>
      </div>
    </div>
    
    <data-file-dialog v-model="showDataFile" @add="onAddDataFile"/>
  </div>
</template>

<script setup lang="ts">
import DataFileDialog from 'src/components/contribute/DataFileDialog.vue';
import DatasetForm from 'src/components/contribute/DatasetForm.vue';
import type { DataFile } from 'src/components/models';
import { notifyError } from 'src/utils/notify';
import type { Dataset, FileNode } from 'src/models';

const { t } = useI18n();
const contrib = useContributeStore();

const showDataFile = ref(false);
const selected = ref<number | null>(null);
const uploading = ref(false);

const datasetCount = computed(() => contrib.study.datasets?.length || 0);

const selectedDataset = computed({
  get() {
    if (
      selected.value !== null &&
      contrib.study.datasets &&
      contrib.study.datasets[selected.value]
    ) {
      return contrib.study.datasets[selected.value] as Dataset;
    }
    // Return a default Dataset object if undefined (adjust fields as needed)
    return {
      name: '',
      description: '',
      folder: {} as FileNode,
      variables: [],
    };
  },
  set(val: Dataset) {
    if (
      selected.value !== null &&
      contrib.study.datasets &&
      contrib.study.datasets[selected.value]
    ) {
      contrib.study.datasets[selected.value] = val;
    }
  },
});

onMounted(() => {
  if (contrib.study.datasets?.length) {
    selected.value = 0;
  }
});

function onShowDataFile() {
  showDataFile.value = true;
}

async function onAddDataFile(dataFile: DataFile) {
  uploading.value = true;
  try {
    await contrib.addDataset(dataFile);
    selected.value = contrib.study.datasets ? contrib.study.datasets.length - 1 : null;
  } catch (error) {
    notifyError(error);
  } finally {
    uploading.value = false;
  }
}

function onDelete(i: number) {
  if (!contrib.study.datasets) return;
  if (contrib.study.datasets.length <= 1) {
    selected.value = null;
  } else if (selected.value === contrib.study.datasets.length - 1) {
    selected.value = selected.value ? selected.value - 1 : null;
  }
  void contrib.deleteDataset(i);
}
</script>
