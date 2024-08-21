<template>
  <div>
    <div v-if="contrib.study.buildings?.length === 0" class="q-mb-md text-help">No buildings defined yet.</div>
    <q-list separator class="q-mb-md">
      <q-item v-for="(building, i) in contrib.study.buildings" :key="building.id" class="q-pl-none q-pr-none">
        <q-item-section>
          <building-form v-model="contrib.study.buildings[i]" class="q-mt-md"/>
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
    <q-btn @click="onAdd" color="secondary" label="Add building" icon="add" class="q-mb-lg" />
  </div>
</template>


<script lang="ts">
export default defineComponent({
  components: { BuildingForm },
  name: 'BuildingsForm',
});
</script>
<script setup lang="ts">
import BuildingForm from './BuildingForm.vue';
const contrib = useContributeStore();

function onAdd() {
  contrib.addBuilding();
}

function onDelete(i: number) {
  contrib.deleteBuilding(i);
}
</script>