<template>
  <div>
    <div v-if="instrumentCount === 0" class="q-mb-md text-help">
      No instruments defined yet.
      <div class="q-mt-md">
        <q-btn @click="onAdd" color="secondary" label="Add instrument" icon="add" />
      </div>
    </div>
    <div v-else>
      <div class="row q-gutter-md">
        <div class="col" style="max-width: 200px;">
          <div class="q-mb-md q-mt-sm">
            <div v-for="(instrument, i) in contrib.study.instruments"
            :key="i">
              <q-btn
                flat
                no-caps
                :label="instrument.identifier"
                :title="instrument.identifier"
                align="left"
                size="12px"
                class="full-width ellipsis"
                :class="`${selected === i ? 'bg-light-blue-1' : ''}`"
                @click="selected = i"
              />
            </div>
          </div>
          <q-btn @click="onAdd" color="secondary" label="Add instrument" icon="add" size="sm" class="full-width"/>
        </div>
        <div class="col" v-if="selected !== null && contrib.study.instruments">
          <div class="text-bold">
            <q-toolbar>
              <q-icon name="thermostat" class="q-mr-xs" size="sm"/>
              {{ contrib.study.instruments[selected]?.identifier }}
              <q-space />
              <q-btn
                rounded
                dense
                flat
                :title="t('duplicate')"
                icon="content_copy"
                @click="onDuplicate(selected)"
              />
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
                :disable="selected === instrumentCount - 1"
                @click="selected = selected !== null ? selected + 1 : null"
              />
            </q-toolbar>
          </div>
          <q-separator class="q-mb-md"/>
          <instrument-form v-model="selectedInstrument" class="q-mt-md" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { notifyInfo } from 'src/utils/notify';
import InstrumentForm from './InstrumentForm.vue';
import type { Instrument } from 'src/models';

const { t } = useI18n();
const contrib = useContributeStore();

const selected = ref<number | null>(null);

const instrumentCount = computed(() => contrib.study.instruments?.length || 0);
const selectedInstrument = computed({
  get() {
    if (selected.value !== null && contrib.study.instruments && contrib.study.instruments[selected.value]) {
      return contrib.study.instruments[selected.value] as Instrument;
    }
    return {
      identifier: '',
      manufacturer: '',
      model: '',
      equipment_grade_rating: '',
      placement: '',
      parameters: [],
    };
  },
  set(value: Instrument) {
    if (selected.value !== null && contrib.study.instruments) {
      contrib.study.instruments[selected.value] = value;
    }
  },
});


onMounted(() => {
  if (contrib.study.instruments?.length) {
    selected.value = 0;
  } else {
    contrib.study.instruments = [];
  }
});

function onDuplicate(i: number) {
  if (!contrib.study.instruments) return;
  contrib.addInstrument(contrib.study.instruments[i]);
  selected.value = contrib.study.instruments.length - 1;
  notifyInfo('Instrument duplicated with its parameters');
}

function onAdd() {
  contrib.addInstrument();
  selected.value = contrib.study.instruments ? contrib.study.instruments.length - 1 : null;
  notifyInfo('New instrument added');
}

function onDelete(i: number) {
  if (!contrib.study.instruments) return;
  if (contrib.study.instruments.length <= 1) {
    selected.value = null;
  } else if (selected.value === contrib.study.instruments.length - 1) {
    selected.value = selected.value ? selected.value - 1 : null;
  }
  contrib.deleteInstrument(i);
  notifyInfo('Instrument deleted');
}
</script>
