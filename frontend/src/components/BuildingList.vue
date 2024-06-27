<template>
  <div>
    <pre>{{ rows }}</pre>

  </div>
</template>

<script lang="ts">
export default defineComponent({
  name: 'BuildingList',
});
</script>
<script setup lang="ts">
const catalogStore = useCatalogStore();
const filtersStore = useFiltersStore();

const rows = ref([])

onMounted(async () => {
  rows.value = await catalogStore.loadBuildings()
})
</script>