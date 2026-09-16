from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import model_validator
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
    BACKEND_URL: Optional[str] = None
    API_V1_PREFIX: str = "/api/v1"
    BACKEND_API_URL: Optional[str] = None
    APP_NAME: str = "Xplanar Experiment Configurator"

    @model_validator(mode='after')
    def compute_urls(self):
        if not self.BACKEND_URL:
            self.BACKEND_URL = f"http://localhost:{self.BACKEND_PORT}"
        if not self.BACKEND_API_URL:
            self.BACKEND_API_URL = f"{self.BACKEND_URL}{self.API_V1_PREFIX}"
        return self

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
