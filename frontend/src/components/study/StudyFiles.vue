<template>
  <div>
    <div class="row">
      <q-btn
        flat
        color="primary"
        icon="download"
        no-caps
        :label="$t('download')"
        class="" />
      <q-space />
      <q-input ref="filterRef" v-model="filter" label="Filter" style="width: 200px" dense>
        <template v-slot:append>
          <q-icon v-if="filter !== ''" name="clear" class="cursor-pointer" @click="resetFilter" />
        </template>
      </q-input>
    </div>

    <q-card flat bordered class="q-mt-md bg-grey-2">
      <q-card-section>
        <q-tree
          :nodes="simple"
          node-key="label"
          :filter="filter"
          default-expand-all
        />
        </q-card-section>
      </q-card>
  </div>
</template>


<script lang="ts">
export default defineComponent({
  name: 'StudyFiles',
});
</script>
<script setup lang="ts">

const catalogStore = useCatalogStore();

const filter = ref('');
const filterRef = ref(null);

const study = computed(() => catalogStore.study);

const simple = computed(() =>  [
    {
      label: study.value?.name,
      children: [
        { label: 'README.md' },
        { label: 'License.md' },
        { label: 'study.json' },
        {
          label: 'datasets',
          children: [
            'co2_atmotube',
            'pm_atmotube',
            'ufp_discmini',
            'co2_rotronic',
            'radon_radonscout',
          ].map((ds) => {
            return {
              label: ds,
              children:[
                { label: 'dictionary.json' },
                { label: 'data.csv' },
                { label: 'dataset.json' }
              ]
            }
          })
        },
      ]
    }
  ]);

function resetFilter () {
  filter.value = ''
}

</script>