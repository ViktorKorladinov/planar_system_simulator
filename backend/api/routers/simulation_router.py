import os

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import FileResponse

from api.dtos.responses.simulation import SimulationBatchGetResponseDTO, SimulationGetResponseDTO
from core.config import settings
from dependencies import get_experiment_service
from services.experiment_service import ExperimentService

router = APIRouter(
    prefix="/simulations",
    tags=["Simulations"]
)


@router.get(
    "",
    response_model=SimulationBatchGetResponseDTO,
    summary="Get a paginated list of simulations."
)
@router.get(
    "/",
    response_model=SimulationBatchGetResponseDTO,
    include_in_schema=False
)
async def get_simulations(
        page: int = 1,
        size: int = 20,
        experiment_service: ExperimentService = Depends(get_experiment_service)
):
    """Fetches a paginated overview of all available simulations."""
    return experiment_service.get_simulations(page=page, size=size)


@router.get(
    "/{simulation_id}",
    response_model=SimulationGetResponseDTO,
    summary="Get full details of a single simulation."
)
async def get_simulation(
        simulation_id: int,
        experiment_service: ExperimentService = Depends(get_experiment_service)
):
    """Fetches full simulation data."""
    simulation = experiment_service.get_simulation_by_id(simulation_id)
    if not simulation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Simulation not found")
    return simulation


@router.get(
    "/{simulation_id}/plots/{filename}",
    response_class=FileResponse,
    summary="Serve HTML Gantt charts and plots for a simulation."
)
async def get_simulation_plot(
        simulation_id: int,
        filename: str
):
    """
    Serves the HTML files with Gannt charts.
    """
    base_storage_path = settings.GRAPH_FOLDER_PATH
    file_path = os.path.join(base_storage_path, str(simulation_id), f"{filename}.html")
    if not os.path.isfile(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plot file '{filename}' not found for simulation {simulation_id}"
        )
    return FileResponse(path=file_path, media_type="text/html")
