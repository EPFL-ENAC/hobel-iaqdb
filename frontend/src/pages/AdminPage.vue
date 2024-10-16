<template>
  <q-page>
    <div class="text-h4 q-pa-md bg-accent text-white text-weight-light">
      {{ $t('administration') }}
    </div>
    <q-separator />
    <div class="q-pa-md">
      <div v-if="!authStore.isAuthenticated">
        <q-spinner-dots size="md" color="primary" />
      </div>
      <div v-else-if="authStore.isAdmin">
        <div class="text-h6">
          {{ $t('admin.contributions') }}
        </div>
        <div class="text-help q-mb-md">
          {{ $t('admin.contributions_info') }}
        </div>
        <div>
          TODO
        </div>
      </div>
      <div v-else>
        <q-card class="bg-negative text-white">
          <q-card-section>
            {{ $t('user.not_admin') }}
          </q-card-section>
        </q-card>
      </div>
    </div>
  </q-page>
</template>

<script setup lang="ts">
const authStore = useAuthStore();

onMounted(() => {
   authStore.init().then(() => {
     if (!authStore.isAuthenticated) {
       authStore.login();
     }
   });
})

</script>
