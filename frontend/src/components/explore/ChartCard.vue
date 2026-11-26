<template>
  <article class="chart-card" :class="{ 'chart-card--split': $slots.panel }">
    <!-- a card without dropdowns: its first line, across the whole card, ends with the download -->
    <div v-if="!underMenus()" class="chart-card__top">
      <div class="chart-card__eyebrow">{{ eyebrow }}</div>
      <ImageMenu :eyebrow="eyebrow" :title="title" :note="note" :parts="parts" :image="image" />
    </div>
    <div class="chart-card__lead">
      <header class="chart-card__header">
        <div class="chart-card__heading">
          <!-- a card with dropdowns: the eyebrow heads the title, the dropdowns start level with it -->
          <div v-if="underMenus()" class="chart-card__eyebrow">{{ eyebrow }}</div>
          <h3 class="chart-card__title">{{ title }}</h3>
          <p v-if="note" class="chart-card__note">{{ note }}</p>
        </div>
        <!-- menus that change what the figure shows, e.g. its context, and the download under the dropdowns -->
        <div v-if="$slots.actions" class="chart-card__side">
          <div class="chart-card__actions">
            <slot name="actions" />
          </div>
          <ImageMenu v-if="underMenus()" :eyebrow="eyebrow" :title="title" :note="note" :parts="parts" :image="image" />
        </div>
      </header>
      <!-- what the figure plots, said as a sentence of menus under the title -->
      <div v-if="$slots.controls" class="chart-card__controls">
        <slot name="controls" />
      </div>
      <template v-if="$slots.panel">
        <div class="chart-card__panel">
          <slot name="panel" />
        </div>
        <div v-if="$slots.footer || timeNote" class="figure-footer" :class="{ 'figure-footer--blank': footerBlank }">
          <div class="chart-card__footer">
            <slot name="footer" />
          </div>
          <TimeNoteLink v-if="timeNote" />
        </div>
      </template>
    </div>
    <div class="chart-card__body">
      <slot />
    </div>
    <!-- the card's own links and hints, then the link to the note on time steps -->
    <div
      v-if="!$slots.panel && ($slots.footer || timeNote)"
      class="figure-footer"
      :class="{ 'figure-footer--blank': footerBlank }"
    >
      <div class="chart-card__footer">
        <slot name="footer" />
      </div>
      <TimeNoteLink v-if="timeNote" />
    </div>
  </article>
</template>

<script setup lang="ts">
/**
 * A figure of an explore chapter: what it counts, the question it answers,
 * the chart, then its footer. With a `panel`, the heading, the panel and the
 * footer stand left of the chart on wide screens. Its menu downloads the
 * figure as an image, drawn by the parts it holds and by `image`.
 */
import ImageMenu from '@/components/explore/ImageMenu.vue';
import TimeNoteLink from '@/components/explore/TimeNoteLink.vue';
import { IMAGE_PARTS, type Draw, type FigureImage } from '@/components/explore/figureImage';

interface Props {
  /** what is counted, e.g. "Datasets by country" */
  eyebrow: string;
  /** the question the figure answers */
  title: string;
  /** how to read the figure: what one point, bar or row is */
  note?: string;
  /** the footer has nothing to show this time: it keeps its place, without its rule */
  footerBlank?: boolean;
  /** what the figure adds to its image, e.g. its ECharts chart or its legend */
  image?: FigureImage;
  /** the menus at the right of the title hold dropdowns: the download goes under them */
  dropdowns?: boolean;
  /** the figure shows readings: its footer links to the note on how their time steps are combined */
  timeNote?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  note: '',
  footerBlank: false,
  image: () => ({}),
  dropdowns: true,
  timeNote: false,
});
const slots = useSlots();

/** the download under the dropdowns, else at the end of the eyebrow's line */
function underMenus(): boolean {
  return !!slots.actions && props.dropdowns;
}

/** the drawings of the parts the card holds, in the order they set up */
const parts: Draw[] = [];
provide(IMAGE_PARTS, {
  add(draw) {
    parts.push(draw);
    return () => parts.splice(parts.indexOf(draw), 1);
  },
});
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

.chart-card__controls {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 12px;
  margin: -16px 0 32px;
  font-size: 0.9375rem;
  color: $grey-7;
}

.chart-card__side {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 16px;

  @media (max-width: $breakpoint-xs-max) {
    width: 100%;
  }
}

.chart-card__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 16px;

  // under the title on a phone: the menus take the card's width
  @media (max-width: $breakpoint-xs-max) {
    width: 100%;
  }
}

.chart-card__lead {
  display: flex;
  flex-direction: column;

  // one column: the footer of a split card goes under the chart, not above it
  @media (max-width: $breakpoint-sm-max) {
    display: contents;

    .figure-footer {
      order: 1;
    }
  }
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

    .chart-card__top {
      grid-column: 1 / -1;
    }

    .chart-card__panel {
      flex: 1;
    }

    .chart-card__body {
      padding-left: 48px;
      border-left: 1px solid $grey-4;
    }
  }
}

.chart-card__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 12px;

  // the line stays as tall as the eyebrow
  .image-menu {
    margin-top: -6px;
    margin-bottom: -6px;
  }
}

.chart-card__eyebrow {
  min-width: 0;
  font-size: 0.8125rem;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  color: $grey-10;
}

.chart-card__heading .chart-card__eyebrow {
  margin-bottom: 12px;
}

.chart-card__title {
  font-size: clamp(1.25rem, 1.1rem + 0.4vw, 1.5rem);
  font-weight: 400;
  line-height: 1.3;
  color: $grey-10;
  margin: 0;
}

// under the title, as a chart's subtitle: a screenshot that keeps the title keeps it
.chart-card__note {
  max-width: 60ch;
  margin: 8px 0 0;
  font-size: 0.875rem;
  line-height: 1.45;
  color: $grey-8;
}

// the card's own footer items: one of them can push itself right with an auto margin
.chart-card__footer {
  display: flex;
  flex: 1;
  align-items: center;
  gap: 24px;
  min-width: 0;
}
</style>
