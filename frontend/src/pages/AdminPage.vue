<template>
  <q-page>
    <div class="text-h4 q-pa-md bg-accent text-white text-weight-light">
      {{ t('administration') }}
    </div>
    <q-toolbar v-if="authStore.isAuthenticated" class="bg-warning">
      <span>{{ t(authStore.isAdmin ? 'user.welcome_admin' : 'user.welcome', { name: authStore.profile?.firstName }) }}</span>
      <q-btn
        color="primary"
        no-caps
        :label="t('user.logout')"
        @click="authStore.logout" 
        size="sm"
        class="on-right"
      />
    </q-toolbar>
    <div class="q-pa-md">
      <div v-if="!authStore.isAuthenticated">
        <q-spinner-dots size="md" color="primary" />
      </div>
      <div v-else-if="authStore.isAdmin">
        <q-tabs
          dense
          no-caps
          align="left"
          active-color="secondary"
          indicator-color="secondary"
          class="text-grey q-mb-md"
        >
          <q-route-tab to="/admin" exact :label="t('admin.contributions')" />
          <q-route-tab to="/admin/downloads" exact :label="t('admin.downloads')" />
        </q-tabs>
        <template v-if="route.path === '/admin/downloads'">
          <div class="text-help q-mb-md">
            {{ t('admin.downloads_info') }}
          </div>
          <download-requests-table />
        </template>
        <template v-else>
          <div class="text-help q-mb-md">
            {{ t('admin.contributions_info') }}
          </div>
          <study-drafts-table />
        </template>
      </div>
      <div v-else>
        <q-card class="bg-negative text-white">
          <q-card-section>
            {{ t('user.not_admin') }}
          </q-card-section>
        </q-card>
      </div>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import StudyDraftsTable from '@/components/admin/StudyDraftsTable.vue';
import DownloadRequestsTable from '@/components/admin/DownloadRequestsTable.vue';

const { t } = useI18n();
const authStore = useAuthStore();
const route = useRoute();

onMounted(() => {
   void authStore.init().then(() => {
     if (!authStore.isAuthenticated) {
       return authStore.login();
     }
   });
})

</script>
