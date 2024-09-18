<template>
  <div>
    <div class="row q-col-gutter-md">
      <div class="col">
        <q-input
          v-model="person.name"
          filled
          :label="$t('study.person_name')"
          :hint="$t('study.person_name_hint')"
        />
      </div>
      <div class="col">
        <q-input
          v-model="person.email"
          filled
          :label="$t('study.person_email')"
          :hint="$t('study.person_email_hint')"
        />
      </div>
      <div class="col">
        <q-input
          v-model="person.institution"
          filled
          :label="$t('study.person_institution')"
          :hint="$t('study.person_institution_hint')"
        />
      </div>
    </div>
    <q-checkbox
      dense
      v-model="person.email_public"
      :label="$t('study.person_email_public')"
      :hint="$t('study.person_email_public_hint')"
      class="q-mt-md"
    />
  </div>
</template>

<script lang="ts">
export default defineComponent({
  name: 'PersonForm',
});
</script>
<script setup lang="ts">
import { Person } from 'src/models';

interface Props {
  modelValue: Person;
}
const props = defineProps<Props>();

const person = ref(props.modelValue);
</script>
