import { defineBoot } from '#q-app/wrappers';
import axios, { type AxiosInstance } from 'axios';
import Keycloak from 'keycloak-js';

declare module '@vue/runtime-core' {
  interface ComponentCustomProperties {
    $axios: AxiosInstance;
    $api: AxiosInstance;
  }
}

interface CustomWindow extends Window {
  env: {
    AUTH_CLIENT_ID: string
    API_URL: string
    API_PATH: string
  }
}

const appEnv = (window as unknown as CustomWindow).env

const keycloak = new Keycloak({
  url: 'https://enac-it-sso.epfl.ch/',
  realm: 'HOBEL',
  clientId: appEnv.AUTH_CLIENT_ID,
});

const cdnUrl = 'https://enacit4r-cdn.epfl.ch/';
const baseUrl = `${appEnv.API_URL}${appEnv.API_PATH}`
const api = axios.create({
  baseURL: baseUrl,
});

export default defineBoot(({ app }) => {
  // for use inside Vue files (Options API) through this.$axios and this.$api

  app.config.globalProperties.$axios = axios;
  // ^ ^ ^ this will allow you to use this.$axios (for Vue Options API form)
  //       so you won't necessarily have to import axios in each vue file

  app.config.globalProperties.$api = api;
  // ^ ^ ^ this will allow you to use this.$api (for Vue Options API form)
  //       so you can easily perform requests against your app's API
});

export { api, baseUrl, cdnUrl, keycloak };
