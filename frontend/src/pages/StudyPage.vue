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
            color="grey-8"
            icon="edit"
            :title="t('edit')"
            @click="onShowDraft"
          />
          <q-btn
            v-if="authStore.isAuthenticated && authStore.isAdmin"
            flat
            dense
            round
            class="q-mb-sm"
            color="negative"
            icon="delete"
            :title="t('delete')"
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
    <confirm-dialog v-model="showDelete" :text="t('confirm_study_delete', { identifier: catalogStore.study?.name })" @confirm="onDelete"/>
    <confirm-dialog v-model="showDraft" :text="t('confirm_study_draft', { identifier: catalogStore.study?.name })" @confirm="onDraft"/>
  </q-page>
</template>

<script setup lang="ts">
import StudyView from 'src/components/study/StudyView.vue';
import ConfirmDialog from 'src/components/ConfirmDialog.vue';

const { t } = useI18n();
const authStore = useAuthStore();
const catalogStore = useCatalogStore();
const contributeStore = useContributeStore();
const route = useRoute();
const router = useRouter();

const showDelete = ref(false);
const showDraft = ref(false);

const studyId = computed(() => route.query.id as string);

watch(
  () => route.query.id,
  () => updateStudy,
);

onMounted(updateStudy);

function updateStudy() {
  catalogStore.loadStudy(studyId.value);
}

function onShowDelete() {
  showDelete.value = true;
}

function onDelete() {
  catalogStore.deleteStudy(studyId.value).then(() => {
    router.push({ name: 'data-hub' });
  });
}

function onShowDraft() {
  showDraft.value = true;
}

function onDraft() {
  if (!catalogStore.study) {
    return;
  }
  contributeStore.reinstateDraft(catalogStore.study);
}
</script>
