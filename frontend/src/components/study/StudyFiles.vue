<template>
  <div>
    <div class="row">
      <div class="col">
        <q-btn
        color="primary"
        icon="download"
        no-caps
        :label="$t('download')"
        class="" />
      </div>
      <div class="col">
        <q-input ref="filterRef" v-model="filter" label="Filter" style="width: 200px">
        <template v-slot:append>
          <q-icon v-if="filter !== ''" name="clear" class="cursor-pointer" @click="resetFilter" />
        </template>
      </q-input>
      </div>
      
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
const filter = ref('');
const filterRef = ref(null);

const simple = [
    {
      label: 'Satisfied customers',
      children: [
        {
          label: 'Good food',
          children: [
            { label: 'Quality ingredients' },
            { label: 'Good recipe' }
          ]
        },
        {
          label: 'Good service (disabled node)',
          disabled: true,
          children: [
            { label: 'Prompt attention' },
            { label: 'Professional waiter' }
          ]
        },
        {
          label: 'Pleasant surroundings',
          children: [
            { label: 'Happy atmosphere' },
            { label: 'Good table presentation' },
            { label: 'Pleasing decor' }
          ]
        }
      ]
    }
  ]

function resetFilter () {
  filter.value = ''
}

</script>