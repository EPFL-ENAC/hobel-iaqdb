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
    <div class="text-bold q-mt-md">{{ $t('Contacts') }}</div>
    <div v-for="contact in study?.contacts" :key="contact.email">
      <q-card flat bordered class="q-mt-md">
        <q-card-section class="q-pa-none">
          <fields-list :dbobject="contact" :items="contactItems"/>
        </q-card-section>
        
      </q-card>
    </div>
    <div class="text-bold q-mt-md">{{ $t('Marker paper') }}</div>
    <fields-list :dbobject="study" :items="refItems"/>
    <div class="q-mt-md">
      <div class="text-bold">License</div>
      <div class="on-right q-mt-sm">
        <div class="text-caption">{{ licenseLabel }}</div>
        <div class="text-help q-mt-xs">{{ licenseDescription }}</div>
      </div>
    </div>
    <div class="q-mt-md">
      <div class="text-bold">IAQ ID</div>
      <div class="on-right q-mt-sm text-caption">{{ study?.identifier }}</div>
    </div>
  </div>
</template>


<script lang="ts">
export default defineComponent({
  name: 'StudyDetails',
});
</script>
<script setup lang="ts">
import { licenseOptions } from 'src/utils/options';
import FieldsList, { FieldItem } from 'src/components/FieldsList.vue';
import { Study, Person } from 'src/models';

const catalogStore = useCatalogStore();
const { t } = useI18n();

const study = computed(() => catalogStore.study);

const progress = computed(() => study.value?.start_year > 2024 ? 0 : study.value?.end_year > 2024 ? 0.5 : 1);
const progressLabel = computed(() => progress.value <= 0 ? t('not_started') : progress.value >= 1 ? t('completed') : t('in_progress'))

const licenseLabel = computed(() => licenseOptions.find((lic) => lic.value === 'CC BY-SA')?.label)
const licenseDescription = computed(() => licenseOptions.find((lic) => lic.value === 'CC BY-SA')?.description)

const items: FieldItem<Study>[] = [
  { field: 'building_count', label: 'Building count' },
  { field: 'space_count', label: 'Space count' },
  { field: 'countries', label: 'Countries' },
]

const refItems: FieldItem<Study>[] = [
  {
    field: 'reference',
    label: 'Reference'
  },
  {
    field: 'cite',
    label: 'How to cite'
  },
  {
    field: 'doi',
    label: 'DOI'
  },
]

const contactItems: FieldItem<Person>[] = [
  {
    field: 'contact',
    label: 'Name',
    html: (val: Study) => val.name
  },
  {
    field: 'contact',
    label: 'Email',
    html: (val: Study) => `&lt;<a href="mailto:${val.email}">${val.email}</a>&gt;`
  },
  {
    field: 'contact',
    label: 'Institution',
    html: (val: Study) => val.institution
  },
]

</script>
