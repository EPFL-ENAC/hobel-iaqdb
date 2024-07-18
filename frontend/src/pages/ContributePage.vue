<template>
  <q-page class="q-mb-lg">
    <div class="q-pt-md q-pb-md bg-accent text-white">
      <div class="row">
        <div class="col"></div>
        <div class="col-8">
          <span class="text-h4 text-weight-light">{{ $t('contribute_title') }}</span>
        </div>
        <div class="col"></div>
      </div>
    </div>
    <q-separator />
    <div class="row q-mt-lg">
      <div class="col"></div>
      <div class="col-8">
        <div v-if="showIntro">
          <q-card flat>
            <q-card-section class="q-pa-none">
              <q-markdown no-heading-anchor-links :src="ContributeMd" />
            </q-card-section>
          </q-card>
          <q-btn
            color="primary"
            :label="$t('start')"
            @click="showIntro = false"
            class="q-mt-lg"
          />
        </div>
        <div v-else>
          <study-stepper class="q-mt-md" @pause="showIntro = true"/>
        </div>
      </div>
      <div class="col"></div>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import ContributeMd from 'src/assets/contribute.md';
import StudyStepper from 'src/components/contribute/StudyStepper.vue';

const showIntro = ref(true);
</script>
