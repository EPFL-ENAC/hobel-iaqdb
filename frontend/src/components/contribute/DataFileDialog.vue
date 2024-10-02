<template>
  <q-dialog :maximized="$q.screen.lt.sm" v-model="showDialog" @hide="onHide">
    <q-card :style="$q.screen.lt.sm ? '' : 'width: 1000px; max-width: 90vw'">
      <q-card-actions v-if="$q.screen.lt.sm" align="right">
        <q-btn flat icon="close" color="primary" v-close-popup />
      </q-card-actions>
      <q-card-section>
        <q-stepper flat v-model="step" vertical color="secondary" animated>
          <q-step
            :name="1"
            title="Select data file"
            icon="settings"
            :done="step > 1"
          >
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
                hint="Select a delimiter-separated format (CSV or TSV)."
                accept=".csv, .tsv"
                @update:model-value="onFileUpdated"
              />
            </div>

            <q-stepper-navigation>
              <q-btn
                @click="step = 2"
                color="secondary"
                label="Next"
                :disable="!localFile"
              />
            </q-stepper-navigation>
          </q-step>

          <q-step
            :name="2"
            title="Preview data"
            icon="create_new_folder"
            :done="step > 2"
          >
            <div class="text-help q-mb-md">
              Verify that the data were correctly read before proceeding to the
              next step. Note that is only a preview of the 10 first lines.
            </div>

            <div>
              <q-table
                :rows="rows"
                :columns="columns"
                flat
                bordered
                table-header-class="text-bold"
              />
            </div>

            <q-stepper-navigation>
              <q-btn
                flat
                @click="step = 1"
                color="secondary"
                label="Previous"
                class="q-ml-sm"
              />
            </q-stepper-navigation>
          </q-step>

        </q-stepper>
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
import { FileObject, DataFile } from 'src/components/models';
import { Variable } from 'src/models';

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

const columns = computed(() =>
  fields.value.map((field) => {
    return { name: field, label: field, field };
  }),
);

const isValid = computed(() => localFile.value);

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
  if (!localFile.value) return;
  fields.value = [];
  rows.value = [];
  dictionary.value = {};
  Papa.parse(localFile.value, {
    preview: 10,
    skipEmptyLines: true,
    dynamicTyping: true,
    header: true,
    complete: function (results) {
      //console.log(results);
      rows.value = results.data;
      results.meta.fields.forEach((field: string) => {
        dictionary.value[field] = {
          name: field,
          type: 'text',
          reference: guessFieldReference(field),
        };
      });
      fields.value = results.meta.fields;
    },
  });
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
