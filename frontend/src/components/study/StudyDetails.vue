<template>
  <div>
    <div>
      <div>
        <div class="float-left text-bold">{{ study?.start_year }}</div>
        <div class="float-right text-bold">{{ study?.end_year }}</div>
      </div>
      <q-linear-progress animation-speed="0" size="30px" color="secondary" :value="progress">
        <div class="absolute-full flex flex-center">
          <q-badge color="white" text-color="accent" :label="progressLabel" />
        </div>
      </q-linear-progress>
    </div>
    <fields-list :dbobject="study" :items="items" />
    <div class="text-bold q-mt-md">{{ $t('Contributors') }}</div>
    <template
      v-for="contributor in study?.contributors"
      :key="contributor.email"
    >
      <fields-list :dbobject="contributor" :items="contactItems" />
    </template>
    <div class="text-bold q-mt-md">{{ $t('Marker paper') }}</div>
    <fields-list :dbobject="study" :items="refItems" />
    <div class="q-mt-md">
      <div class="text-bold">{{ $t('study.license') }}</div>
      <div class="on-right q-mt-sm">
        <div class="text-caption">{{ licenseLabel }}</div>
        <div class="text-help q-mt-xs">{{ licenseDescription }}</div>
      </div>
    </div>
    <div class="q-mt-md">
      <div class="text-bold">IAQ ID</div>
      <q-btn flat class="q-mt-sm text-caption" icon-right="link" no-caps :to="`/study?id=${study?.identifier}`" :label="study?.identifier"> </q-btn>
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

const currentYear = new Date().getFullYear();

const study = computed(() => catalogStore.study);

const progress = computed(() => {
  if (!study.value) return 0;
  if (!study.value.end_year) return 0.5;
  if (!study.value.start_year) return study.value.end_year > currentYear ? 0.5 : 1;
  return study.value.start_year > currentYear ? 0 : study.value.end_year > currentYear ? 0.5 : 1;
});
const progressLabel = computed(() =>
  progress.value <= 0
    ? t('not_started')
    : progress.value >= 1
      ? t('completed')
      : t('in_progress'),
);

const licenseLabel = computed(
  () => licenseOptions.find((lic) => lic.value === study.value?.license)?.label,
);
const licenseDescription = computed(
  () => licenseOptions.find((lic) => lic.value === study.value?.license)?.description,
);

const items: FieldItem<Study>[] = [
  {
    field: 'website',
    label: 'Website',
    html: (val: Study) =>
      val.website ? `<a href="${val.website}" target="_blank" class="epfl">${val.website}</a>` : '-',
  },
];

const refItems: FieldItem<Study>[] = [
  {
    field: 'citation',
    label: 'Citation',
  },
  {
    field: 'doi',
    label: 'DOI',
    html: (val: Study) =>
      val.doi ? `<a href="${val.doi.startsWith('http') ? val.doi : 'https://doi.org/' + val.doi}" target="_blank" class="epfl">${val.doi}</a>` : '-',
  },
];

const contactItems: FieldItem<Person>[] = [
  {
    field: 'contact',
    label: 'Name',
    html: (val: Person) => val.name + (val.email_public ? ` &lt;<a href="mailto:${val.email}" class="epfl">${val.email}</a>&gt;` : ''),
  },
  {
    field: 'contact',
    label: 'Institution / Company',
    html: (val: Person) => val.institution,
  },
];
</script>
