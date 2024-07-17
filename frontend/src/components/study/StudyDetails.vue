<template>
  <div>
    <div>
      <div>
        <div class="float-left text-bold">{{ study?.start_year }}</div>
        <div class="float-right text-bold">{{ study?.end_year }}</div>
      </div>
      <q-linear-progress stripe size="30px" color="secondary" :value="progress">
        <div class="absolute-full flex flex-center">
          <q-badge color="white" text-color="accent" :label="progressLabel" />
        </div>
      </q-linear-progress>
    </div>
    <fields-list :dbobject="study" :items="items"/>
    <div class="text-bold q-mt-md">{{ $t('Contact') }}</div>
    <fields-list :dbobject="study" :items="contactItems"/>
    <div class="text-bold q-mt-md">{{ $t('Reference') }}</div>
    <fields-list :dbobject="study" :items="refItems"/>
    <div class="q-mt-md">
      <span class="text-bold">IAQ ID</span>: {{ study?.identifier }}
    </div>
  </div>
</template>


<script lang="ts">
export default defineComponent({
  name: 'StudyDetails',
});
</script>
<script setup lang="ts">
import FieldsList, { FieldItem } from 'src/components/FieldsList.vue';
import { Study } from 'src/models';

const catalogStore = useCatalogStore();
const { t } = useI18n();

const study = computed(() => catalogStore.study);

const progress = computed(() => study.value?.start_year > 2024 ? 0 : study.value?.end_year > 2024 ? 0.5 : 1);
const progressLabel = computed(() => progress.value <= 0 ? t('not_started') : progress.value >= 1 ? t('completed') : t('in_progress'))

const items: FieldItem<Study>[] = [
  { field: 'building_count', },
  { field: 'room_count', },
  { field: 'countries', },
]

const refItems: FieldItem<Study>[] = [
  {
    field: 'author',
    label: 'Author'
  },
  {
    field: 'citation',
    label: 'How to cite'
  },
  {
    field: 'doi',
    label: 'DOI'
  },
]

const contactItems: FieldItem<Study>[] = [
  {
    field: 'contact',
    label: 'Name',
    html: (val: Study) => val.contact.name
  },
  {
    field: 'contact',
    label: 'Email',
    html: (val: Study) => `&lt;<a href="mailto:${val.contact.email}">${val.contact.email}</a>&gt;`
  },
  {
    field: 'contact',
    label: 'Institution',
    html: (val: Study) => val.contact.institution
  },
]

</script>
