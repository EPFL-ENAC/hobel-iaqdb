import type { TableRequestProps } from '@/components/models';

/**
 * Server-side paged q-table over one of the current study's item lists,
 * fetched only when the table is mounted (i.e. its tab is visible).
 */
export function useStudyItemsTable<T>(
  items: 'buildings' | 'spaces' | 'instruments' | 'datasets',
  sortBy = 'identifier',
) {
  const catalogStore = useCatalogStore();

  const tableRef = ref();
  const rows = ref<T[]>([]);
  const loading = ref(false);
  const pagination = ref({
    sortBy,
    descending: false,
    page: 1,
    rowsPerPage: 25,
    rowsNumber: 0,
  });

  function onRequest(props: TableRequestProps) {
    if (!catalogStore.study?.id) return;
    const { page, rowsPerPage, sortBy, descending } = props.pagination;
    loading.value = true;
    void catalogStore
      .loadStudyItems<T>(items, (page - 1) * rowsPerPage, rowsPerPage, sortBy, descending)
      .then((result) => {
        rows.value = result.data;
        pagination.value = { page, rowsPerPage, sortBy, descending, rowsNumber: result.total };
      })
      .finally(() => (loading.value = false));
  }

  watch(
    () => catalogStore.study?.id,
    () => {
      rows.value = [];
      pagination.value.page = 1;
      tableRef.value?.requestServerInteraction();
    },
  );
  onMounted(() => tableRef.value?.requestServerInteraction());

  return { tableRef, rows, loading, pagination, onRequest };
}
