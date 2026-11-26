<template>
  <div class="q-pa-md">
    <template v-if="helpStore.content">
      <q-markdown
        no-heading-anchor-links
        :src="helpStore.content"
        class="app-md"
      />
      <q-separator class="q-my-md" />
    </template>

    <div class="text-h6 q-mb-sm">{{ t('glossary.title') }}</div>
    <q-input
      v-model="search"
      dense
      outlined
      clearable
      :placeholder="t('glossary.search')"
      class="q-mb-md"
    >
      <template #prepend>
        <q-icon name="search" size="18px" />
      </template>
    </q-input>

    <div v-if="!grouped.length" class="text-body2 text-grey-7">
      {{ t('glossary.no_match') }}
    </div>

    <q-list v-else dense separator>
      <template v-for="group in grouped" :key="group.category">
        <q-item-label header class="text-weight-medium text-grey-8 q-px-none">
          {{ t(`glossary.categories.${group.category}`) }}
        </q-item-label>
        <q-item v-for="entry in group.entries" :key="entry.key" class="q-px-none">
          <q-item-section>
            <q-item-label class="text-weight-medium">
              {{ entry.term }}
            </q-item-label>
            <q-item-label caption class="text-grey-8">
              {{ entry.definition }}
            </q-item-label>
          </q-item-section>
        </q-item>
      </template>
    </q-list>
  </div>
</template>

<script setup lang="ts">
import { GLOSSARY, GLOSSARY_CATEGORIES } from '@/utils/glossary';

const { t } = useI18n();
const helpStore = useHelpStore();
const search = ref<string | null>('');

const grouped = computed(() => {
  const needle = (search.value || '').trim().toLowerCase();
  const filtered = needle
    ? GLOSSARY.filter(
        (e) =>
          e.term.toLowerCase().includes(needle) ||
          e.definition.toLowerCase().includes(needle) ||
          (e.aliases ?? []).some((a) => a.toLowerCase().includes(needle)),
      )
    : GLOSSARY;

  return GLOSSARY_CATEGORIES.map((category) => ({
    category,
    entries: filtered.filter((e) => e.category === category),
  })).filter((g) => g.entries.length > 0);
});
</script>