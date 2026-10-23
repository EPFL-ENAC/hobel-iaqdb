<template>
  <q-btn-toggle
    :model-value="modelValue"
    class="figure-toggle"
    :options="options"
    no-caps
    unelevated
    dense
    color="white"
    text-color="grey-10"
    toggle-color="grey-10"
    toggle-text-color="white"
    @update:model-value="(value: V) => emit('update:modelValue', value)"
  />
</template>

<script setup lang="ts" generic="V extends string">
/** A bordered choice of a few options in a figure's controls, e.g. Pearson | Spearman. */
defineProps<{
  modelValue: V;
  options: { value: V; label: string }[];
}>();
const emit = defineEmits<{ 'update:modelValue': [value: V] }>();
</script>

<style scoped lang="scss">
.figure-toggle {
  border: 1px solid $grey-10;
  border-radius: 0;

  :deep(.q-btn) {
    border-radius: 0;
    padding: 4px 12px;
  }

  :deep(.q-btn + .q-btn) {
    border-left: 1px solid $grey-10;
  }
}
</style>
