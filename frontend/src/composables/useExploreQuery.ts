/**
 * One explore request per chart: results are cached by canonical key for the
 * page session, identical in-flight requests are shared, and a parameter
 * change aborts the previous request so a stale response never paints.
 */
import { canonicalKey, query, type ExploreRoute } from '@/api/explore';
import type { ExploreParams, ExploreResult } from '@/models';
import axios from 'axios';

const results = new Map<string, ExploreResult>();
const inflight = new Map<string, Promise<ExploreResult>>();

export function clearExploreCache() {
  results.clear();
  inflight.clear();
}

export function useExploreQuery(route: ExploreRoute, params: () => ExploreParams | null) {
  const result = ref<ExploreResult | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);
  let controller: AbortController | null = null;

  const empty = computed(() => result.value !== null && result.value.meta.n === 0);

  async function run() {
    const current = params();
    controller?.abort();
    controller = null;
    if (current === null) {
      result.value = null;
      return;
    }
    const key = canonicalKey(route, current);
    const cached = results.get(key);
    if (cached) {
      result.value = cached;
      error.value = null;
      return;
    }
    const own = new AbortController();
    controller = own;
    loading.value = true;
    error.value = null;
    try {
      let pending = inflight.get(key);
      if (!pending) {
        pending = query(route, current, own.signal).finally(() => inflight.delete(key));
        inflight.set(key, pending);
      }
      const value = await pending;
      results.set(key, value);
      if (controller === own) result.value = value;
    } catch (e: unknown) {
      if (axios.isCancel(e)) return;
      error.value = e instanceof Error ? e.message : String(e);
      if (controller === own) result.value = null;
    } finally {
      if (controller === own) loading.value = false;
    }
  }

  watch(params, () => void run(), { immediate: true, deep: true });
  onBeforeUnmount(() => controller?.abort());

  return { result, loading, error, empty, refresh: run };
}
