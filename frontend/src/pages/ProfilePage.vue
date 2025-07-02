<template>
  <q-page>
    <div class="text-h4 q-pa-md bg-accent text-white text-weight-light">
      {{ t('profile') }}
      <span v-if="authStore.isAuthenticated"> - {{ authStore.profile?.email }}</span>
    </div>
    <q-separator />
    <div class="q-pa-md">
      <div v-if="authStore.isAuthenticated">
        <div class="q-mb-md">
          <span>{{ t(authStore.isAdmin ? 'user.welcome_admin' : 'user.welcome', { name: authStore.profile?.firstName }) }}</span>
        </div>
        <q-btn
          color="primary"
          no-caps
          :label="t('user.logout')"
          @click="authStore.logout" />
      </div>
      <div v-else>
        <q-spinner-dots size="md" color="primary" />
      </div>
    </div>
  </q-page>
</template>

<script setup lang="ts">
const { t } = useI18n();
const authStore = useAuthStore();

onMounted(() => {
   void authStore.init().then(() => {
     if (!authStore.isAuthenticated) {
       void authStore.login();
     }
   });
})

</script>
