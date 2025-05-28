<template>
  <q-list v-if="dbobject" separator>
    <q-item v-for="item in visibleItems" :key="item.field">
      <q-item-section>
        <q-item-label overline>
          {{ $t(item.label ? item.label : item.field) }}
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

<script lang="ts">
import { toMaxDecimals } from 'src/utils/numbers';
import { truncateString } from 'src/utils/strings';
export default defineComponent({
  name: 'FieldsList',
});
</script>
<script setup lang="ts">
import { withDefaults } from 'vue';
import { DBModel, Person, Study } from 'src/models';

export interface FieldItem<T extends DBModel> {
  field: string;
  label?: string;
  unit?: string;
  format?: (val: T) => string;
  links?: (val: T) => string[] | null; // href
  html?: (val: T) => string;
  visible?: (val: T) => boolean;
  comment?: (val: T) => string;
}

export interface FieldsListProps {
  dbobject: Study | Person;
  items: FieldItem<Study | Person>[];
}

const props = withDefaults(defineProps<FieldsListProps>(), {
  dbobject: undefined,
  items: undefined,
});

const visibleItems = computed(() => {
  return props.items.filter((item) => {
    if (item.visible) {
      return item.visible(props.dbobject);
    }
    return true;
  });
});
</script>
