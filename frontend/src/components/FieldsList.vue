<template>
  <q-list v-if="dbobject" dense separator>
    <q-item v-for="item in visibleItems" :key="item.field">
      <q-item-section>
        <q-item-label overline>
          {{ t(item.label ? item.label : item.field) }}
        </q-item-label>
      </q-item-section>
      <q-item-section>
        <q-item-label>
          <a
            v-if="item.link && item.link(dbobject)"
            :href="item.link(dbobject)"
            target="_blank"
            class="epfl"
            >{{ dbobject[item.field] }}</a
          >
          <span v-else-if="item.format"
            >{{ item.format(dbobject) }} {{ item.unit }}</span
          >
          <span v-else>
            {{
              dbobject[item.field]
                ? typeof dbobject[item.field] === 'number'
                  ? toMaxDecimals(dbobject[item.field], 3)
                  : dbobject[item.field]
                : '-'
            }}
            {{ item.unit }}
          </span>
          <div
            v-if="item.comment && item.comment(dbobject)"
            class="text-grey-6 q-mt-sm"
          >
            {{ item.comment(dbobject) }}
          </div>
        </q-item-label>
      </q-item-section>
    </q-item>
  </q-list>
</template>

<script setup lang="ts">
import { toMaxDecimals } from '@/utils/numbers';

export interface FieldItem {
  field: string;
  label?: string;
  unit?: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  format?: (val: any) => string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  link?: (val: any) => string | undefined; // href, must be a safe URL
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  visible?: (val: any) => boolean;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  comment?: (val: any) => string;
}

export interface FieldsListProps {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  dbobject: any;
  items?: FieldItem[];
}

const props = defineProps<FieldsListProps>();

const { t } = useI18n();

const visibleItems = computed(() => {
  return props.items?.filter((item) => {
    if (item.visible) {
      return item.visible(props.dbobject);
    }
    return true;
  }) || [];
});
</script>
