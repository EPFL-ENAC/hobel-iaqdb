<template>
  <q-page>
    <div class="q-pt-md q-pb-md bg-accent text-white text-weight-light">
      <div class="row">
        <div class="col"></div>
        <div class="col-10">
          <span class="text-h4">{{ catalogStore.study?.name }}</span>
          <q-btn
            v-if="authStore.isAuthenticated && authStore.isAdmin"
            flat
            dense
            round
            class="on-right q-mb-sm"
            color="negative"
            icon="delete"
            :title="$t('delete')"
            @click="onShowDelete"
          />
        </div>
        <div class="col"></div>
      </div>
    </div>
    <q-separator />
    <div class="row">
      <div class="col"></div>
      <div class="col-10">
        <study-view />
      </div>
      <div class="col"></div>
    </div>
    <confirm-dialog v-model="showDelete" :text="$t('confirm_study_delete', { identifier: catalogStore.study?.name })" @confirm="onDelete"/>
  </q-page>
</template>

<script setup lang="ts">
import StudyView from 'src/components/study/StudyView.vue';
import ConfirmDialog from 'src/components/ConfirmDialog.vue';

const authStore = useAuthStore();
const catalogStore = useCatalogStore();
const route = useRoute();
const router = useRouter();

const showDelete = ref(false);

watch(
  () => route.params.id,
  () => updateStudy,
);

onMounted(updateStudy);

function updateStudy() {
  catalogStore.loadStudy(route.params.id as string);
}

function onShowDelete() {
  showDelete.value = true;
}

function onDelete() {
  catalogStore.deleteStudy(route.params.id as string).then(() => {
    router.push({ name: 'catalog' });
  });
}
</script>
