<template>
  <div>
    <q-input
      v-model="contrib.study.name"
      filled
      :label="t('study.name') + ' *'"
      :hint="t('study.name_hint')"
      :rules="[val => !!val || t('required')]"
      class="q-mb-md"
    />
    <q-input
      v-model="contrib.study.description"
      filled
      type="textarea"
      :label="t('study.description')"
      :hint="t('study.description_hint')"
      class="q-mb-md"
    />
    <q-input
      v-model="contrib.study.website"
      filled
      :label="t('study.url')"
      :hint="t('study.url_hint')"
      class="q-mb-md"
    />

    <div class="text-bold q-mb-md">Data collection</div>
    <div class="row q-col-gutter-md q-mb-md">
      <div class="col">
        <q-input
          v-model.number="contrib.study.start_year"
          filled
          type="number"
          :min="1900"
          :max="new Date().getFullYear()"
          :label="t('study.start_year')"
          :hint="t('study.start_year_hint')"
        />
      </div>
      <div class="col">
        <q-input
          v-model.number="contrib.study.end_year"
          filled
          type="number"
          :min="1900"
          :max="new Date().getFullYear()"
          :label="t('study.end_year')"
          :hint="t('study.end_year_hint')"
        />
      </div>
      <div class="col">
        <q-input
          v-model.number="contrib.study.duration"
          filled
          type="number"
          :min="0"
          :label="t('study.duration')"
          :hint="t('study.duration_hint')"
        />
      </div>
    </div>
    <div class="row q-col-gutter-md q-mb-md">
      <div class="col">
        <q-select
          v-model="occupant_impacts"
          :options="occupantImpactOptions"
          filled
          multiple
          emit-value
          map-options
          :label="t('study.occupant_impact')"
          :hint="t('study.occupant_impact_hint')"
          @update:model-value="contrib.study.occupant_impact = $event.join(',')"
        />
      </div>
      <div class="col">
        <q-select
          v-model="other_indoor_params"
          :options="otherIndoorParamOptions"
          filled
          multiple
          emit-value
          map-options
          :label="t('study.other_indoor_param')"
          :hint="t('study.other_indoor_param_hint')"
          @update:model-value="contrib.study.other_indoor_param = $event.join(',')"
        />
      </div>
    </div>

    <div class="text-bold q-mb-sm q-mt-lg">Data contributors</div>
    <div class="text-help q-mb-sm">
      Information about the data contributors who may be contacted for further
      details.
    </div>
    <q-card flat bordered class="q-mb-md bg-grey-2">
      <q-card-section>
        <div v-if="contrib.study.contributors?.length === 0" class="text-help">
          No contributors defined yet.
        </div>
        <q-list v-if="contrib.study.contributors?.length" separator>
          <q-item
            v-for="(person, i) in contrib.study.contributors"
            :key="i"
            class="q-pl-none q-pr-none"
          >
            <q-item-section>
              <person-form v-if="contrib.study.contributors[i]" v-model="contrib.study.contributors[i]" />
            </q-item-section>
            <q-item-section side>
              <q-btn
                rounded
                dense
                flat
                color="negative"
                :title="t('delete')"
                icon="delete"
                class="q-ml-xs"
                @click="onDeleteContributor(i)"
              />
            </q-item-section>
          </q-item>
        </q-list>
      </q-card-section>
      <q-card-actions class="bg-grey-3 q-pa-md">
        <q-btn
          @click="onAddContributor"
          color="secondary"
          label="Add contributor"
          icon="add"
          size="sm"
        />
      </q-card-actions>
    </q-card>
    <div class="text-bold q-mb-md">Publication reference</div>
    <div class="row q-col-gutter-md q-mb-md">
      <div class="col">
        <q-input
          v-model="contrib.study.citation"
          filled
          type="textarea"
          :label="t('study.citation')"
          :hint="t('study.citation_hint')"
        />
      </div>
      <div class="col">
        <q-input
          v-model="contrib.study.doi"
          filled
          :label="t('study.doi')"
          :hint="t('study.doi_hint')"
        />
      </div>
    </div>

    <div class="text-bold q-mb-md">Other information</div>
    <div class="row q-col-gutter-md q-mb-md">
      <div class="col">
        <q-input
          v-model="contrib.study.funding"
          filled
          type="textarea"
          :label="t('study.funding')"
          :hint="t('study.funding_hint')"
          class="q-mb-md"
        />
      </div>
      <div class="col">
        <q-input
          v-model="contrib.study.ethics"
          filled
          type="textarea"
          :label="t('study.ethics')"
          :hint="t('study.ethics_hint')"
          class="q-mb-md"
        />
      </div>
      <div class="col">
        <q-input
          v-model="contrib.study.data_processing"
          filled
          type="textarea"
          :label="t('study.data_processing')"
          :hint="t('study.data_processing_hint')"
          class="q-mb-md"
        />
      </div>
    </div>
    <div class="row q-col-gutter-md q-mb-md">
      <div class="col">
        <q-checkbox
          v-model="license_accepted"
          dense
          :label="t('study.license_accept')"
          @update:model-value="onToggleLicenseAccepted"
        />
        <q-markdown class="text-hint q-mt-sm" :src="t('study.license_accept_hint')" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import PersonForm from './PersonFom.vue';
import {
  occupantImpactOptions,
  otherIndoorParamOptions,
} from 'src/utils/options';

const { t } = useI18n();
const contrib = useContributeStore();

const occupant_impacts = ref<string[]>([]);
const other_indoor_params = ref<string[]>([]);
const license_accepted = ref(false);

onMounted(
  () => {
    if (contrib.study.occupant_impact) {
      if (typeof contrib.study.occupant_impact === 'string') {
        occupant_impacts.value = (contrib.study.occupant_impact as string).split(',');
      }
    } else {
      occupant_impacts.value = [];
    }
    if (contrib.study.other_indoor_param) {
      if (typeof contrib.study.other_indoor_param === 'string') {
        other_indoor_params.value = (contrib.study.other_indoor_param as string).split(',');
      }
    } else {
      other_indoor_params.value = [];
    }
    license_accepted.value = contrib.study.license === 'PDDL';
  },
);

watch(
  () => contrib.study,
  (study) => {
    license_accepted.value = study.license === 'PDDL';
  },
);

function onToggleLicenseAccepted() {
  if (license_accepted.value) {
    contrib.study.license = 'PDDL';
  } else {
    contrib.study.license = '';
  }
}

function onAddContributor() {
  contrib.addContributor();
}

function onDeleteContributor(i: number) {
  contrib.deleteContributor(i);
}
</script>
