import { defineStore } from 'pinia';
import { schema as fetchSchema } from '@/api/explore';
import type { ExploreDimension, ExploreSchema } from '@/models';
import type { OptionItem } from '@/utils/options';

export const DEFAULT_PARAMETER = 'co2';

export const useExploreStore = defineStore(
  'explore',
  () => {
    const schema = ref<ExploreSchema | null>(null);
    /** persisted; first visit starts on the default, an empty list means all datasets */
    const parameters = ref<string[]>([DEFAULT_PARAMETER]);
    let pending: Promise<ExploreSchema> | null = null;
    /** study identifier to name, for chart labels; filled once by loadStudyNames */
    const studyNames = ref(new Map<string, string>());
    let studyNamesPending: Promise<void> | null = null;

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
            // drop the default, or persisted slugs, the schema does not offer
            const known = new Set(value.parameters.map((p) => p.slug));
            parameters.value = parameters.value.filter((slug) =>
              known.has(slug),
            );
            return value;
          })
          .finally(() => {
            pending = null;
          });
      }
      return pending;
    }

    /** Select the default parameter when the schema offers it, none otherwise. */
    function resetParameters(): void {
      parameters.value = schema.value?.parameters.some(
        (p) => p.slug === DEFAULT_PARAMETER,
      )
        ? [DEFAULT_PARAMETER]
        : [];
    }

    function dimension(key: string): ExploreDimension | undefined {
      return dimensions.value.get(key);
    }

    /** Load the study names once; later calls share the first request. */
    function loadStudyNames(): Promise<void> {
      if (!studyNamesPending)
        studyNamesPending = useCatalogStore()
          .loadStudySummaries(0, 1000, false)
          .then((res) => {
            studyNames.value = new Map(
              res.data.map((s) => [s.identifier, s.name]),
            );
          })
          .catch((err: unknown) => {
            // a failed load may be retried by the next caller
            studyNamesPending = null;
            throw err;
          });
      return studyNamesPending;
    }

    /**
     * Event: open the pair x × y in the custom relationship chart, e.g. from a
     * correlation matrix cell. The chart listens with `$onAction`.
     */
    function showPair(x: string, y: string): { x: string; y: string } {
      return { x, y };
    }

    function parameterLabel(slug: string): string {
      return (
        schema.value?.parameters.find((p) => p.slug === slug)?.label || slug
      );
    }

    return {
      schema,
      parameters,
      dimensions,
      parameterOptions,
      loadSchema,
      resetParameters,
      dimension,
      parameterLabel,
      studyNames,
      loadStudyNames,
      showPair,
    };
  },
  { persist: { pick: ['parameters'] } },
);
