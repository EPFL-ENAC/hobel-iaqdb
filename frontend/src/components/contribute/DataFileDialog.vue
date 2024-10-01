<template>
  <q-dialog :maximized="$q.screen.lt.sm" v-model="showDialog" @hide="onHide">
    <q-card :style="$q.screen.lt.sm ? '' : 'width: 800px; max-width: 90vw'">
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
              <q-btn @click="step = 3" color="secondary" label="Next" />
              <q-btn
                flat
                @click="step = 1"
                color="secondary"
                label="Previous"
                class="q-ml-sm"
              />
            </q-stepper-navigation>
          </q-step>

          <q-step
            :name="3"
            title="Fields"
            caption="Data dictionary"
            icon="add_comment"
          >
            <div class="text-help q-mb-md">
              Each column needs to be qualified, using the IAQ data schema.
              Unknown column will be ignored.
            </div>

            <div v-if="warnings.length">
              <q-card bordered class="bg-warning">
                <div>
                  <div class="q-pl-md q-pr-md q-pt-md">
                    <span class="text-bold on-left">Warnings</span>
                    <span>Please fix the following issues as much as possible before proceeding.</span>
                  </div>
                  <ul>
                    <li v-for="msg in warnings" :key="msg">{{ msg }}</li>
                  </ul>
                </div>
              </q-card>
            </div>

            <q-list separator>
              <q-item
                v-for="field in fields"
                :key="field"
                class="q-pl-none q-pr-none"
              >
                <q-item-section>
                  <div class="text-caption text-bold">{{ field }}</div>
                  <div v-if="isTimestamp(dictionary[field].variable)" class="q-mt-sm">
                    <q-input
                      v-model="dictionary[field].format"
                      filled
                      dense
                      label="Format"
                      hint="e.g. YYYY-MM-DD HH:mm:ss"
                      style="max-width: 300px;"
                    />
                  </div>
                </q-item-section>
                <q-item-section side>
                  <q-select
                    v-model="dictionary[field].variable"
                    :options="fieldOptions"
                    emit-value
                    map-options
                  />
                </q-item-section>
              </q-item>
            </q-list>

            <q-stepper-navigation>
              <q-btn
                flat
                @click="step = 2"
                color="secondary"
                label="Previous"
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
import { physicalParameterOptions } from 'src/utils/options';
import Papa from 'papaparse';
import { FileObject, FieldSpec, DataFile } from 'src/components/models';


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
const dictionary = ref<{ [Key: string]: FieldSpec }>({});

const columns = computed(() =>
  fields.value.map((field) => {
    return { name: field, label: field, field };
  }),
);

const fieldOptions = [
  { value: 'building', label: 'Building ID' },
  { value: 'space', label: 'Space ID' },
  { value: 'instrument', label: 'Instrument ID' },
  { value: 'timestamp', label: 'Timestamp' },
  ...physicalParameterOptions,
  { value: 'other', label: 'Other' },
];

function isPhysicalParameter(variable: string) {
  return physicalParameterOptions.find((opt) => opt.value === variable);
}

function isTimestamp(variable: string) {
  return variable === 'timestamp';
}

function isOther(variable: string) {
  return variable === 'other';
}


const warnings = computed(() => {
  const keys = Object.keys(dictionary.value);
  const rval = [];
  if (!keys.find((field) => dictionary.value[field].variable === 'building')) {
    rval.push('Building ID is missing');
  }
  if (!keys.find((field) => dictionary.value[field].variable === 'space')) {
    rval.push('Space ID is missing');
  }
  if (
    !keys.find((field) => dictionary.value[field].variable === 'instrument')
  ) {
    rval.push('Instrument ID is missing');
  }
  if (!keys.find((field) => dictionary.value[field].variable === 'timestamp')) {
    rval.push('Timestamp is missing');
  }
  return rval;
});

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
          field,
          variable: guessFieldVariable(field),
        };
      });
      fields.value = results.meta.fields;
    },
  });
}

function guessFieldVariable(field: string) {
  const matches = fieldOptions
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
    dictionary: Object.values(dictionary.value),
  } as DataFile;
  emit('add', data);
}
</script>
