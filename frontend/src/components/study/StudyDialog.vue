<template>
  <q-dialog :maximized="$q.screen.lt.sm" v-model="showDialog" @hide="onHide">
    <q-card :style="$q.screen.lt.sm ? '' : `width: '500px'; max-width: 80vw`">
      <q-card-actions v-if="$q.screen.lt.sm" align="right">
        <q-btn flat icon="close" color="primary" v-close-popup />
      </q-card-actions>
      <q-card-section>
        <q-card flat bordered class="q-mt-md bg-grey-3 q-mb-md">
          <q-card-section>
            <q-markdown :src="study?.description" />
          </q-card-section>
        </q-card>
      </q-card-section>
      <q-card-section>
        <study-tabs :show-map="false" />
      </q-card-section>
      <q-card-actions v-if="$q.screen.gt.xs" align="right">
        <q-btn flat :label="t('close')" color="primary" v-close-popup />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { useQuasar } from 'quasar';
import StudyTabs from 'src/components/study/StudyTabs.vue';

const catalogStore = useCatalogStore();

interface Props {
  modelValue: boolean;
}
const props = defineProps<Props>();
const emit = defineEmits(['update:modelValue']);

const $q = useQuasar();
const { t } = useI18n();

const showDialog = ref(props.modelValue);

const study = computed(() => catalogStore.study);

watch(
  () => props.modelValue,
  (value) => {
    showDialog.value = value;
  },
);

function onHide() {
  emit('update:modelValue', false);
}
</script>
