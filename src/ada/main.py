from fastapi import FastAPI

from ada.api.health import router as health_router
from ada.api.webhooks import router as webhooks_router
from ada.auth.middleware import AuthMiddleware, RBACMiddleware
from ada.core.config import settings

app = FastAPI(
    title="ADA",
    description="Autonomous Decision Agent - Bleap's backoffice intelligence engine",
    version="0.1.0",
    debug=settings.debug,
)

# Auth middleware (order matters: RBAC runs after Auth)
app.add_middleware(RBACMiddleware)
app.add_middleware(AuthMiddleware)

app.include_router(health_router)
app.include_router(webhooks_router)
