import { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: () => import('layouts/SimpleLayout.vue'),
    children: [
      { path: '', component: () => import('pages/HomePage.vue') },
      {
        path: '/contribute',
        component: () => import('pages/ContributePage.vue'),
      },
      {
        path: '/study/:id',
        component: () => import('src/pages/StudyPage.vue'),
      },
      {
        path: '/admin',
        component: () => import('pages/AdminPage.vue'),
      },
      {
        path: '/profile',
        component: () => import('pages/ProfilePage.vue'),
      },
    ],
  },
  {
    path: '/',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      { path: '/map', component: () => import('src/pages/MapPage.vue') },
      {
        path: '/catalog',
        component: () => import('src/pages/CatalogPage.vue'),
      },
      { path: '/search', component: () => import('src/pages/SearchPage.vue') },
    ],
  },

  // Always leave this as last one,
  // but you can also remove it
  {
    path: '/:catchAll(.*)*',
    component: () => import('pages/ErrorNotFound.vue'),
  },
];

export default routes;
