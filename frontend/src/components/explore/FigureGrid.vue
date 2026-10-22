<template>
  <div class="figure-grid" :class="`figure-grid--${columns}`">
    <slot />
  </div>
</template>

<script setup lang="ts">
/** A row of figures of the same height, one per column on narrow screens. */
withDefaults(defineProps<{ columns?: 2 | 3 }>(), { columns: 2 });
</script>

<style scoped lang="scss">
.figure-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 24px;
}

@media (min-width: $breakpoint-md-min) {
  .figure-grid {
    gap: 40px;
  }

  .figure-grid--2 {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .figure-grid--3 {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 32px;
  }
}
</style>
