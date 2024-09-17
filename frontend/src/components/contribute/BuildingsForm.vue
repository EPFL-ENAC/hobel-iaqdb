<template>
  <div>
    <div v-if="contrib.study.buildings?.length === 0" class="q-mb-md text-help">No buildings defined yet.</div>
    <div v-else>
      <div class="text-hint">
        <q-icon name="info" class="q-mr-xs" />
        <span>{{ $t('study.building_count') }}: {{ buildingCount }}</span> / 
        <span>{{ $t('study.space_count') }}: {{ spaceCount }}</span>
      </div>
      <q-list separator>
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
    </div>
    
    <q-btn @click="onAdd" color="secondary" label="Add building" icon="add"/>
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

const buildingCount = computed(() => contrib.study.buildings?.length || 0);
const spaceCount = computed(() => contrib.study.buildings?.map((b) => b.spaces?.length || 0).reduce((acc, val) => acc + val, 0) || 0);

function onAdd() {
  contrib.addBuilding();
}

function onDelete(i: number) {
  contrib.deleteBuilding(i);
}
</script>