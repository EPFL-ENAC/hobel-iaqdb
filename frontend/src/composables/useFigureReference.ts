import type { ExploreBenchmark } from '@/models';

/**
 * The reference one figure compares its pollutant with. Each figure keeps its
 * own picks, one per pollutant, so a pick under one chart leaves the other
 * charts alone. A pollutant without a pick uses its default. The picks last
 * as long as the page.
 */
export function useFigureReference(parameter: Ref<string | null>) {
  const exploreStore = useExploreStore();
  /** benchmark id per pollutant */
  const picks = ref<Record<string, string>>({});

  const benchmark = computed<ExploreBenchmark | null>(() => {
    const slug = parameter.value;
    const picked = slug ? picks.value[slug] : undefined;
    return exploreStore.benchmarksOf(slug).find((b) => b.id === picked) ?? exploreStore.defaultBenchmarkOf(slug);
  });

  function pick(b: ExploreBenchmark): void {
    if (parameter.value) picks.value = { ...picks.value, [parameter.value]: b.id };
  }

  return { benchmark, pick };
}
