<template>
  <article class="chart-card" :class="{ 'chart-card--split': $slots.panel }">
    <div class="chart-card__lead">
      <header class="chart-card__header">
        <div class="chart-card__heading">
          <div class="chart-card__eyebrow">{{ eyebrow }}</div>
          <h3 class="chart-card__title">{{ title }}</h3>
        </div>
        <!-- menus that change what the figure shows, e.g. its context -->
        <div v-if="$slots.actions" class="chart-card__actions">
          <slot name="actions" />
        </div>
      </header>
      <template v-if="$slots.panel">
        <div class="chart-card__panel">
          <slot name="panel" />
        </div>
        <div v-if="$slots.footer" class="figure-footer" :class="{ 'figure-footer--blank': footerBlank }">
          <slot name="footer" />
        </div>
      </template>
    </div>
    <div class="chart-card__body">
      <slot />
    </div>
    <div v-if="!$slots.panel && $slots.footer" class="figure-footer" :class="{ 'figure-footer--blank': footerBlank }">
      <slot name="footer" />
    </div>
  </article>
</template>

<script setup lang="ts">
/**
 * A figure of an explore chapter: what it counts, the question it answers,
 * the chart, then its footer. With a `panel`, the heading, the panel and the
 * footer stand left of the chart on wide screens.
 */
interface Props {
  /** what is counted, e.g. "Datasets by country" */
  eyebrow: string;
  /** the question the figure answers */
  title: string;
  /** the footer has nothing to show this time: it keeps its place, without its rule */
  footerBlank?: boolean;
}

withDefaults(defineProps<Props>(), { footerBlank: false });
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

// the heading on the left, the menus on the right; on narrow cards the
// menus wrap under the title
.chart-card__header {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px 32px;
  margin-bottom: 40px;
}

.chart-card__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 16px;
}

.chart-card__lead {
  display: flex;
  flex-direction: column;
}

.chart-card__body {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.chart-card__panel {
  margin-bottom: 32px;
}

@media (min-width: $breakpoint-md-min) {
  .chart-card--split {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(0, 2fr);
    column-gap: 48px;

    .chart-card__panel {
      flex: 1;
    }

    .chart-card__body {
      padding-left: 48px;
      border-left: 1px solid $grey-4;
    }
  }
}

.chart-card__eyebrow {
  font-size: 0.8125rem;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  color: $grey-10;
  margin-bottom: 12px;
}

.chart-card__title {
  font-size: clamp(1.25rem, 1.1rem + 0.4vw, 1.5rem);
  font-weight: 400;
  line-height: 1.3;
  color: $grey-10;
  margin: 0;
}
</style>
