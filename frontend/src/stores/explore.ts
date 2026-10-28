import { defineStore } from 'pinia';
import { schema as fetchSchema, measurements } from '@/api/explore';
import { setMeasurementYears } from '@/stores/filters';
import type { Dataset, ExploreDimension, ExploreSchema } from '@/models';
import type { OptionItem } from '@/utils/options';

/** the pollutant a figure showing one pollutant opens on, when it has data */
export const DEFAULT_PARAMETER = 'co2';

export const useExploreStore = defineStore(
  'explore',
  () => {
    const schema = ref<ExploreSchema | null>(null);
    /** the pollutants picked, persisted; none (the default) means every pollutant */
    const parameters = ref<string[]>([]);
    let pending: Promise<ExploreSchema> | null = null;
    let yearsPending: Promise<void> | null = null;
    /** study identifier to name, for chart labels; filled once by loadStudyNames */
    const studyNames = ref(new Map<string, string>());
    let studyNamesPending: Promise<void> | null = null;
    /** dataset id to name, for chart labels; filled as charts show datasets */
    const datasetNames = ref(new Map<string, string>());

    const dimensions = computed(
      () =>
        new Map<string, ExploreDimension>(
          (schema.value?.dimensions || []).map((d) => [d.key, d]),
        ),
    );

    const parameterOptions = computed<OptionItem[]>(() =>
      (schema.value?.parameters || []).map((p) => ({
        value: p.slug,
        // some labels already end with their unit, e.g. "Biocontaminants (sequence reads)"
        label: p.unit && !p.label.endsWith(`(${p.unit})`) ? `${p.label} (${p.unit})` : p.label,
      })),
    );

    async function loadSchema(): Promise<ExploreSchema> {
      void loadMeasurementYears();
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

    /** The first and last years holding records bound the year filter; loaded once. */
    function loadMeasurementYears(): Promise<void> {
      // from the dataset summaries: no scan of the daily aggregate
      yearsPending ??= measurements({ agg: 'coverage', by: ['parameter'] })
        .then((result) => {
          const year = (at?: string) => (at ? [Number(at.slice(0, 4))] : []);
          const first = result.buckets.flatMap((b) => year(b.coverage?.first_at));
          const last = result.buckets.flatMap((b) => year(b.coverage?.last_at));
          if (first.length && last.length) setMeasurementYears({ min: Math.min(...first), max: Math.max(...last) });
        })
        .catch(() => {
          // try again on the next load
          yearsPending = null;
        });
      return yearsPending;
    }

    /** Back to every pollutant. */
    function resetParameters(): void {
      parameters.value = [];
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

    /** Load the names of the datasets not known yet; a failure leaves them to their ids. */
    async function loadDatasetNames(ids: string[]): Promise<void> {
      const missing = [...new Set(ids)].filter((id) => !datasetNames.value.has(id));
      if (!missing.length) return;
      let datasets: Dataset[];
      try {
        datasets = await useCatalogStore().loadDatasetsByIds(missing.map(Number));
      } catch {
        // the ids stay as they are; the next call asks again
        return;
      }
      const names = new Map(datasetNames.value);
      for (const dataset of datasets) names.set(String(dataset.id), dataset.name);
      datasetNames.value = names;
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
      datasetNames,
      loadDatasetNames,
      showPair,
    };
  },
  // a key of its own: selections saved while CO₂ was the default start over on every pollutant
  { persist: { key: 'explore-parameters', pick: ['parameters'] } },
);
