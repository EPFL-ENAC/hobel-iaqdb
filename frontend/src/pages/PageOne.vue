<template>
  <q-page class="q-pa-md">
    <div class="text-h6 q-mb-md">Page 1</div>
    <q-card flat style="max-width: 300px">
      <q-item>
        <q-item-section avatar>
          <q-skeleton type="QAvatar" />
        </q-item-section>
        <q-item-section>
          <q-item-label>
            <q-skeleton type="text" />
          </q-item-label>
          <q-item-label caption>
            <q-skeleton type="text" />
          </q-item-label>
        </q-item-section>
      </q-item>
      <q-skeleton height="200px" square />
    </q-card>
  </q-page>
</template>

<script setup lang="ts">
</script>
