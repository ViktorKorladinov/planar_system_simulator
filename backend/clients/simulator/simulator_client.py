import requests

from api.dtos.requests.webhook import ExperimentStatusUpdateDTO
from core.config import settings
from domain.enums import ExperimentStatus


class SimulatorClient:
    def __init__(self, api_key: str):
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {api_key}"})

    def notify_experiment_status_change(self, experiment_id: int, status: ExperimentStatus) -> bool:
        """Sends a thin notification to the simulator when experiment status is updated.

        Args:
            experiment_id: ID of the experiment which was updated.
            status: New experiment status.

        Returns:
            True if the notification was sent.
        """
        url = f"{settings.BACKEND_API_URL}/webhooks/experiment-updated"
        payload = ExperimentStatusUpdateDTO(experiment_id=experiment_id, status=status).model_dump(mode='json')

        try:
            response = self.session.post(url, json=payload, timeout=5)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            raise e
