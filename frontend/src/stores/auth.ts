import { defineStore } from 'pinia';
import { keycloak } from '@/boot/api';
import type { KeycloakProfile } from 'keycloak-js';


export const useAuthStore = defineStore('auth', () => {

  const profile = ref<KeycloakProfile>();
  const realmRoles = ref<string[]>([]);
  const isAuthenticated = computed(() => profile.value !== undefined);
  const isAdmin = computed(() => realmRoles.value.includes('admin'));

  // keycloak is a plain (non-reactive) Keycloak instance, so a `computed`
  // reading keycloak.token would never invalidate: Vue has nothing to track
  // and the value freezes at whatever it was on first access, even after
  // updateToken() refreshes the underlying token. Track it explicitly instead.
  const accessToken = ref<string | undefined>(keycloak.token)

  async function init() {
    if (isAuthenticated.value) return Promise.resolve(true);
    profile.value = undefined;
    realmRoles.value = [];
    return keycloak.init({
      onLoad: 'check-sso' // Optional: 'login-required' forces login right away, 'check-sso' checks if the user is already logged in.
    }).then(async (authenticated: boolean) => {
      if (authenticated) {
        realmRoles.value = keycloak.tokenParsed?.realm_access?.roles || [];
        profile.value = await keycloak.loadUserProfile();
        accessToken.value = keycloak.token
        keycloak.onTokenExpired = () => void updateToken().catch(() => undefined)
        keycloak.onAuthRefreshSuccess = () => {
          accessToken.value = keycloak.token
        }
        return authenticated;
      } else {
        return authenticated;
      }
    });
  }

  async function login() {
    if (isAuthenticated.value) return;
    // redirects to keycloak login page
    return await keycloak.login();
  }

  async function logout() {
    if (!isAuthenticated.value) return;
    return await keycloak.logout({
      redirectUri: window.location.origin,
    }).then(() => {
      profile.value = undefined;
      realmRoles.value = [];
      accessToken.value = undefined
    });
  }

  async function updateToken() {
    return await keycloak.updateToken(30)
      .then((refreshed: boolean) => {
        if (refreshed) {
          accessToken.value = keycloak.token
        }
        return refreshed;
      })
      .catch(() => {
        console.error('Failed to refresh token');
        return logout().finally(() => { throw new Error('Failed to refresh token'); });
      });
  }

  return {
    isAuthenticated,
    isAdmin,
    profile,
    realmRoles,
    accessToken,
    init,
    login,
    logout,
    updateToken,
  };

});
