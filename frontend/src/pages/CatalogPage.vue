<template>
  <q-page>
    <div class="text-h4 q-pa-md bg-accent text-white text-weight-light">
      {{ $t('studies') }}
    </div>
    <q-separator />
    <study-list />    
  </q-page>
</template>

<script setup lang="ts">
import StudyList from 'src/components/StudyList.vue';

</script>
