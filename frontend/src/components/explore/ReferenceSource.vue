<template>
  <div v-if="benchmark" class="reference-source">
    <span class="reference-source__label">{{ t('explore_figures.reference_source.label') }}</span>
    <ReferenceMenu
      class="reference-source__pill"
      :parameter="parameter"
      :selected="benchmark"
      @pick="(b) => emit('pick', b)"
    />
    <span class="reference-source__name">
      <span class="reference-source__text">{{ benchmark.source }}</span>
      <q-icon name="info_outline" size="14px" class="reference-source__info" />
      <q-tooltip max-width="320px" anchor="top middle" self="bottom middle" :offset="[0, 6]">
        <div class="reference-source__tip">
          <p class="reference-source__tip-title">{{ benchmark.source }}</p>
          <p>{{ details }}</p>
          <p v-if="comparison">{{ comparison }}</p>
        </div>
      </q-tooltip>
    </span>
    <a
      v-if="benchmark.url"
      :href="benchmark.url"
      target="_blank"
      rel="noopener noreferrer"
      class="reference-source__link"
      >{{ t('explore_figures.reference_source.link') }}<q-icon name="open_in_new" size="12px" class="q-ml-xs"
    /></a>
  </div>
</template>

<script setup lang="ts">
/**
 * The one-line caption under a figure that names its reference: the pill
 * with the value, to pick another one, then the source and a link to it. A
 * tooltip on the source gives institution, year, region, type of limit and
 * averaging period. With `compared`, it also says which means the figure
 * compares with the reference. A pick goes back to the figure.
 */
import ReferenceMenu from '@/components/explore/ReferenceMenu.vue';
import type { ExploreBenchmark } from '@/models';

const props = defineProps<{
  parameter: string | null;
  /** the reference of the figure */
  benchmark: ExploreBenchmark | null;
  /** the figure counts the periods above the reference, at the reference's grain */
  compared?: boolean;
}>();
const emit = defineEmits<{ pick: [benchmark: ExploreBenchmark] }>();
const { t } = useI18n();

const details = computed(() => {
  const b = props.benchmark;
  if (!b) return '';
  const by = b.year === null ? b.institution : `${b.institution}, ${b.year}`;
  return [by, b.region, b.limit_type, b.period].join(' · ') + '.';
});

/** how the figure compares, then how the value was derived, e.g. a unit conversion */
const comparison = computed(() => {
  const b = props.benchmark;
  if (!b) return '';
  const parts = props.compared ? [t(`explore_figures.reference_source.compared.${b.grain}`)] : [];
  if (b.note) parts.push(`${b.note}.`);
  return parts.join(' ');
});
</script>

<style scoped lang="scss">
// one quiet line across the card; a long source name gives way first.
// 24px above and below, as the footer leaves under its rule
.reference-source {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  margin: 24px 0;
  font-size: 0.75rem;
  line-height: 20px;
  color: $grey-7;
}

.reference-source__label,
.reference-source__pill,
.reference-source__link {
  flex: none;
}

.reference-source__name {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  margin-left: 2px;
  color: $grey-9;
  cursor: help;
}

.reference-source__text {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.reference-source__info {
  flex: none;
  color: $grey-6;
}

.reference-source__link {
  margin-left: 8px;
  color: $figure-accent-strong;
  white-space: nowrap;
}

.reference-source__tip {
  font-size: 0.75rem;
  line-height: 1.5;

  p {
    margin: 0;
  }

  p + p {
    margin-top: 4px;
  }
}

.reference-source__tip-title {
  font-weight: 500;
}
</style>
