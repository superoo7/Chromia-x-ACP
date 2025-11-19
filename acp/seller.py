import logging
import threading
from typing import Optional

from dotenv import load_dotenv

from virtuals_acp.memo import ACPMemo
from virtuals_acp.client import VirtualsACP
from virtuals_acp.job import ACPJob
from virtuals_acp.models import ACPJobPhase
from virtuals_acp.contract_clients.contract_client_v2 import ACPContractClientV2
import pathlib
import os
import asyncio
import json

from db import Database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("SellerAgent")

env_path = pathlib.Path(__file__).parent.parent / ".env.local"
load_dotenv(dotenv_path=env_path, override=True)

REJECT_JOB = False

class EnvSettings:
    SELLER_WALLET_PRIVATE_KEY = os.getenv("SELLER_WALLET_PRIVATE_KEY")
    SELLER_AGENT_WALLET_ADDRESS = os.getenv("SELLER_AGENT_WALLET_ADDRESS")
    SELLER_ENTITY_ID = int(os.getenv("SELLER_ENTITY_ID"))


def seller():

    db = Database()
    env = EnvSettings()

    # Top-level sync handler to wrap coroutine on_new_task and ensure it is awaited
    def on_new_task(job: ACPJob, memo_to_sign: Optional[ACPMemo] = None):
        # Bridge awaitable coroutine with event loop using asyncio.run for standalone runs, or ensure_future for running loop
        async def async_inner():
            logger.info(
                f"[on_new_task] Received job {job.id} (phase: {job.phase})"
            )
            logger.info(f"{job}")

            if (
                job.phase == ACPJobPhase.REQUEST
                and memo_to_sign is not None
                and memo_to_sign.next_phase == ACPJobPhase.NEGOTIATION
            ):
                response = True
                logger.info(
                    f"Responding to job {job.id} with requirement: {job.requirement}"
                )
                if response:
                    job.accept("Job requirement matches agent capability")
                    job.create_requirement(
                        f"Job {job.id} accepted, please make payment to proceed"
                    )
                else:
                    job.reject("Job requirement does not meet agent capability")
                logger.info(f"Job {job.id} responded with {response}")

            elif (
                job.phase == ACPJobPhase.TRANSACTION
                and memo_to_sign is not None
                and memo_to_sign.next_phase == ACPJobPhase.EVALUATION
            ):
                # to cater cases where agent decide to reject job after payment has been made
                if REJECT_JOB:  # conditional check for job rejection logic
                    reason = "Job requirement does not meet agent capability"
                    logger.info(f"Rejecting job {job.id} with reason: {reason}")
                    job.reject(reason)
                    logger.info(f"Job {job.id} rejected")
                    return

                # TODO: change response_data to your services
                response_data = "This is a test response"

                deliverable = {
                    "response": response_data,
                    "is_success": True,
                }

                logger.info(
                    f"Delivering job {job.id} with deliverable {deliverable}")
                job.deliver(deliverable)

                await db.create_job(
                    str(job.id),
                    job.client_address,
                    json.dumps(deliverable)
                )

                logger.info(f"Job {job.id} delivered")
                return

            elif job.phase == ACPJobPhase.COMPLETED:
                logger.info(f"Job {job.id} completed")
                await db.update_job_status(str(job.id), "COMPLETED")

            elif job.phase == ACPJobPhase.REJECTED:
                logger.info(f"Job {job.id} rejected")
                await db.update_job_status(str(job.id), "REJECTED")

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(async_inner())
        else:
            # If a running loop exists, schedule coroutine execution
            asyncio.ensure_future(async_inner())

    VirtualsACP(
        acp_contract_clients=ACPContractClientV2(
            wallet_private_key=env.SELLER_WALLET_PRIVATE_KEY,
            agent_wallet_address=env.SELLER_AGENT_WALLET_ADDRESS,
            entity_id=env.SELLER_ENTITY_ID
        ),
        on_new_task=on_new_task
    )

    logger.info("Seller agent is running, waiting for new tasks...")
    asyncio.run(db.init())
    logger.info("===Database initialized===")
    threading.Event().wait()


if __name__ == "__main__":
    seller()
