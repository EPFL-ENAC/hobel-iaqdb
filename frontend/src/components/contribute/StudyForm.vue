<template>
  <div>
    <q-input
      v-model="contrib.study.name"
      filled
      :label="$t('study.name') + ' *'"
      :hint="$t('study.name_hint')"
      :rules="[val => !!val || $t('required')]"
      class="q-mb-md"
    />
    <q-input
      v-model="contrib.study.description"
      filled
      type="textarea"
      :label="$t('study.description')"
      :hint="$t('study.description_hint')"
      class="q-mb-md"
    />
    <q-input
      v-model="contrib.study.website"
      filled
      :label="$t('study.url')"
      :hint="$t('study.url_hint')"
      class="q-mb-md"
    />

    <div class="text-bold q-mb-md">Data collection</div>
    <div class="row q-col-gutter-md q-mb-md">
      <div class="col">
        <q-input
          v-model.number="contrib.study.start_year"
          filled
          type="number"
          :label="$t('study.start_year')"
          :hint="$t('study.start_year_hint')"
        />
      </div>
      <div class="col">
        <q-input
          v-model.number="contrib.study.end_year"
          filled
          type="number"
          :label="$t('study.end_year')"
          :hint="$t('study.end_year_hint')"
        />
      </div>
      <div class="col">
        <q-input
          v-model.number="contrib.study.duration"
          filled
          type="number"
          :label="$t('study.duration')"
          :hint="$t('study.duration_hint')"
        />
      </div>
    </div>
    <div class="row q-col-gutter-md q-mb-md">
      <div class="col">
        <q-input
          v-model.number="contrib.study.building_count"
          filled
          type="number"
          :label="$t('study.building_count')"
          :hint="$t('study.building_count_hint')"
        />
      </div>
      <div class="col">
        <q-input
          v-model.number="contrib.study.space_count"
          filled
          type="number"
          :label="$t('study.space_count')"
          :hint="$t('study.space_count_hint')"
        />
      </div>
    </div>
    <div class="row q-col-gutter-md q-mb-md">
      <div class="col">
        <q-select
          v-model="contrib.study.occupant_impact"
          :options="occupantImpactOptions"
          filled
          emit-value
          map-options
          :label="$t('study.occupant_impact')"
          :hint="$t('study.occupant_impact_hint')"
        />
      </div>
      <div class="col">
        <q-select
          v-model="contrib.study.other_indoor_param"
          :options="otherIndoorParamOptions"
          filled
          emit-value
          map-options
          :label="$t('study.other_indoor_param')"
          :hint="$t('study.other_indoor_param_hint')"
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
            :key="person.id"
            class="q-pl-none q-pr-none"
          >
            <q-item-section>
              <person-form v-model="contrib.study.contributors[i]" />
            </q-item-section>
            <q-item-section side>
              <q-btn
                rounded
                dense
                flat
                color="negative"
                :title="$t('delete')"
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
          :label="$t('study.citation')"
          :hint="$t('study.citation_hint')"
        />
      </div>
      <div class="col">
        <q-input
          v-model="contrib.study.doi"
          filled
          :label="$t('study.doi')"
          :hint="$t('study.doi_hint')"
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
          :label="$t('study.funding')"
          :hint="$t('study.funding_hint')"
          class="q-mb-md"
        />
      </div>
      <div class="col">
        <q-input
          v-model="contrib.study.ethics"
          filled
          type="textarea"
          :label="$t('study.ethics')"
          :hint="$t('study.ethics_hint')"
          class="q-mb-md"
        />
      </div>
      <div class="col">
        <q-select
          v-model="contrib.study.license"
          :options="licenseOptions"
          filled
          emit-value
          map-options
          :label="$t('study.license') + ' *'"
          :hint="$t('study.license_hint')"
          :rules="[val => !!val || $t('required')]"
        >
          <template v-slot:option="scope">
            <q-item v-bind="scope.itemProps">
              <q-item-section>
                <q-item-label>{{ scope.opt.label }}</q-item-label>
                <q-item-label caption style="max-width: 500px">{{
                  scope.opt.description
                }}</q-item-label>
              </q-item-section>
            </q-item>
          </template>
        </q-select>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
export default defineComponent({
  name: 'StudyForm',
});
</script>
<script setup lang="ts">
import PersonForm from './PersonFom.vue';
import {
  occupantImpactOptions,
  otherIndoorParamOptions,
  licenseOptions,
} from 'src/utils/options';
import { notifyError } from 'src/utils/notify';

const contrib = useContributeStore();

function onAddContributor() {
  contrib.addContributor();
}

function onDeleteContributor(i: number) {
  contrib.deleteContributor(i);
}
</script>
