import { defineStore } from 'pinia';
import { keycloak } from 'src/boot/api';
import type { KeycloakProfile } from 'keycloak-js';


export const useAuthStore = defineStore('auth', () => {

  const profile = ref<KeycloakProfile>();
  const realmRoles = ref<string[]>([]);
  const isAuthenticated = computed(() => profile.value !== undefined);
  const isAdmin = computed(() => realmRoles.value.includes('admin'));
  const accessToken = computed(() => keycloak.token);

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
    });
  }

  async function updateToken() {
    return await keycloak.updateToken(30)
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