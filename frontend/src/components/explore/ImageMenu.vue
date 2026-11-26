<template>
  <q-btn
    outline
    size="sm"
    padding="xs sm"
    :icon="outlinedFileDownload"
    color="grey-8"
    class="image-menu"
    :aria-label="t('figure_image.download')"
  >
    <q-tooltip>{{ t('figure_image.download') }}</q-tooltip>
    <q-menu auto-close anchor="bottom right" self="top right">
      <q-list dense class="image-menu__list">
        <q-item v-for="format in FORMATS" :key="format" clickable @click="download(format)">
          <q-item-section>{{ t(`figure_image.${format}`) }}</q-item-section>
        </q-item>
      </q-list>
    </q-menu>
  </q-btn>
</template>

<script setup lang="ts">
/**
 * The download menu of a figure: the card's heading, its chart drawn again
 * as SVG and a footer saying what the figure shows and where it comes from,
 * as an SVG file or a PNG file.
 */
import { useQuasar } from 'quasar';
import { outlinedFileDownload } from '@quasar/extras/material-icons-outlined';
import {
  CONTENT_WIDTH,
  composeImage,
  fileName,
  save,
  toPng,
  type Draw,
  type FigureImage,
} from '@/components/explore/figureImage';
import { FILTER_SECTIONS, appliedDraft } from '@/composables/useFilterDraft';
import { useFilterSummary } from '@/composables/useFilterSummary';
import { useChartFormat } from '@/composables/useChartFormat';

const props = defineProps<{
  eyebrow: string;
  title: string;
  note: string;
  /** the drawings of the parts the card holds, in their order */
  parts: Draw[];
  image: FigureImage;
}>();
const { t, locale } = useI18n();
const $q = useQuasar();
const exploreStore = useExploreStore();
const { values } = useFilterSummary();
const { describeReference } = useChartFormat();

const FORMATS = ['png', 'svg'] as const;

/** what the figure shows and where it comes from, a line each */
function footer(date: Date): string[] {
  const draft = appliedDraft();
  const filters = FILTER_SECTIONS.flatMap((section) => values(draft, section));
  const units = (props.image.pollutants ?? []).flatMap((slug) => {
    const unit = exploreStore.schema?.parameters.find((p) => p.slug === slug)?.unit;
    if (!unit) return [];
    const pollutant = exploreStore.parameterLabel(slug);
    // some labels already end with their unit, e.g. "Biocontaminants (sequence reads)"
    return [pollutant.endsWith(`(${unit})`) ? pollutant : t('figure_image.unit', { pollutant, unit })];
  });
  const reference = props.image.reference;
  return [
    filters.length ? t('figure_image.filters', { filters: filters.join(' · ') }) : t('figure_image.no_filters'),
    ...(units.length ? [t('figure_image.units', { units: units.join(' · ') })] : []),
    ...(reference
      ? [
          t('figure_image.reference', {
            value: describeReference(reference),
            source: reference.year === null ? reference.source : `${reference.source}, ${reference.year}`,
          }),
        ]
      : []),
    ...(props.image.notes ?? []).filter(Boolean),
    t('figure_image.source', {
      version: import.meta.env.APP_VERSION,
      catalog: exploreStore.schema?.version ?? '',
      url: `${window.location.origin}${window.location.pathname}`,
      date: new Intl.DateTimeFormat(locale.value, { dateStyle: 'long' }).format(date),
    }),
    t('figure_image.cite', { site: window.location.origin }),
  ];
}

async function download(format: (typeof FORMATS)[number]): Promise<void> {
  const date = new Date();
  try {
    const draws = props.image.draw ? [...props.parts, props.image.draw] : props.parts;
    const page = composeImage({
      eyebrow: props.eyebrow,
      title: props.title,
      note: props.note,
      drawings: draws.map((draw) => draw(CONTENT_WIDTH)),
      legend: props.image.legend ?? [],
      footer: footer(date),
    });
    const blob =
      format === 'svg'
        ? new Blob([page.svg], { type: 'image/svg+xml' })
        : await toPng(page.svg, page.width, page.height);
    save(blob, fileName(props.eyebrow, format, date));
  } catch (error) {
    $q.notify({ type: 'negative', message: t('figure_image.failed') });
    throw error;
  }
}
</script>

<style scoped lang="scss">
// at the right end of the eyebrow's line, or under the card's dropdowns; its
// corners as round as theirs
.image-menu {
  flex: none;
  margin-left: auto;
  border-radius: 4px;
}

// the grey of the dropdowns' outline
.image-menu::before {
  border-color: rgba(0, 0, 0, 0.24);
}

.image-menu__list {
  min-width: 140px;
}
</style>
