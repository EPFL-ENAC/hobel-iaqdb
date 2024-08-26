<template>
  <div>
    <q-input
      v-model="space.identifier"
      filled
      :label="$t('study.space.identifier')"
      :hint="$t('study.space.identifier_hint')"
      class="q-mb-md"
    />

    <div class="row q-col-gutter-md">
      <div class="col">
        <q-select
          v-model="space.space"
          :options="spaceTypeOptions"
          filled
          emit-value
          map-options
          :label="$t('study.space.space')"
          :hint="$t('study.space.space_hint')"
        />
      </div>
      <div class="col">
        <q-select
          v-model="space.occupancy"
          :options="occupancyOptions"
          filled
          emit-value
          map-options
          :label="$t('study.space.occupancy')"
          :hint="$t('study.space.occupancy_hint')"
        />
      </div>
    </div>

    <div class="row q-col-gutter-md">
      <div class="col">
        <q-select
          v-model="space.ventilation"
          :options="ventilationOptions"
          filled
          emit-value
          map-options
          :label="$t('study.building.ventilation')"
          :hint="$t('study.building.ventilation_hint')"
        />
      </div>
      <div class="col">
        <q-select
          v-model="space.smoking"
          :options="yesNoOptions"
          filled
          emit-value
          map-options
          :label="$t('study.building.smoking')"
          :hint="$t('study.building.smoking_hint')"
        />
      </div>
    </div>
    
    <div class="text-bold q-mb-md">Periods</div>
    <q-card flat bordered class="q-mb-md bg-white">
      <q-card-section>
        <div v-if="space.periods?.length === 0" class="text-help">No periods defined yet.</div>
        <q-list separator>
          <q-item v-for="(period, i) in space.periods" :key="period.id" class="q-pl-none q-pr-none">
            <q-item-section>
              <period-form v-model="space.periods[i]" class="q-mt-md"/>
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
                @click="onDeletePeriod(i)" />
            </q-item-section>
          </q-item>
        </q-list>
      </q-card-section>
      <q-card-actions class="bg-grey-3 q-pa-md">
        <q-btn @click="onAddPeriod" color="secondary" label="Add Period" icon="add" flat size="sm" />
      </q-card-actions>
    </q-card>

  </div>
</template>


<script lang="ts">
export default defineComponent({
  name: 'SpaceForm',
});
</script>
<script setup lang="ts">
import { spaceTypeOptions, occupancyOptions, ventilationOptions, yesNoOptions } from 'src/utils/options';
import { Building, Space } from 'src/models';
import PeriodForm from 'src/components/contribute/PeriodForm.vue';

interface Props {
  modelValue: Space;
  building: Building;
}
const props = defineProps<Props>();

const contrib = useContributeStore();

const space = ref(props.modelValue);

function onAddPeriod() {
  contrib.addPeriod(props.building.identifier, space.value.identifier);
}

function onDeletePeriod(i: number) {
  contrib.deletePeriod(props.building.identifier, space.value.identifier, i);
}
</script>