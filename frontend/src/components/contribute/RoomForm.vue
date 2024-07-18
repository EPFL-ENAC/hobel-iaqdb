<template>
  <div>
    <q-input
      v-model="room.identifier"
      filled
      :label="$t('study.room.identifier')"
      :hint="$t('study.room.identifier_hint')"
      class="q-mb-md"
    />

    <div class="row q-col-gutter-md">
      <div class="col">
        <q-select
          v-model="room.space"
          :options="spaceTypeOptions"
          filled
          emit-value
          map-options
          :label="$t('study.room.space')"
          :hint="$t('study.room.space_hint')"
        />
      </div>
      <div class="col">
        <q-select
          v-model="room.occupancy"
          :options="occupancyOptions"
          filled
          emit-value
          map-options
          :label="$t('study.room.occupancy')"
          :hint="$t('study.room.occupancy_hint')"
        />
      </div>
    </div>

    <div class="row q-col-gutter-md">
      <div class="col">
        <q-select
          v-model="room.ventilation"
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
          v-model="room.smoking"
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
        <div v-if="room.periods?.length === 0" class="text-help">No periods defined yet.</div>
        <q-list separator>
          <q-item v-for="(period, i) in room.periods" :key="period._id" class="q-pl-none q-pr-none">
            <q-item-section>
              <period-form v-model="room.periods[i]" class="q-mt-md"/>
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
  name: 'RoomForm',
});
</script>
<script setup lang="ts">
import { spaceTypeOptions, occupancyOptions, ventilationOptions, yesNoOptions } from 'src/utils/options';
import { Building, Room } from 'src/models';
import PeriodForm from 'src/components/contribute/PeriodForm.vue';

interface Props {
  modelValue: Room;
  building: Building;
}
const props = defineProps<Props>();

const contrib = useContributeStore();

const room = ref(props.modelValue);

function onAddPeriod() {
  contrib.addPeriod(props.building.identifier, room.value.identifier);
}

function onDeletePeriod(i: number) {
  contrib.deletePeriod(props.building.identifier, room.value.identifier, i);
}
</script>