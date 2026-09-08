from abc import ABC, abstractmethod


class BaseTaskClient(ABC):
    @abstractmethod
    def enqueue_experiment(self, experiment_id: int) -> str:
        """Creates tasks for an experiment and adds it to the queue.
        Args:
            experiment_id: ID of the experiment which should be enqueued.

        Returns:
            ID of the task containing the experiment that was enqueued.
        """

    @abstractmethod
    def cancel_experiment(self, task_id: str) -> None:
        """Removes the task from the queue or stops worker which works on it.
        Args:
            task_id: ID of the task which should be canceled.
        """
