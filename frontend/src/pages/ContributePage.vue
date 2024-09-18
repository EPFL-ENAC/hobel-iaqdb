<template>
  <q-page class="q-mb-lg">
    <div class="q-pt-md q-pb-md bg-accent text-white">
      <div class="row">
        <div class="col"></div>
        <div class="col-8">
          <span class="text-h4 text-weight-light">{{
            $t('contribute_title')
          }}</span>
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
            @click="onStart"
            class="q-mt-lg"
          />
          <q-btn
            color="secondary"
            :flat="!contrib.inProgress"
            :label="$t('resume')"
            :disable="!contrib.inProgress"
            @click="onResume"
            class="q-mt-lg on-right"
          />
        </div>
        <div v-else>
          <study-stepper
            class="q-mt-md"
            @pause="showIntro = true"
            @finish="onFinish"
          />
        </div>
      </div>
      <div class="col"></div>
    </div>
    <study-upload-dialog v-model="showUpload" @close="onUploaded" />
  </q-page>
</template>

<script setup lang="ts">
import ContributeMd from 'src/assets/contribute.md';
import StudyStepper from 'src/components/contribute/StudyStepper.vue';
import StudyUploadDialog from 'src/components/contribute/StudyUploadDialog.vue';

const contrib = useContributeStore();

const showIntro = ref(true);
const showUpload = ref(false);

function onStart() {
  contrib.reset();
  showIntro.value = false;
}

function onResume() {
  showIntro.value = false;
}

function onFinish() {
  // TODO contribute store to upload stuff
  showUpload.value = true;
}

function onUploaded() {
  showIntro.value = true;
}
</script>
