<template>
  <div>
    <q-input
      v-model="contrib.study.name"
      filled
      :label="$t('study.name')"
      :hint="$t('study.name_hint')"
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
      v-model="contrib.study.url"
      filled
      :label="$t('study.url')"
      :hint="$t('study.url_hint')"
      class="q-mb-md"
    />

    <div class="text-bold q-mb-md">Time range</div>
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

    <div class="text-bold q-mb-sm q-mt-lg">Data contributor</div>
    <div class="text-help q-mb-md">Information about the principal contact person regarding the data.</div>
    <div class="row q-col-gutter-md q-mb-md">
      <div class="col">
        <q-input
          v-model="contrib.study.contact.name"
          filled
          :label="$t('study.contact_name')"
          :hint="$t('study.contact_name_hint')"
        />  
      </div>
      <div class="col">
        <q-input
          v-model="contrib.study.contact.email"
          filled
          :label="$t('study.contact_email')"
          :hint="$t('study.contact_email_hint')"
        />  
      </div>
      <div class="col">
        <q-input
          v-model="contrib.study.contact.institution"
          filled
          :label="$t('study.contact_institution')"
          :hint="$t('study.contact_institution_hint')"
        />  
      </div>
    </div>

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
  </div>
</template>


<script lang="ts">
export default defineComponent({
  name: 'StudyForm',
});
</script>
<script setup lang="ts">
const contrib = useContributeStore();
</script>