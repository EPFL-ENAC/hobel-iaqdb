<template>
  <label class="figure-menu" :title="selectedLabel">
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
const props = defineProps<{
  label: string;
  modelValue: V;
  options: { value: V; label: string }[];
}>();
const emit = defineEmits<{ 'update:modelValue': [value: V] }>();

/** the whole choice on hover, when it is cut short */
const selectedLabel = computed(() => props.options.find((opt) => opt.value === props.modelValue)?.label);
</script>

<style scoped lang="scss">
.figure-menu {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  // never wider than the card: a long choice is cut short instead
  max-width: 100%;
  min-width: 0;
  font-size: 0.875rem;
  color: $grey-10;
}

.figure-menu__label {
  flex: none;
}

.figure-menu__select {
  min-width: 120px;
  flex: 0 1 auto;
  overflow: hidden;

  :deep(.q-field__control) {
    border-radius: 2px;
  }

  :deep(.q-field__control-container),
  :deep(.q-field__native) {
    flex-wrap: nowrap;
    min-width: 0;
  }

  :deep(.q-field__native > span) {
    min-width: 0;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
  }
}
</style>
