<template>
  <q-dialog v-model="open">
    <q-card class="figure-dialog" :style="`width: ${width}px;`">
      <q-card-section class="row items-start no-wrap q-pb-sm">
        <div class="col">
          <div v-if="eyebrow" class="figure-dialog__eyebrow">{{ eyebrow }}</div>
          <div class="figure-dialog__title">{{ title }}</div>
        </div>
        <q-btn v-close-popup class="q-ml-md" flat round dense icon="close" :aria-label="t('ranked_bars.close')" />
      </q-card-section>
      <q-card-section class="figure-dialog__scroll" :class="{ 'figure-dialog--loading': loading }">
        <slot />
      </q-card-section>
      <q-card-section v-if="$slots.footer" class="figure-dialog__footer">
        <slot name="footer" />
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
/** A figure in full, e.g. every row of a list cut short in its card, under the card's heading. */
interface Props {
  eyebrow?: string | undefined;
  title?: string | undefined;
  /** dims the content while a new set loads */
  loading?: boolean | undefined;
  width?: number | undefined;
}

withDefaults(defineProps<Props>(), { eyebrow: '', title: '', loading: false, width: 760 });
const open = defineModel<boolean>({ default: false });
const { t } = useI18n();
</script>

<style scoped lang="scss">
.figure-dialog {
  max-width: 92vw;
  border-radius: 0;
}

.figure-dialog__eyebrow {
  font-size: 0.8125rem;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  color: $grey-10;
  margin-bottom: 8px;
}

.figure-dialog__title {
  font-size: 1.375rem;
  line-height: 1.3;
  color: $grey-10;
}

.figure-dialog__scroll {
  max-height: 65vh;
  overflow-y: auto;
  padding-top: 0;
  transition: opacity 0.2s;
}

.figure-dialog--loading {
  opacity: 0.5;
}

.figure-dialog__footer {
  border-top: 1px solid $grey-4;
  font-size: 0.875rem;
  color: $grey-9;
}
</style>
