<template>
  <q-dialog :maximized="$q.screen.lt.sm" v-model="showDialog" @hide="onHide">
    <q-card :style="$q.screen.lt.sm ? '' : 'width: 1000px; max-width: 80vw'">
      <q-card-actions v-if="$q.screen.lt.sm" align="right">
        <q-btn flat icon="close" color="primary" v-close-popup />
      </q-card-actions>
      <q-card-section>
        <study-stepper
            class="q-mt-md"
            @finish="onFinish"
          />
      </q-card-section>
      <q-card-actions v-if="$q.screen.gt.xs" align="right">
        <q-btn
          flat
          :label="$t('cancel')"
          v-close-popup
        />
        <q-btn
          flat
          :label="$t('save')"
          color="primary"
          v-close-popup
          @click="onSave"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>


<script lang="ts">
export default defineComponent({
  name: 'StudyDraftDialog',
});
</script>
<script setup lang="ts">
import StudyStepper from 'src/components/contribute/StudyStepper.vue';

interface Props {
  modelValue: boolean;
}
const props = defineProps<Props>();
const emit = defineEmits(['update:modelValue', 'saved']);

const showDialog = ref(props.modelValue);

watch(
  () => props.modelValue,
  (value) => {
    showDialog.value = value;
  },
);

function onHide() {
  emit('update:modelValue', false);
}

function onSave() {
  emit('saved');
}
</script>