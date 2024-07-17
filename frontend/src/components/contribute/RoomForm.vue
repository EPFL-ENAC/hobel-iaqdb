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
    
  </div>
</template>


<script lang="ts">
export default defineComponent({
  name: 'BuildingForm',
});
</script>
<script setup lang="ts">
import { spaceTypeOptions, occupancyOptions, ventilationOptions, yesNoOptions } from 'src/utils/options';
import { Room } from 'src/models';

interface Props {
  modelValue: Room;
}
const props = defineProps<Props>();

const room = ref(props.modelValue);
</script>