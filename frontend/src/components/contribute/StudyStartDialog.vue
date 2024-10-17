<template>
  <q-dialog :maximized="$q.screen.lt.sm" v-model="showDialog" @hide="onHide">
    <q-card :style="$q.screen.lt.sm ? '' : 'width: 500px; max-width: 80vw'">
      <q-card-actions v-if="$q.screen.lt.sm" align="right">
        <q-btn flat icon="close" color="primary" v-close-popup />
      </q-card-actions>
      <q-card-section>
        <q-option-group
          v-model="startMode"
          :options="options"
          color="primary"
        />
        <q-input
          v-show="startMode === '_existing'"
          v-model="identifier"
          filled
          :label="$t('study.identifier')"
          :hint="$t('study.identifier_hint')"
        />
      </q-card-section>
      <q-card-actions v-if="$q.screen.gt.xs" align="right">
        <q-btn flat :label="$t('cancel')" color="primary" v-close-popup />
        <q-btn
          :label="$t('start')"
          color="primary"
          :disable="startMode === '_existing' && !identifier"
          @click="doStart"
          v-close-popup
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script lang="ts">
export default defineComponent({
  name: 'StudyStartDialog',
});
</script>
<script setup lang="ts">

const contrib = useContributeStore();

interface Props {
  modelValue: boolean;
}
const props = defineProps<Props>();
const emit = defineEmits(['update:modelValue', 'started']);

const showDialog = ref(props.modelValue);
const identifier = ref('');

const startMode = ref('_draft');
const options = [
  { label: 'New Study', value: '_draft' },
  { label: 'Existing Study', value: '_existing' },
];

watch(
  () => props.modelValue,
  (value) => {
    showDialog.value = value;
    if (contrib.study?.identifier) {
      identifier.value = contrib.study.identifier;
    } else {
      identifier.value = '';
    }
  },
);

function onHide() {
  emit('update:modelValue', false);
}

async function doStart() {
  if (startMode.value === '_draft' || !identifier.value) {
    contrib.reset();
  } else if (identifier.value !== '_draft') {
    try {
      // reload
      await contrib.load(identifier.value);
    } catch (error) {
      console.error(error);
      contrib.reset();
    }
  }
  emit('started');
}

</script>
