<template>
  <div>
    <!-- <q-btn label="Reset" push color="white" text-color="primary" @click="step = 1" class="q-mb-md" /> -->

    <q-btn @click="onPause" color="secondary" label="Pause" class="q-mb-lg" />

    <q-stepper
      v-model="step"
      header-nav
      ref="stepper"
      color="primary"
      animated
    >
      <q-step
        :name="1"
        title="Study information"
        icon="settings"
        :done="step > 1"
        :header-nav="step > 1"
      >
        <q-markdown no-heading-anchor-links :src="StepStudyMd" />
        <study-form class="q-mt-lg"/>

        <q-stepper-navigation>
          <q-btn @click="() => { done1 = true; step = 2 }" color="primary" label="Continue" />
        </q-stepper-navigation>
      </q-step>

      <q-step
        :name="2"
        title="Buildings and rooms information"
        icon="domain"
        :done="step > 2"
        :header-nav="step > 2"
      >
        <q-markdown no-heading-anchor-links :src="StepBuildingsMd" />
        <buildings-form class="q-mt-lg"/>

        <q-stepper-navigation>
          <q-btn @click="() => { done2 = true; step = 3 }" color="primary" label="Continue" />
          <q-btn flat @click="step = 1" color="primary" label="Back" class="on-right" />
        </q-stepper-navigation>
      </q-step>

      <q-step
        :name="3"
        title="Upload datasets"
        icon="upload"
        :header-nav="step > 3"
      >
        <q-markdown no-heading-anchor-links :src="StepDatasetsMd" />
        <datasets-form class="q-mt-lg"/>
        <q-stepper-navigation>
          <q-btn color="primary" @click="done3 = true" label="Finish" />
          <q-btn flat @click="step = 2" color="primary" label="Back" class="on-right" />
        </q-stepper-navigation>
      </q-step>
    </q-stepper>
  </div>
</template>


<script lang="ts">
export default defineComponent({
  components: { BuildingsForm, DatasetsForm },
  name: 'StudyStepper',
});
</script>
<script setup lang="ts">
import StepStudyMd from 'src/assets/step-study.md';
import StepBuildingsMd from 'src/assets/step-buildings.md';
import StepDatasetsMd from 'src/assets/step-datasets.md';
import StudyForm from 'src/components/contribute/StudyForm.vue';
import BuildingsForm from 'src/components/contribute/BuildingsForm.vue'; 
import DatasetsForm from './DatasetsForm.vue';

const emit = defineEmits(['pause']);

const step = ref(1);

function onPause() {
  emit('pause');
}
</script>
