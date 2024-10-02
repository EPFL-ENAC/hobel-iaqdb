<template>
  <div>
    <q-input
      v-model="dataset.name"
      filled
      :label="$t('study.dataset.name')"
      :hint="$t('study.dataset.name_hint')"
      class="q-mb-md"
    />
    <q-input
      v-model="dataset.description"
      filled
      type="textarea"
      :label="$t('study.dataset.description')"
      :hint="$t('study.dataset.description_hint')"
      class="q-mb-md"
    />
    <div v-if="dataset.folder.children">
      <template v-for="child in dataset.folder.children" :key="child.path">
        <q-input
          v-model="child.name"
          filled
          readonly
          :label="$t('study.dataset.file')"
          :hint="$t('study.dataset.file_hint')"
          class="q-mb-md">
          <template v-slot:after>
          <q-btn
            flat
            icon="download"
            :title="$t('download')"
            color="primary"
            @click="onDownload(child)"
          />
        </template>
      </q-input>
      </template>
    </div>
    <div class="text-outline text-grey-8">
      {{ $t('study.dataset.dictionary') }}
    </div>
    <div class="text-hint">
      {{ $t('study.dataset.dictionary_hint') }}
    </div>
    <dataset-variables-form v-model="dataset" />
  </div>
</template>


<script lang="ts">
export default defineComponent({
  name: 'DatasetForm',
});
</script>
<script setup lang="ts">
import DatasetVariablesForm from 'src/components/contribute/DatasetVariablesForm.vue';
import { Dataset, FileNode } from 'src/models';

const contrib = useContributeStore();

interface Props {
  modelValue: Dataset;
}
const props = defineProps<Props>();

const dataset = ref(props.modelValue);

watch(() => props.modelValue, (val) => {
  dataset.value = val;
});

function onDownload(file: FileNode) {
  console.log('Download', file);
  contrib.downloadFile(file);
}

</script>