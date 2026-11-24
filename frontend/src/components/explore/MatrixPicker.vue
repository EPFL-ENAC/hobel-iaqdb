<template>
  <q-btn
    outline
    no-caps
    color="grey-8"
    icon="tune"
    :label="t('explore_figures.correlation.pollutants', { count: modelValue.length })"
    :loading="loading"
    class="matrix-picker__open"
    @click="onOpen"
  />
  <FigureDialog v-model="open" :eyebrow="eyebrow" :title="t('explore_figures.matrix_picker.title')" :width="560">
    <div class="matrix-picker">
      <p class="matrix-picker__lead">{{ t('explore_figures.matrix_picker.lead', { max }) }}</p>
      <p v-if="lockedShown.length" class="matrix-picker__lead">
        {{ t('explore_figures.matrix_picker.locked', { pollutants: lockedShown.join(', ') }) }}
      </p>
      <FacetList
        :model-value="draft"
        :options="rows"
        :limit="12"
        :format="formatCompact"
        searchable
        :search-placeholder="t('explore_figures.matrix_picker.search')"
        @update:model-value="onPick"
      />
    </div>
    <template #footer>
      <div class="matrix-picker__footer">
        <button type="button" class="figure-link" @click="onDefault">
          {{ t('explore_figures.matrix_picker.default') }}
        </button>
        <q-space />
        <span class="matrix-picker__count">{{
          t('explore_figures.matrix_picker.count', { count: draft.length, max })
        }}</span>
        <q-btn v-close-popup flat no-caps :label="t('explore_figures.matrix_picker.cancel')" />
        <q-btn
          unelevated
          no-caps
          color="grey-10"
          :disable="draft.length < 2"
          :label="t('explore_figures.matrix_picker.apply')"
          @click="onApply"
        />
      </div>
    </template>
  </FigureDialog>
</template>

<script setup lang="ts">
/**
 * The pollutants of the correlation matrix, picked in a dialog (#229, R3):
 * one row per pollutant with records, with a bar of its records. The
 * pollutants selected in the filters stay checked: the matrix always shows
 * them (R5). "Default" goes back to the default set.
 */
import FacetList from '@/components/filters/FacetList.vue';
import FigureDialog from '@/components/explore/FigureDialog.vue';
import type { FacetOption } from '@/components/filters/facets';
import { shortParameterName } from '@/components/plots/charts';
import { useChartFormat } from '@/composables/useChartFormat';

interface Props {
  /** the pollutants in the matrix now, in its order */
  modelValue: string[];
  /** the pollutants with records under the filters */
  options: { value: string; label: string }[];
  /** records of each pollutant under the filters, for the bars */
  records: Map<string, number>;
  /** selected in the filters: always in the matrix, so not unchecked here */
  locked: string[];
  /** the set "Default" goes back to */
  defaults: string[];
  max: number;
  eyebrow?: string;
  loading?: boolean;
}

const props = withDefaults(defineProps<Props>(), { eyebrow: '', loading: false });
const emit = defineEmits<{ 'update:modelValue': [value: string[]] }>();
const { t } = useI18n();
const { formatCompact } = useChartFormat();

const open = ref(false);
const draft = ref<string[]>([]);
/**
 * The row order, fixed when the dialog opens: the pollutants of the matrix,
 * then the others, most records first. A row does not move when checked.
 */
const order = ref<string[]>([]);

const offered = computed(() => new Set(props.options.map((opt) => opt.value)));
const lockedSet = computed(() => new Set(props.locked.filter((slug) => offered.value.has(slug))));
const lockedShown = computed(() => [...lockedSet.value].map(shortParameterName));
const labels = computed(() => new Map(props.options.map((opt) => [opt.value, opt.label])));

const rows = computed<FacetOption[]>(() => {
  const full = draft.value.length >= props.max;
  return order.value.map((slug) => {
    const locked = lockedSet.value.has(slug);
    const capped = full && !draft.value.includes(slug);
    return {
      value: slug,
      label: labels.value.get(slug) ?? slug,
      count: props.records.get(slug) ?? 0,
      disabled: locked || capped,
      ...(locked
        ? { title: t('explore_figures.matrix_picker.locked_title') }
        : capped
          ? { title: t('explore_figures.matrix_picker.full', { max: props.max }) }
          : {}),
    };
  });
});

/** in the order of the rows */
function sorted(slugs: Iterable<string>): string[] {
  const picked = new Set(slugs);
  return order.value.filter((slug) => picked.has(slug));
}

function onOpen(): void {
  const current = props.modelValue.filter((slug) => offered.value.has(slug));
  const rest = props.options
    .map((opt) => opt.value)
    .filter((slug) => !current.includes(slug))
    .sort((a, b) => (props.records.get(b) ?? 0) - (props.records.get(a) ?? 0));
  order.value = [...current, ...rest];
  draft.value = sorted([...current, ...lockedSet.value]);
  open.value = true;
}

function onPick(value: string[]): void {
  // locked rows, and the unchecked rows at the cap, are disabled: the draft stays within the cap
  draft.value = sorted(value);
}

/** The default set, and the locked pollutants; these first when both do not fit. */
function onDefault(): void {
  const room = Math.max(0, props.max - lockedSet.value.size);
  const defaults = props.defaults.filter((slug) => offered.value.has(slug) && !lockedSet.value.has(slug));
  draft.value = sorted([...defaults.slice(0, room), ...lockedSet.value]);
}

function onApply(): void {
  emit('update:modelValue', [...draft.value]);
  open.value = false;
}
</script>

<style scoped lang="scss">
.matrix-picker {
  // room for a count like "11.1M"
  --facet-count-width: 44px;
}

.matrix-picker__open {
  border-radius: 2px;
}

.matrix-picker__lead {
  margin: 0 0 12px;
  font-size: 0.875rem;
  line-height: 1.5;
  color: $grey-8;
}

.matrix-picker__footer {
  display: flex;
  align-items: center;
  gap: 12px;
}

.matrix-picker__count {
  color: $grey-7;
  font-variant-numeric: tabular-nums;
}
</style>
