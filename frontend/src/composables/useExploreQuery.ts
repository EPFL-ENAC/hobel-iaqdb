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
    const shared = join(route, current, key);
    const onAbort = () => leave(shared);
    own.signal.addEventListener('abort', onAbort, { once: true });
    try {
      const value = await shared.promise;
      results.set(key, value);
      if (controller === own) result.value = value;
    } catch (e: unknown) {
      // this chart moved on (or unmounted): the outcome is no longer its own
      if (own.signal.aborted || axios.isCancel(e)) return;
      error.value = e instanceof Error ? e.message : String(e);
      if (controller === own) result.value = null;
    } finally {
      own.signal.removeEventListener('abort', onAbort);
      if (controller === own) loading.value = false;
    }
  }

  watch(params, () => void run(), { immediate: true, deep: true });
  onBeforeUnmount(() => controller?.abort());

  return { result, loading, error, empty, refresh: run };
}
