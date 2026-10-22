<template>
  <div class="ranked-bars" :class="{ 'ranked-bars--loading': loading }">
    <div class="ranked-bars__body">
      <!-- as many lines as the list can show, filled or not: the height never changes -->
      <RankedTable
        v-bind="tableProps"
        :rows="visible"
        :other="other"
        :min-rows="lines"
        @select="(row) => emit('select', row)"
      >
        <template v-if="$slots['label-header']" #label-header><slot name="label-header" /></template>
      </RankedTable>
      <div v-if="$slots.message" class="ranked-bars__message">
        <slot name="message" />
      </div>
      <q-inner-loading :showing="loading && !rows.length && !$slots.message" color="grey-7" />
    </div>
    <div class="figure-footer">
      <button v-if="hidden.length" type="button" class="ranked-bars__toggle" @click="showAll = true">
        {{ t('ranked_bars.show_all', { count: rows.length }) }}
      </button>
      <span class="ranked-bars__hint" :title="hintText">
        <slot name="hint" />
      </span>
    </div>
    <q-dialog v-model="showAll">
      <q-card class="ranked-bars__dialog">
        <q-card-section class="row items-start no-wrap q-pb-sm">
          <div class="col">
            <div v-if="dialogEyebrow" class="ranked-bars__eyebrow">{{ dialogEyebrow }}</div>
            <div class="ranked-bars__title">{{ dialogTitle }}</div>
          </div>
          <q-btn
            class="q-ml-md" v-close-popup flat round dense icon="close" :aria-label="t('ranked_bars.close')" />
        </q-card-section>
        <q-card-section class="ranked-bars__scroll" :class="{ 'ranked-bars--loading': loading }">
          <RankedTable v-bind="tableProps" :rows="rows" @select="(row) => emit('select', row)">
            <template v-if="$slots['label-header']" #label-header><slot name="label-header" /></template>
          </RankedTable>
        </q-card-section>
        <q-card-section v-if="$slots.hint" class="ranked-bars__dialog-hint">
          <slot name="hint" />
        </q-card-section>
      </q-card>
    </q-dialog>
  </div>
</template>

<script setup lang="ts" generic="T">
/**
 * A ranked list of horizontal bars: the first `limit` rows, then the others
 * summed into one hatched row; "Show all" lists every row in a dialog.
 */
import RankedTable from '@/components/explore/RankedTable.vue';
import type { RankedColumn, RankedRow } from '@/components/explore/ranked';

interface Props {
  /** in the order shown */
  rows: RankedRow<T>[];
  /** rows shown before the rest are summed into "Other" */
  limit?: number | undefined;
  labelHeader?: string;
  barHeader?: string;
  valueHeader?: string;
  /** cells after the value */
  columns?: RankedColumn<T>[];
  /** keys of the rows drawn in the accent colour; all of them when absent */
  highlighted?: string[] | undefined;
  /** label of the summed row, "Other" by default */
  otherLabel?: string;
  formatValue?: ((value: number) => string) | undefined;
  /** how a row is laid out, as in RankedTable */
  layout?: 'inline' | 'stacked' | undefined;
  /** in the inline layout, the share of the width the labels get */
  labelWidth?: string | undefined;
  /** heading of the full list dialog */
  dialogEyebrow?: string;
  dialogTitle?: string;
  /** dims the rows while a new set loads */
  loading?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  limit: 10,
  labelHeader: '',
  barHeader: '',
  valueHeader: '',
  columns: () => [],
  highlighted: undefined,
  otherLabel: '',
  formatValue: undefined,
  layout: 'inline',
  labelWidth: '30%',
  dialogEyebrow: '',
  dialogTitle: '',
  loading: false,
});
const emit = defineEmits<{ select: [row: RankedRow<T>] }>();
const { t } = useI18n();

const slots = useSlots();
const showAll = ref(false);

/** the hint in full, for when the footer cuts it short */
const hintText = computed(() =>
  (slots.hint?.() || [])
    .map((node) => (typeof node.children === 'string' ? node.children : ''))
    .join('')
    .trim() || undefined,
);

/** the most lines the list shows: `limit` rows and "Other" */
const lines = computed(() => props.limit + 1);

/** "Other" only when it stands for two rows or more: else show the one row */
const collapses = computed(() => props.rows.length > props.limit + 1);
const visible = computed(() => (collapses.value ? props.rows.slice(0, props.limit) : props.rows));
const hidden = computed(() => (collapses.value ? props.rows.slice(props.limit) : []));
const other = computed(() =>
  hidden.value.length ? { rows: hidden.value, value: hidden.value.reduce((sum, row) => sum + row.value, 0) } : null,
);

/** what the list and the dialog draw alike */
const tableProps = computed(() => ({
  labelHeader: props.labelHeader,
  barHeader: props.barHeader,
  valueHeader: props.valueHeader,
  columns: props.columns,
  highlighted: props.highlighted,
  otherLabel: props.otherLabel,
  formatValue: props.formatValue,
  layout: props.layout,
  labelWidth: props.labelWidth,
}));
</script>

<style scoped lang="scss">
.ranked-bars {
  display: flex;
  flex-direction: column;
  flex: 1;
  transition: opacity 0.2s;
}

.ranked-bars--loading {
  opacity: 0.5;
}


.ranked-bars__body {
  position: relative;
  margin-bottom: 24px;
}

// an empty or failed load, over the reserved lines
.ranked-bars__message {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  background: white;
  text-align: center;
}

.ranked-bars__toggle {
  flex-shrink: 0;
  padding: 0;
  border: 0;
  background: none;
  font: inherit;
  color: $figure-accent-strong;
  text-decoration: underline;
  text-underline-offset: 0.2em;
  cursor: pointer;
}

.ranked-bars__hint {
  min-width: 0;
  margin-left: auto;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: $grey-9;
}

.ranked-bars__dialog {
  width: 760px;
  max-width: 92vw;
  border-radius: 0;
}

.ranked-bars__eyebrow {
  font-size: 0.8125rem;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  color: $grey-10;
  margin-bottom: 8px;
}

.ranked-bars__title {
  font-size: 1.375rem;
  line-height: 1.3;
  color: $grey-10;
}

.ranked-bars__scroll {
  max-height: 65vh;
  overflow-y: auto;
  padding-top: 0;
}

.ranked-bars__dialog-hint {
  border-top: 1px solid $grey-4;
  font-size: 0.875rem;
  color: $grey-9;
}
</style>
