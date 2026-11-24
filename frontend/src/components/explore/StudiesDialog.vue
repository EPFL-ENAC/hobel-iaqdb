<template>
  <!-- with a default slot, the slot is a link that opens the dialog -->
  <button v-if="$slots.default" type="button" class="figure-link studies-dialog__link" @click="open = true">
    <slot />
    <q-tooltip>{{ t('explore_figures.studies.list') }}</q-tooltip>
  </button>
  <FigureDialog v-model="open" :eyebrow="t('explore_figures.studies.eyebrow')" :title="title">
    <p v-for="line in lead" :key="line" class="studies-dialog__lead">{{ line }}</p>
    <table class="studies-dialog__table">
      <thead>
        <tr>
          <th>{{ t('explore_figures.studies.study') }}</th>
          <th class="studies-dialog__number studies-dialog__r">
            {{ t('explore_figures.studies.r', { method: methodName }) }}
          </th>
          <th class="studies-dialog__number">{{ t('explore_figures.studies.spaces') }}</th>
          <th v-if="pointsLabel" class="studies-dialog__number">{{ pointsLabel }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="study in studies" :key="study.study">
          <td class="studies-dialog__name">
            <router-link :to="{ path: '/study', query: { id: study.study } }" :title="keyLabel('study', study.study)">{{
              keyLabel('study', study.study)
            }}</router-link>
          </td>
          <td class="studies-dialog__number studies-dialog__r">{{ rOf(study) }}</td>
          <td class="studies-dialog__number">{{ study.n_spaces.toLocaleString(locale) }}</td>
          <td v-if="pointsLabel" class="studies-dialog__number">{{ study.n.toLocaleString(locale) }}</td>
        </tr>
      </tbody>
    </table>
    <template v-if="$slots.footer" #footer><slot name="footer" /></template>
  </FigureDialog>
</template>

<script setup lang="ts">
/**
 * The studies behind a pooled r (#229): per study, its own r, its spaces and
 * its points, and a link to its page. A pooled r far from the r of its
 * studies comes from the differences between them.
 */
import FigureDialog from '@/components/explore/FigureDialog.vue';
import { keyLabel } from '@/components/plots/charts';
import { useChartFormat } from '@/composables/useChartFormat';
import type { ExploreStudyFit, ExploreWithin } from '@/models';

interface Props {
  /** the pair, e.g. "PM10 × CO₂" */
  title: string;
  method: 'pearson' | 'spearman';
  /** the r of all studies together; null below the minimum sample size */
  r: number | null | undefined;
  within: ExploreWithin | undefined;
  /** header of the column of the points of each study; no column without it */
  pointsLabel?: string | undefined;
}

const props = defineProps<Props>();
const open = defineModel<boolean>({ default: false });
const { t, locale } = useI18n();
const { describeWithin } = useChartFormat();

const studies = computed(() => props.within?.studies ?? []);
const methodName = computed(() => t(`plots.${props.method}`));

/** the r of all studies together, then the r within each study */
const lead = computed(() => {
  const pooled =
    props.r === null || props.r === undefined
      ? t('plots.too_little_data')
      : t('explore_figures.studies.pooled', { method: methodName.value, r: props.r.toFixed(2) });
  return [pooled, describeWithin(props.within)].filter(Boolean);
});

function rOf(study: ExploreStudyFit): string {
  if (study.r !== undefined) return study.r.toFixed(2);
  return study.enough ? t('explore_figures.studies.no_r') : t('explore_figures.studies.too_little');
}
</script>

<style scoped lang="scss">
.studies-dialog__lead {
  margin: 0 0 4px;
  font-size: 0.9375rem;
  color: $grey-9;
}

.studies-dialog__table {
  width: 100%;
  margin-top: 12px;
  border-collapse: collapse;
  table-layout: fixed;
  font-size: 0.875rem;
  font-variant-numeric: tabular-nums;

  th {
    padding: 4px 8px;
    border-bottom: 1px solid $grey-4;
    font-weight: normal;
    text-align: left;
    color: $grey-8;
  }

  td {
    padding: 6px 8px;
    border-bottom: 1px solid $grey-3;
  }
}

.studies-dialog__name {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;

  a {
    color: $figure-accent-strong;
  }
}

/* green like the other figure links, without an underline */
.studies-dialog__link,
.studies-dialog__name a {
  text-decoration: none;
}


.studies-dialog__number {
  width: 96px;
  text-align: right !important;
  white-space: nowrap;
}

.studies-dialog__r {
  width: 160px;
  white-space: normal;
}
</style>
