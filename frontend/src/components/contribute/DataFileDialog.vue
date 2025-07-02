<template>
  <q-dialog :maximized="$q.screen.lt.sm" v-model="showDialog" @hide="onHide">
    <q-card :style="$q.screen.lt.sm ? '' : 'width: 1000px; max-width: 90vw'">
      <q-card-actions v-if="$q.screen.lt.sm" align="right">
        <q-btn flat icon="close" color="primary" v-close-popup />
      </q-card-actions>
      <q-card-section>
        <div class=" q-mb-md">
          Select a data file from your computer. If an archive of several files is provided, make sure that all files have the same schema.
        </div>
        <div>
          <q-file
            filled
            v-model="localFile"
            clearable
            label="Data file"
            hint="Select a delimiter-separated format (CSV or TSV) file or a ZIP file containing one or more CSV/TSV files."
            accept=".csv, .tsv, .zip"
            @update:model-value="onFileUpdated"
          />
        </div>
          
        <div v-if="loadingFile" class="q-mt-md">
          <q-spinner-dots size="md"/>
        </div>
        <div v-else-if="localFile && fields.length" class="q-mt-md">
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
      </q-card-section>
      <q-card-actions v-if="$q.screen.gt.xs" align="right">
        <q-btn flat :label="t('cancel')" color="secondary" v-close-popup />
        <q-btn
          :label="update ? t('update') : t('add')"
          color="primary"
          @click="onAddDataFile"
          v-close-popup
          :disable="!isValid"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { useQuasar } from 'quasar';
import { referenceOptions } from 'src/utils/options';
import Papa from 'papaparse';
import { ZipReader, BlobReader } from '@zip.js/zip.js';
import type { DataFile } from 'src/components/models';
import type { Variable } from 'src/models';
import { notifyError } from 'src/utils/notify';
import { LimitedTransformStream } from 'src/utils/streams';

interface Props {
  modelValue: boolean;
  update?: boolean | undefined;
}
const props = defineProps<Props>();
const emit = defineEmits(['update:modelValue', 'add']);

const $q = useQuasar();
const { t } = useI18n();

const step = ref(1);
const showDialog = ref(props.modelValue);
const localFile = ref<File>();
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
    void parseZipFile(localFile.value);
  } else {
    parseDelimitedData(localFile.value);
  }
}

async function parseZipFile(file: File) {
  // Create a FileReader to read the file
  const zipReader = new ZipReader(new BlobReader(file));
  try {
    const csvEntry = (await zipReader.getEntries()).find(entry => entry.filename.endsWith('.csv') || entry.filename.endsWith('.tsv'));
    if (!csvEntry) {
      notifyError('No CSV/TSV entries found in the ZIP archive.');
      loadingFile.value = false;
    } else {
      // Creates a TransformStream object, the content of the first entry in the zip
      // will be written in the `writable` property.
      const csvStream = new LimitedTransformStream();
      // Creates a Promise object resolved to the content of the first entry returned
      // as text from `helloWorldStream.readable`.
      const csvTextPromise = new Response(csvStream.readable).text();
      if (!csvEntry.getData) {
        notifyError('ZIP entry does not support getData method.');
        loadingFile.value = false;
        return;
      }
      await csvEntry.getData(csvStream.writable);

      // Read the content of the CSV file as a text stream
      await csvTextPromise.then((text: string) => {
        // Split the CSV content into lines
        const lines = text.split('\n');
        // Read the header + first 10 lines
        const firstLines = lines.slice(0, 11);
        parseDelimitedData(firstLines.join('\n'));
      });
    }
  } catch (error) {
    notifyError(error);
    loadingFile.value = false;
  } finally {
    void zipReader.close();
  }
}

function parseDelimitedData(csv: File | string) {
  Papa.parse(csv, {
    preview: 10,
    skipEmptyLines: true,
    dynamicTyping: true,
    header: true,
    delimiter: '', // try most common delimiters
    complete: onCSVParseCompleted,
  });
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function onCSVParseCompleted(results: any) {
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
  return matches.length ? matches[0] || 'other' : 'other';
}

function onAddDataFile() {
  const data = {
    file: localFile.value,
    variables: Object.values(dictionary.value),
  } as DataFile;
  emit('add', data);
}
</script>
