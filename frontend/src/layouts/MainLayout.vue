<template>
  <q-layout view="hHh lpR fFf" @scroll="onScroll">
    <q-header bordered class="bg-white text-grey-10" :class="{ 'main-layout__header--float': floatBar }">
      <div class="main-layout__top">
        <app-toolbar
          :no-menu="!hasFilterDrawer"
          @toggle-left="toggleLeftDrawer"
          @toggle-right="toggleRightDrawer"
        />
      </div>
      <!-- on a phone or tablet the bar floats under the toolbar: it slides away while scrolling down -->
      <div
        class="main-layout__bar"
        :class="{ 'main-layout__bar--hidden': floatBar && barHidden }"
        :inert="(floatBar && barHidden) || undefined"
      >
        <q-resize-observer @resize="(size) => (barHeight = size.height)" />
        <router-view name="bar" />
      </div>
    </q-header>

    <q-drawer
      v-if="hasFilterDrawer"
      v-model="leftDrawerOpen"
      :mini="!leftDrawerOpen || miniStateLeft"
      show-if-above
      bordered
    >
      <div v-if="!miniStateLeft">
        <layers-drawer />
      </div>
      <div
        v-if="!$q.screen.lt.md"
        class="absolute"
        style="top: 10px; right: 10px"
      >
        <q-btn
          dense
          round
          unelevated
          :icon="miniStateLeft ? 'chevron_right' : 'chevron_left'"
          @click="miniStateLeft = !miniStateLeft"
        />
      </div>
    </q-drawer>

    <q-drawer
      v-if="route.path === '/data-hub'"
      v-model="rightDrawerOpen"
      :mini="!rightDrawerOpen || miniStateRight"
      :width="$q.screen.lt.md ? 300 : (showPlots ? 300 : 500)"
      side="right"
      show-if-above
      bordered
    >
      <div v-show="!miniStateRight" class="q-mt-xl">
        <div v-show="helpStore.show">
          <help-drawer />
          <div class="absolute" style="top: 10px; right: 20px">
            <q-btn dense round unelevated icon="close" @click="toggleShowHelp" />
          </div>
        </div>
        <div v-show="catalogStore.showStudyDetails">
          <study-details-drawer />
          <div class="absolute" style="top: 10px; right: 20px">
            <q-btn dense round unelevated icon="close" @click="toggleShowStudyDetails" />
          </div>
        </div>
        <div v-show="showPlots">
          <plots-drawer />
        </div>
      </div>
      <div
        v-if="!$q.screen.lt.md"
        class="absolute"
        style="top: 10px; left: 10px"
      >
        <q-btn
          dense
          round
          unelevated
          :icon="miniStateRight ? 'chevron_left' : 'chevron_right'"
          @click="miniStateRight = !miniStateRight"
        />
      </div>
    </q-drawer>

    <q-page-container>
      <!-- the room the floating bar takes at the top of the page -->
      <div v-if="floatBar" :style="{ height: `${barHeight}px` }" aria-hidden="true" />
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { useQuasar } from 'quasar';
import AppToolbar from '@/components/AppToolbar.vue';
import LayersDrawer from '@/components/LayersDrawer.vue';
import PlotsDrawer from '@/components/PlotsDrawer.vue';
import HelpDrawer from '@/components/HelpDrawer.vue';
import StudyDetailsDrawer from '@/components/StudyDetailsDrawer.vue';

const $q = useQuasar();
const helpStore = useHelpStore();
const catalogStore = useCatalogStore();
const route = useRoute();

const leftDrawerOpen = ref(false);
const rightDrawerOpen = ref(false);
const miniStateLeft = ref(false);
const miniStateRight = ref(false);

/** the filters side bar; explore filters from the bar in the header */
const hasFilterDrawer = computed(() => route.path !== '/explore');

/**
 * On a phone or tablet the toolbar stays and the filter bar floats under it,
 * out of the header's height: scrolling down slides the bar away, scrolling
 * up brings it back.
 */
const floatBar = computed(() => $q.screen.lt.md && route.matched.some((r) => r.components?.bar));
const barHeight = ref(0);
const barHidden = ref(false);

/** how far to scroll one way before the bar follows */
const SCROLL_SLACK = 24;
let lastTop = 0;
let direction = 0;
let turnedAt = 0;

function onScroll({ position }: { position: number }): void {
  const top = position;
  const moved = Math.sign(top - lastTop);
  if (moved && moved !== direction) {
    direction = moved;
    turnedAt = lastTop;
  }
  lastTop = top;
  if (top <= barHeight.value) barHidden.value = false;
  else if (direction > 0 && top - turnedAt > SCROLL_SLACK) barHidden.value = true;
  else if (direction < 0 && turnedAt - top > SCROLL_SLACK) barHidden.value = false;
}

watch(() => route.path, () => (barHidden.value = false));

const showPlots = computed(() => {
  return !helpStore.show && !catalogStore.showStudyDetails;
});

watch(
  () => helpStore.show,
  (newValue) => {
    if (newValue) {
      rightDrawerOpen.value = true;
      miniStateRight.value = false;
    }
  },
);

watch(
  () => catalogStore.showStudyDetails,
  (newValue) => {
    if (newValue) {
      rightDrawerOpen.value = true;
      miniStateRight.value = false;
    }
  },
);

function toggleLeftDrawer() {
  leftDrawerOpen.value = !leftDrawerOpen.value;
}

function toggleRightDrawer() {
  rightDrawerOpen.value = !rightDrawerOpen.value;
}

function toggleShowHelp() {
  helpStore.show = !helpStore.show;
}

function toggleShowStudyDetails() {
  catalogStore.showStudyDetails = !catalogStore.showStudyDetails;
}
</script>

<style scoped lang="scss">
.main-layout__header--float {
  // the toolbar covers the bar as it slides up behind it
  .main-layout__top {
    position: relative;
    z-index: 1;
    background: white;
  }

  .main-layout__bar {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    border-bottom: 1px solid $grey-4;
    background: white;
    transition: transform 0.2s ease;
  }

  .main-layout__bar--hidden {
    transform: translateY(-100%);
  }
}
</style>
