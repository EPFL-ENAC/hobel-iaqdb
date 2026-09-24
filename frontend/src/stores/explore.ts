import { defineStore } from 'pinia';
import { api } from '@/boot/api';
import { schema as fetchSchema } from '@/api/explore';
import type {
  ExploreDimension,
  ExploreSchema,
  StudySummariesResult,
} from '@/models';
import type { OptionItem } from '@/utils/options';

export const DEFAULT_PARAMETER = 'co2';

export const useExploreStore = defineStore('explore', () => {
  const schema = ref<ExploreSchema | null>(null);
  const parameters = ref<string[]>([]);
  /** study identifier -> name, for charts keyed by study */
  const studyNames = ref<Record<string, string>>({});
  let pending: Promise<ExploreSchema> | null = null;

  const dimensions = computed(
    () =>
      new Map<string, ExploreDimension>(
        (schema.value?.dimensions || []).map((d) => [d.key, d]),
      ),
  );

  const parameterOptions = computed<OptionItem[]>(() =>
    (schema.value?.parameters || []).map((p) => ({
      value: p.slug,
      label: p.unit ? `${p.label} (${p.unit})` : p.label,
    })),
  );

  async function loadSchema(): Promise<ExploreSchema> {
    if (schema.value) return schema.value;
    if (!pending) {
      pending = fetchSchema()
        .then((value) => {
          schema.value = value;
          if (
            !parameters.value.length &&
            value.parameters.some((p) => p.slug === DEFAULT_PARAMETER)
          ) {
            parameters.value = [DEFAULT_PARAMETER];
          }
          return value;
        })
        .finally(() => {
          pending = null;
        });
    }
    return pending;
  }

  function dimension(key: string): ExploreDimension | undefined {
    return dimensions.value.get(key);
  }

  function parameterLabel(slug: string): string {
    return schema.value?.parameters.find((p) => p.slug === slug)?.label || slug;
  }

  async function loadStudyNames(identifiers: string[]): Promise<void> {
    const missing = identifiers.filter((id) => !(id in studyNames.value));
    if (!missing.length) return;
    const response = await api.get('/catalog/study-summaries', {
      params: {
        filter: JSON.stringify({ identifier: missing }),
        range: JSON.stringify([0, missing.length - 1]),
      },
    });
    const names = { ...studyNames.value };
    for (const study of (response.data as StudySummariesResult).data)
      names[study.identifier] = study.name;
    studyNames.value = names;
  }

  function studyName(identifier: string): string {
    return studyNames.value[identifier] || identifier;
  }

  return {
    schema,
    parameters,
    studyNames,
    dimensions,
    parameterOptions,
    loadSchema,
    dimension,
    parameterLabel,
    loadStudyNames,
    studyName,
  };
});
