from api.config import config
from enacit4r_auth.services.auth import KeycloakService, User  # noqa: F401

kc_service = KeycloakService(
    config.KEYCLOAK_URL,
    config.KEYCLOAK_REALM,
    config.KEYCLOAK_API_ID,
    config.KEYCLOAK_API_SECRET,
    "admin",
    client_roles=config.KEYCLOAK_CLIENT_ROLES,
)


def is_admin(user: User | None) -> bool:
    return user is not None and kc_service.admin_role in kc_service.get_roles(user)
