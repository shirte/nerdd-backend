import logging

from nerdd_link import Action, Channel, LogMessage, ResultCheckpointMessage
from omegaconf import DictConfig

from ..data import RecordNotFoundError, Repository
from ..models import JobUpdate, ResultCheckpoint

__all__ = ["SaveResultCheckpointToDb"]

logger = logging.getLogger(__name__)


class SaveResultCheckpointToDb(Action[ResultCheckpointMessage]):
    def __init__(self, channel: Channel, repository: Repository, config: DictConfig) -> None:
        super().__init__(channel.result_checkpoints_topic())
        self.repository = repository
        self.config = config

    async def _process_message(self, message: ResultCheckpointMessage) -> None:
        job_id = message.job_id
        checkpoint_id = message.checkpoint_id
        logger.info(f"Received result checkpoint {checkpoint_id} for job {job_id}")

        try:
            # update job status
            job = await self.repository.update_job(JobUpdate(id=job_id, status="processing"))
        except RecordNotFoundError:
            # the job might not exist anymore, e.g., if it was deleted
            logger.warning(f"Job {job_id} not found, skipping checkpoint processing")
            return

        # create result checkpoint
        await self.repository.create_result_checkpoint(
            ResultCheckpoint(
                id=f"{job_id}-{checkpoint_id}", job_type=job.job_type, **message.model_dump()
            )
        )

        # check if all checkpoints have been processed
        checkpoints = await self.repository.get_result_checkpoints_by_job_id(job_id)
        if len(checkpoints) == job.num_checkpoints_total:
            await self.channel.logs_topic().send(
                LogMessage(
                    job_id=job_id,
                    message_type="all_checkpoints_processed",
                )
            )

    def _get_group_name(self):
        return "save-result-checkpoint-to-db"
