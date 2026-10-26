import { type RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: () => import('@/layouts/SimpleLayout.vue'),
    children: [
      { path: '', component: () => import('@/pages/HomePage.vue') },
      {
        path: '/contribute',
        component: () => import('@/pages/ContributePage.vue'),
      },
      {
        path: '/study',
        component: () => import('@/pages/StudyPage.vue'),
      },
      {
        path: '/admin',
        component: () => import('@/pages/AdminPage.vue'),
      },
      {
        path: '/admin/downloads',
        component: () => import('@/pages/AdminPage.vue'),
      },
      {
        path: '/admin/ingestion',
        component: () => import('@/pages/AdminPage.vue'),
      },
    ],
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    children: [
      {
        path: '/explore',
        name: 'explore',
        // the filter bar sits in the layout's header, under the toolbar
        components: {
          default: () => import('@/pages/ExplorePage.vue'),
          bar: () => import('@/components/filters/FilterBar.vue'),
        },
      },
      {
        path: '/data-hub',
        name: 'data-hub',
        component: () => import('@/pages/DataHubPage.vue'),
      },
    ],
  },

  // Always leave this as last one,
  // but you can also remove it
  {
    path: '/:catchAll(.*)*',
    component: () => import('@/pages/ErrorNotFound.vue'),
  },
];

export default routes;
