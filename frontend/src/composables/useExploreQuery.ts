/**
 * One explore request per chart: results are cached by canonical key for the
 * page session, identical in-flight requests are shared, and a parameter
 * change aborts the previous request so a stale response never paints.
 *
 * A shared request carries its own signal: a chart that stops waiting only
 * leaves the request, which is aborted once no chart waits on it anymore.
 */
import { canonicalKey, query, type ExploreRoute } from '@/api/explore';
import type { ExploreParams, ExploreResult } from '@/models';
import axios from 'axios';

interface Shared {
  promise: Promise<ExploreResult>;
  controller: AbortController;
  waiters: number;
}

const results = new Map<string, ExploreResult>();
const inflight = new Map<string, Shared>();

function join(route: ExploreRoute, params: ExploreParams, key: string): Shared {
  let shared = inflight.get(key);
  if (!shared) {
    const controller = new AbortController();
    const entry: Shared = {
      controller,
      waiters: 0,
      promise: query(route, params, controller.signal).finally(() => {
        if (inflight.get(key) === entry) inflight.delete(key);
      }),
    };
    inflight.set(key, entry);
    shared = entry;
  }
  shared.waiters += 1;
  return shared;
}

function leave(shared: Shared) {
  shared.waiters -= 1;
  if (shared.waiters === 0) shared.controller.abort();
}

export function clearExploreCache() {
  results.clear();
  inflight.clear();
}

/**
 * Imperative explore request: `load(params)` runs one request and fills
 * `result`; the caller decides when. A `load` aborts the previous one.
 */
export function useExploreRequest(route: ExploreRoute) {
  const result = ref<ExploreResult | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);
  let controller: AbortController | null = null;

  const empty = computed(() => result.value !== null && result.value.meta.n === 0);

  /** Resolves with the result, or null when aborted by a later load or failed. */
  async function load(params: ExploreParams | null): Promise<ExploreResult | null> {
    controller?.abort();
    controller = null;
    if (params === null) {
      result.value = null;
      return null;
    }
    const key = canonicalKey(route, params);
    const cached = results.get(key);
    if (cached) {
      result.value = cached;
      error.value = null;
      return cached;
    }
    const own = new AbortController();
    controller = own;
    loading.value = true;
    error.value = null;
    const shared = join(route, params, key);
    const onAbort = () => leave(shared);
    own.signal.addEventListener('abort', onAbort, { once: true });
    try {
      const value = await shared.promise;
      results.set(key, value);
      if (controller !== own) return null;
      result.value = value;
      return value;
    } catch (e: unknown) {
      // this chart moved on (or unmounted): the outcome is no longer its own
      if (own.signal.aborted || axios.isCancel(e)) return null;
      error.value = e instanceof Error ? e.message : String(e);
      if (controller === own) result.value = null;
      return null;
    } finally {
      own.signal.removeEventListener('abort', onAbort);
      if (controller === own) loading.value = false;
    }
  }

  onBeforeUnmount(() => controller?.abort());

  return { result, loading, error, empty, load };
}

/** Reactive explore request: re-runs whenever `params()` changes. */
export function useExploreQuery(route: ExploreRoute, params: () => ExploreParams | null) {
  const request = useExploreRequest(route);
  const run = () => request.load(params());
  watch(params, () => void run(), { immediate: true, deep: true });
  return { ...request, refresh: run };
}
