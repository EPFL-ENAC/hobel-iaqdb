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
            <div v-for="(dataset, i) in contrib.study.datasets" :key="dataset.id">
              <q-btn
                flat
                no-caps
                :label="dataset.name"
                :disable="uploading"
                align="left"
                size="12px"
                class="full-width"
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
                {{ contrib.study.datasets[selected].name }}
                <q-space />
                <q-btn
                  v-if="selected !== null"
                  rounded
                  dense
                  flat
                  color="negative"
                  :title="$t('delete')"
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
                  :title="$t('previous')"
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
                  :title="$t('next')"
                  icon="arrow_forward_ios"
                  class="q-ml-xs"
                  :disable="selected === datasetCount - 1"
                  @click="selected = selected !== null ? selected + 1 : null"
                />
              </q-toolbar>
            </div>
            <q-separator class="q-mb-md"/>
            <dataset-form v-if="selected !== null" v-model="contrib.study.datasets[selected]"/>
          </div>
        </div>
      </div>
    </div>
    
    <data-file-dialog v-model="showDataFile" @add="onAddDataFile"/>
  </div>
</template>

<script lang="ts">
export default defineComponent({
  components: { DataFileDialog },
  name: 'DatasetsForm',
});
</script>
<script setup lang="ts">
import DataFileDialog from 'src/components/contribute/DataFileDialog.vue';
import DatasetForm from 'src/components/contribute/DatasetForm.vue';
import { DataFile } from 'src/components/models';

const contrib = useContributeStore();

const showDataFile = ref(false);
const selected = ref<number | null>(null);
const uploading = ref(false);

const datasetCount = computed(() => contrib.study.datasets?.length || 0);

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
  await contrib.addDataset(dataFile);
  uploading.value = false;
  selected.value = contrib.study.datasets ? contrib.study.datasets.length - 1 : null;
}

function onDelete(i: number) {
  if (!contrib.study.datasets) return;
  if (contrib.study.datasets.length <= 1) {
    selected.value = null;
  } else if (selected.value === contrib.study.datasets.length - 1) {
    selected.value = selected.value ? selected.value - 1 : null;
  }
  contrib.deleteDataset(i);
}
</script>
