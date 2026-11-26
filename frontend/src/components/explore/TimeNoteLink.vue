<template>
  <button type="button" class="figure-link time-note-link" @click="helpStore.toggleHelp(TIME_NOTE)">
    <q-icon :name="outlinedHelpOutline" size="16px" aria-hidden="true" />
    <span>{{ t('explore_figures.time_note.link') }}</span>
    <q-tooltip>{{ t('explore_figures.time_note.tooltip') }}</q-tooltip>
  </button>
</template>

<script setup lang="ts">
/**
 * The link in a chart's footer to the note on how readings taken at
 * different time steps (every minute, every hour, over several days) are
 * combined, opened in the help drawer.
 */
import { outlinedHelpOutline } from '@quasar/extras/material-icons-outlined';

const { t } = useI18n();
const helpStore = useHelpStore();

/** public/time-resolution.md */
const TIME_NOTE = 'time-resolution';
</script>

<style scoped lang="scss">
// a question mark and a few words: the tooltip says the rest
.time-note-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
</style>
