<template>
  <div>
    <div v-if="contrib.study.instruments?.length === 0" class="q-mb-md text-help">No instruments defined yet.</div>
    <q-list separator class="q-mb-md">
      <q-item v-for="(instrument, i) in contrib.study.instruments" :key="instrument.id" class="q-pl-none q-pr-none">
        <q-item-section>
          <instrument-form v-model="contrib.study.instruments[i]" class="q-mt-md"/>
        </q-item-section>

        <q-item-section side>
          <q-btn
            rounded
            dense
            flat
            color="grey-6"
            :title="$t('delete')"
            icon="delete"
            class="q-ml-xs"
            @click="onDelete(i)" />
        </q-item-section>
      </q-item>
    </q-list>
    <q-btn @click="onAdd" color="secondary" label="Add instrument" icon="add" class="q-mb-lg" />
  </div>
</template>


<script lang="ts">
export default defineComponent({
  components: { InstrumentForm },
  name: 'InstrumentsForm',
});
</script>
<script setup lang="ts">
import InstrumentForm from './InstrumentForm.vue';
const contrib = useContributeStore();

function onAdd() {
  contrib.addInstrument();
}

function onDelete(i: number) {
  contrib.deleteInstrument(i);
}
</script>