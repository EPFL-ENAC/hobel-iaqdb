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
          <span v-if="item.html" v-html="item.html(dbobject)"></span>
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
          <div v-if="item.links">
            <dt v-if="item.links(dbobject)">
              <dl
                v-for="link in item.links(dbobject)"
                :key="link"
                class="q-mt-sm q-mb-sm field-item"
              >
                <a :href="link" target="_blank">
                  {{ truncateString(link, 100) }}
                  <q-icon name="open_in_new" />
                </a>
              </dl>
            </dt>
            <span v-else>-</span>
          </div>
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
import { toMaxDecimals } from 'src/utils/numbers';
import { truncateString } from 'src/utils/strings';

export interface FieldItem {
  field: string;
  label?: string;
  unit?: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  format?: (val: any) => string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  links?: (val: any) => string[] | null; // href
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  html?: (val: any) => string;
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
