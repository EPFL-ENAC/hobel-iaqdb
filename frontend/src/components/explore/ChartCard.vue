<template>
  <article class="chart-card">
    <header class="chart-card__header">
      <div class="chart-card__top">
        <div class="chart-card__eyebrow">{{ eyebrow }}</div>
        <div v-if="$slots.aside" class="chart-card__aside">
          <slot name="aside" />
        </div>
      </div>
      <h3 class="chart-card__title">{{ title }}</h3>
    </header>
    <div class="chart-card__body">
      <slot />
    </div>
    <div v-if="$slots.footer" class="figure-footer">
      <slot name="footer" />
    </div>
  </article>
</template>

<script setup lang="ts">
/** A figure of an explore chapter: what it counts, the question it answers, the chart, then its footer. */
interface Props {
  /** what is counted, e.g. "Datasets by country" */
  eyebrow: string;
  /** the question the figure answers */
  title: string;
}

defineProps<Props>();
</script>

<style scoped lang="scss">
.chart-card {
  // as tall as its neighbours in the row: the body takes the slack
  display: flex;
  flex-direction: column;
  height: 100%;
  background: white;
  border: 1px solid $grey-4;
  padding: 32px;
  min-width: 0;

  @media (max-width: $breakpoint-xs-max) {
    padding: 20px 16px;
  }
}

.chart-card__header {
  margin-bottom: 40px;
}

// the eyebrow on the left, the aside on the right; on narrow cards the
// aside wraps under the eyebrow, never beside the title
.chart-card__top {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  justify-content: space-between;
  gap: 4px 24px;
  margin-bottom: 12px;
}

.chart-card__body {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.chart-card__eyebrow {
  font-size: 0.8125rem;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  color: $grey-10;
}

.chart-card__title {
  font-size: clamp(1.25rem, 1.1rem + 0.4vw, 1.5rem);
  font-weight: 400;
  line-height: 1.3;
  color: $grey-10;
  margin: 0;
}

.chart-card__aside {
  font-size: 0.875rem;
  white-space: nowrap;
}
</style>
