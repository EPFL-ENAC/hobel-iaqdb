<template>
  <q-dialog :maximized="$q.screen.lt.sm" v-model="showDialog" @hide="onHide">
    <q-card :style="$q.screen.lt.sm ? '' : 'width: 1000px; max-width: 90vw'">
      <q-card-actions v-if="$q.screen.lt.sm" align="right">
        <q-btn flat icon="close" color="primary" v-close-popup />
      </q-card-actions>
      <q-card-section>
        <div class="text-help q-mb-md">
          Select a data file from your computer. The file will not be
          uploaded at this point.
        </div>
        <div>
          <q-file
            filled
            v-model="localFile"
            clearable
            label="Data file"
            hint="Select a delimiter-separated format (CSV or TSV) file or a ZIP file containing one or more CSV/TSV files that use the same schema."
            accept=".csv, .tsv, .zip"
            @update:model-value="onFileUpdated"
          />
        </div>
          
        <div v-if="loadingFile" class="q-mt-md">
          <q-spinner-dots size="md"/>
        </div>
        <div v-else-if="localFile" class="q-mt-md">
          <div v-if="fields">
            <div class="text-help q-mb-md">
              Verify that the data were correctly read before proceeding to the
              file upload. Note that is only a preview of the 10 first lines.
            </div>
            <q-table
              :rows="rows"
              :columns="columns"
              flat
              bordered
              table-header-class="text-bold"
              v-model:pagination="pagination"
            />
          </div>
        </div>
      </q-card-section>
      <q-card-actions v-if="$q.screen.gt.xs" align="right">
        <q-btn flat :label="$t('cancel')" color="primary" v-close-popup />
        <q-btn
          :label="$t('add')"
          color="primary"
          @click="onAddDataset"
          v-close-popup
          :disable="!isValid"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script lang="ts">
export default defineComponent({
  name: 'DataFileDialog',
});
</script>
<script setup lang="ts">
import { referenceOptions } from 'src/utils/options';
import Papa from 'papaparse';
import JSZip from 'jszip';
import { FileObject, DataFile } from 'src/components/models';
import { Variable } from 'src/models';
import { notifyError } from 'src/utils/notify';

interface Props {
  modelValue: boolean;
}
const props = defineProps<Props>();
const emit = defineEmits(['update:modelValue', 'add', 'cancel']);

const step = ref(1);
const showDialog = ref(props.modelValue);
const localFile = ref<FileObject>();
const fields = ref([]);
const rows = ref([]);
const dictionary = ref<{ [Key: string]: Variable }>({});
const loadingFile = ref(false);
const pagination = ref({
  sortBy: 'id',
  descending: false,
  page: 1,
  rowsPerPage: 5,
});

const columns = computed(() =>
  fields.value.map((field) => {
    return { name: field, label: field, field };
  }),
);

const isValid = computed(() => localFile.value && fields.value.length > 0);

watch(
  () => props.modelValue,
  (value) => {
    showDialog.value = value;
    step.value = 1;
    localFile.value = undefined;
    rows.value = [];
    fields.value = [];
  },
);

function onHide() {
  emit('update:modelValue', false);
}

function onFileUpdated() {
  if (!localFile.value) {
    loadingFile.value = false;
    return;
  }
  fields.value = [];
  rows.value = [];
  dictionary.value = {};
  pagination.value.page = 1;
  loadingFile.value = true;
  if (localFile.value.type === 'application/zip') {
    parseZipFile(localFile.value);
  } else {
    parseDelimitedData(localFile.value);
  }
}

function parseZipFile(file: FileObject) {
  // Create a FileReader to read the file
  const reader = new FileReader();
  reader.onload = function (e) {
    if (!e.target?.result) {
      notifyError('No file content found.');
      loadingFile.value = false;
      return;
    }
    // Pass the ZIP data to JSZip
    JSZip.loadAsync(e.target.result).then(zip => {
      // Assume there is only one CSV file in the zip
      console.log(zip.files);
      const csvFile = Object.keys(zip.files).find(fileName => fileName.endsWith('.csv'));
      // Read the CSV file content
      if (csvFile) {
        zip.file(csvFile)?.async('string').then(content => {
          // Split CSV content into lines
          const lines = content.split('\n');
          // Get the first 10 lines (+header)
          const firstLines = [];
          for (let i = 0; i < lines.length && i < 11; i++) {
            firstLines.push(lines[i]);
          }
          parseDelimitedData(firstLines.join('\n'));
        });
      } else {
        notifyError('No CSV file found in the ZIP archive.');
        loadingFile.value = false;
      }
    }).catch(error => {
      notifyError('Error reading ZIP file: ' + error.message);
      loadingFile.value = false;
    });
  };
  // Read the file as an ArrayBuffer (required for JSZip)
  reader.readAsArrayBuffer(file);
}

function parseDelimitedData(csv: FileObject | string) {
  Papa.parse(csv, {
    preview: 10,
    skipEmptyLines: true,
    dynamicTyping: true,
    header: true,
    delimiter: ',',
    complete: onCSVParseCompleted,
  });
}

function onCSVParseCompleted(results) {
  if (results.errors?.length) {
    notifyError(results.errors);
    loadingFile.value = false;
    return;
  }
  rows.value = results.data;
  results.meta.fields.forEach((field: string) => {
    dictionary.value[field] = {
      name: field,
      type: 'text',
      reference: guessFieldReference(field),
    };
  });
  fields.value = results.meta.fields;
  loadingFile.value = false;
}

function guessFieldReference(field: string) {
  const matches = referenceOptions
    .map((opt) => {
      return {
        value: opt.value,
        re: new RegExp(opt.value, 'gi'),
      };
    })
    .map((optRe) => {
      return field.match(optRe.re) != null ? optRe.value : null;
    })
    .filter((opt) => opt != null);
  return matches.length ? matches[0] : 'other';
}

function onAddDataset() {
  const data = {
    file: localFile.value,
    variables: Object.values(dictionary.value),
  } as DataFile;
  emit('add', data);
}
</script>
