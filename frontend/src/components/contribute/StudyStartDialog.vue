<template>
  <q-dialog :maximized="$q.screen.lt.sm" v-model="showDialog" @hide="onHide">
    <q-card :style="$q.screen.lt.sm ? '' : 'width: 500px; max-width: 80vw'">
      <q-card-actions v-if="$q.screen.lt.sm" align="right">
        <q-btn flat icon="close" color="primary" v-close-popup />
      </q-card-actions>
      <q-card-section>
        <q-input
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
  if (!identifier.value) {
    contrib.reset();
  } else if (contrib.study?.identifier !== identifier.value) {
    try {
      await contrib.load(identifier.value);
    } catch (error) {
      console.error(error);
      contrib.reset();
    }
  }
  emit('started');
}

</script>
