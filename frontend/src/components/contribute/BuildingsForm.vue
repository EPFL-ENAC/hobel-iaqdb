<template>
  <div>
    <div v-if="contrib.study.buildings?.length === 0" class="q-mb-md text-help">
      No buildings defined yet.
      <div class="q-mt-md">
        <q-btn @click="onAdd" color="secondary" label="Add building" icon="add" />
      </div>
    </div>
    <div v-else>
      <div class="text-hint q-mb-md">
        <q-icon name="info" class="q-mr-xs" />
        <span>{{ $t('study.building_count') }}: {{ buildingCount }}</span> /
        <span>{{ $t('study.space_count') }}: {{ spaceCount }}</span>
      </div>
      <div class="row q-gutter-md">
        <div class="col" style="max-width: 200px;">
          <div class="q-mb-md q-mt-sm">
            <div v-for="(building, i) in contrib.study.buildings"
            :key="building.id">
              <q-btn
                flat
                no-caps
                :label="building.identifier"
                align="left"
                size="12px"
                class="full-width"
                :class="`${selected === i ? 'bg-light-blue-1' : ''}`"
                @click="selected = i"
              />
            </div>
          </div>
          <q-btn @click="onAdd" color="secondary" label="Add building" icon="add" size="sm" class="full-width"/>
        </div>
        <div class="col" v-if="selected !== null && contrib.study.buildings">
          <div class="text-bold">
            <q-toolbar>
              <q-icon name="business" class="q-mr-xs" size="sm"/>
              {{ contrib.study.buildings[selected].identifier }}
              <q-space />
              <q-btn
                v-if="selected !== null"
                rounded
                dense
                flat
                color="negative"
                :title="$t('delete')"
                icon="delete"
                @click="onDelete(selected)"
              />
              <q-btn
                v-if="selected !== null"
                rounded
                dense
                flat
                size="sm"
                :title="$t('previous')"
                icon="arrow_back_ios"
                class="on-right"
                :disable="selected === 0"
                @click="selected = selected !== null ? selected - 1 : null"
              />
              <q-btn
                v-if="selected !== null"
                rounded
                dense
                flat
                size="sm"
                :title="$t('next')"
                icon="arrow_forward_ios"
                class="q-ml-xs"
                :disable="selected === buildingCount - 1"
                @click="selected = selected !== null ? selected + 1 : null"
              />
            </q-toolbar>
          </div>
          <q-separator class="q-mb-md"/>
          <building-form
            v-model="contrib.study.buildings[selected]"
          />
        </div>
      </div>
    </div>
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

const selected = ref<number | null>(null);

const buildingCount = computed(() => contrib.study.buildings?.length || 0);
const spaceCount = computed(
  () =>
    contrib.study.buildings
      ?.map((b) => b.spaces?.length || 0)
      .reduce((acc, val) => acc + val, 0) || 0,
);

onMounted(() => {
  if (contrib.study.buildings?.length) {
    selected.value = 0;
  }
});

function onAdd() {
  contrib.addBuilding();
  selected.value = contrib.study.buildings ? contrib.study.buildings.length - 1 : null;
}

function onDelete(i: number) {
  if (!contrib.study.buildings) return;
  if (contrib.study.buildings.length <= 1) {
    selected.value = null;
  } else if (selected.value === contrib.study.buildings.length - 1) {
    selected.value = selected.value ? selected.value - 1 : null;
  }
  contrib.deleteBuilding(i);

}
</script>
