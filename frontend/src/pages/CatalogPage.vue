<template>
  <q-page>
    <div class="text-h6 q-pa-md">
      {{ $t('studies') }}
    </div>
    <q-separator />
    <study-list />    
  </q-page>
</template>

<script setup lang="ts">
import StudyList from 'src/components/StudyList.vue';

</script>
