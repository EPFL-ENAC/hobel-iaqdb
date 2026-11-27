<template>
  <span
    v-if="entry"
    class="glossary-tip"
    role="button"
    tabindex="0"
    :aria-label="`${entry.term}: ${entry.definition}`"
    @click.stop.prevent
  >
    <q-icon name="info_outline" size="14px" class="glossary-tip__icon" />
    <q-tooltip
      max-width="300px"
      anchor="top middle"
      self="bottom middle"
      :offset="[0, 6]"
    >
      <div class="glossary-tip__body">
        <div class="glossary-tip__title">{{ entry.term }}</div>
        <div class="glossary-tip__text">{{ entry.definition }}</div>
      </div>
    </q-tooltip>
  </span>
</template>

<script setup lang="ts">
import { lookupGlossary } from '@/utils/glossary';

const props = defineProps<{
  term: string | null | undefined;
  fallback?: string | null | undefined;
}>();

const entry = computed(() => lookupGlossary(props.term, props.fallback));
</script>

<style scoped lang="scss">
.glossary-tip {
  display: inline-flex;
  align-items: center;
  flex: none;
  color: currentColor;
  opacity: 0.55;
  cursor: help;
  transition: opacity 0.15s;

  &:hover,
  &:focus-visible {
    opacity: 1;
  }
}

.glossary-tip__body {
  font-size: 0.75rem;
  line-height: 1.45;
}

.glossary-tip__title {
  font-weight: 500;
}

.glossary-tip__text {
  margin-top: 4px;
}
</style>
