<template>
  <div>
    <q-btn
      color="secondary"
      icon="add"
      label="Add data file"
      @click="onShowDataFile"
    />

    <!-- <pre>{{ contrib.study }}</pre> -->
    <data-file-dialog v-model="showDataFile" />
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

//const contrib = useContributeStore();

const showDataFile = ref(false);

function onShowDataFile() {
  showDataFile.value = true;
}
</script>
