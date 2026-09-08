from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv()


class Settings(BaseSettings):
    # --- Project Info ---
    PROJECT_NAME: str = "Xplanar Experiment Configurator"
    DEBUG: bool = False

    # --- Database ---
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/dbname"

    # --- Backend ---
    BACKEND_PORT: int = 8000
    BACKEND_URL: str = f"http://localhost:{str(BACKEND_PORT)}"
    API_V1_PREFIX: str = "/api/v1"
    BACKEND_API_URL: str = f"{BACKEND_URL}{API_V1_PREFIX}"
    APP_NAME: str = "Xplanar Experiment Configurator"

    # --- Celery ---
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    CELERY_WORKER_PREFETCH_MULTIPLIER: int = 1
    CELERY_TASK_ACKS_LATE: bool = True

    # --- Simulator ---
    SIMULATOR_API_KEY: str = "key"
    SIMULATOR_ALLOWED_ORIGIN: str = "http://localhost:3000"

    # --- Simulator ---
    FRONTEND_ALLOWED_ORIGIN: str = "http://localhost:5173"

    # --- Solvers ---
    MAX_PROCESS_AMOUNT: int = 8

    # --- CPLEX ---
    CPLEX_PATH: str = "C:\\Program Files\\IBM\\ILOG\\CPLEX_Studio2212\\cpoptimizer\\bin\\x64_win64\\cpoptimizer.exe"
    ARM64_PATH: str = "/Users/viktorkorladinov/Applications/CPLEX_Studio2212/cpoptimizer/bin/arm64_osx/cpoptimizer"
    GRAPH_TEMPLATE_PATH: Path = BASE_DIR / "templates" / "graph_template.html"
    GRAPH_FOLDER_PATH: Path = BASE_DIR / "data" / "plots"

    model_config = SettingsConfigDict(env_file=f"{BASE_DIR}/.env", extra="ignore")


settings = Settings()
