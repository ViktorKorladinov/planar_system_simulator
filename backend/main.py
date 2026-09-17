from fastapi import FastAPI, APIRouter
from api.handlers import register_exception_handlers
from api.routers import layout_router, simulation_router, order_list_router, ingredient_list_router
from api.routers import experiment_router, configuration_router
from api.routers.notification_router import webhook_router, notifications_router
from core.config import settings
from core.logger import configure_logging
from fastapi.middleware.cors import CORSMiddleware
import uvicorn


configure_logging()

app = FastAPI(title=settings.APP_NAME)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.SIMULATOR_ALLOWED_ORIGIN, settings.FRONTEND_ALLOWED_ORIGIN, "http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
register_exception_handlers(app)
api_v1_router = APIRouter(prefix=settings.API_V1_PREFIX)
api_v1_router.include_router(experiment_router.router)
api_v1_router.include_router(layout_router.router)
api_v1_router.include_router(configuration_router.router)
api_v1_router.include_router(simulation_router.router)
api_v1_router.include_router(webhook_router)
api_v1_router.include_router(notifications_router)
api_v1_router.include_router(order_list_router.router)
api_v1_router.include_router(ingredient_list_router.router)
app.include_router(api_v1_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=int(settings.BACKEND_PORT), reload=False)