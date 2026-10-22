<template>
  <label class="figure-menu">
    <span class="figure-menu__label">{{ label }}</span>
    <q-select
      :model-value="modelValue"
      :options="options"
      emit-value
      map-options
      dense
      outlined
      options-dense
      class="figure-menu__select"
      @update:model-value="(value) => emit('update:modelValue', value)"
    />
  </label>
</template>

<script setup lang="ts" generic="V extends string | number | null">
/** A labelled menu in a figure's header, e.g. "Context [Country]". */
defineProps<{
  label: string;
  modelValue: V;
  options: { value: V; label: string }[];
}>();
const emit = defineEmits<{ 'update:modelValue': [value: V] }>();
</script>

<style scoped lang="scss">
.figure-menu {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 0.875rem;
  color: $grey-10;
}

.figure-menu__select {
  min-width: 120px;

  :deep(.q-field__control) {
    border-radius: 2px;
  }
}
</style>
