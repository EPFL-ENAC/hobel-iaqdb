window.env = {
  API_URL: 'http://localhost:8000',
  API_PATH: '',
  // Keycloak (defaults: https://enac-it-sso2.epfl.ch/, realm EPFL)
  // KEYCLOAK_URL: 'https://enac-it-sso2.epfl.ch/',
  // KEYCLOAK_REALM: 'EPFL',
  // Keycloak client ID of the frontend
  AUTH_CLIENT_ID: 'iaqdb-local-ui',
  // Keycloak client ID of the backend, which holds the admin role (client role). Unset when the
  // admin role is a realm role
  AUTH_API_CLIENT_ID: 'iaqdb-local-api',
}
