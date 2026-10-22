<template>
  <div class="figure-frame" :class="`figure-frame--${fit}`" :style="`min-height: ${height}px;`">
    <slot />
    <div v-if="message" class="figure-frame__message text-caption" :class="error ? 'text-negative' : 'text-grey-7'">
      {{ message }}
    </div>
    <q-inner-loading :showing="loading && !message" color="grey-7" />
  </div>
</template>

<script setup lang="ts">
/**
 * The plot area of a figure: at least a set height, whatever its state, and
 * as tall as the card allows; an empty or failed load is said over it.
 */
interface Props {
  height?: number | undefined;
  loading?: boolean;
  error?: string | null;
  /** said when the load came back empty */
  empty?: string;
  /**
   * `fill` (default): the content is sized to the frame, as a chart needs
   * a box with a definite size; `content`: the frame is as tall as its content
   */
  fit?: 'fill' | 'content';
}

const props = withDefaults(defineProps<Props>(), {
  height: 260,
  loading: false,
  error: null,
  empty: '',
  fit: 'fill',
});
const { t } = useI18n();

const message = computed(() => (props.error ? `${t('plots.error')}: ${props.error}` : props.empty));
</script>

<style scoped lang="scss">
// at least `height`, and the rest of the card when a neighbour makes it taller
.figure-frame {
  position: relative;
  flex: 1 0 auto;
}

// a chart reads its box's size once mounted: it gets the frame's exact box,
// not a percentage of a height the layout has not settled
.figure-frame--fill > :slotted(*) {
  position: absolute;
  inset: 0;
}

.figure-frame__message {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  background: white;
  text-align: center;
}
</style>
