<template>
  <div class="figure-frame" :class="`figure-frame--${fit}`" :style="`min-height: ${height}px;`">
    <slot />
    <div v-if="message" class="figure-frame__message text-caption" :class="error ? 'text-negative' : 'text-grey-7'">
      {{ message }}
    </div>
    <q-inner-loading :showing="loading && !message">
      <div v-if="slowShown" class="figure-frame__slow">
        <q-spinner size="24px" color="grey-7" />
        <span class="text-body2 text-grey-9">{{ slow }}</span>
      </div>
      <q-spinner v-else size="42px" color="grey-7" />
    </q-inner-loading>
  </div>
</template>

<script setup lang="ts">
/**
 * The plot area of a figure: at least a set height, whatever its state, and
 * as tall as the card allows; an empty or failed load is said over it, and
 * a load that runs long says so in a panel over it.
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
  /** said with the spinner once a load runs past `SLOW_AFTER` */
  slow?: string;
}

const props = withDefaults(defineProps<Props>(), {
  height: 260,
  loading: false,
  error: null,
  empty: '',
  fit: 'fill',
  slow: '',
});
const { t } = useI18n();

/** ms before a load is said to take a while: a quick one never flashes it */
const SLOW_AFTER = 1000;
const slowShown = ref(false);
let slowTimer: ReturnType<typeof setTimeout> | undefined;

watch(
  () => props.loading,
  (loading) => {
    clearTimeout(slowTimer);
    slowShown.value = false;
    if (loading && props.slow) slowTimer = setTimeout(() => (slowShown.value = true), SLOW_AFTER);
  },
  { immediate: true },
);
onBeforeUnmount(() => clearTimeout(slowTimer));

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

// a panel of its own: said over the figure, it must not read through it
.figure-frame__slow {
  display: flex;
  align-items: center;
  gap: 12px;
  max-width: 320px;
  padding: 12px 16px;
  border: 1px solid $grey-4;
  border-radius: 2px;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
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
