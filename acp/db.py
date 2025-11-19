import asyncio
from postchain_client_py import BlockchainClient
from postchain_client_py.blockchain_client.types import NetworkSettings
from postchain_client_py.blockchain_client.types import Operation, Transaction
from dotenv import load_dotenv
load_dotenv(dotenv_path=".env.local")

import os
from coincurve import PrivateKey
import json

# Load private key from environment variable
private_bytes = bytes.fromhex(os.getenv("CHR_PRIV_KEY"))
private_key = PrivateKey(private_bytes)
public_key = private_key.public_key.format() 

class Database:
    def __init__(self):
        self.client = None

    async def init(self):
        settings = NetworkSettings(
            node_url_pool=["http://localhost:7740"],
            blockchain_iid=0
        )
        self.client = await BlockchainClient.create(settings)

    async def total_jobs(self):
        return await self.client.query("total_jobs")

    async def create_job(self, id: str, evm_address: str, result: dict):
        operation = Operation(
            op_name="create_job",
            args=[id, evm_address, result]
        )
        transaction = Transaction(
            operations=[operation],
            signers=[public_key],
            signatures=None,
        )
        signed_tx = await self.client.sign_transaction(transaction, private_bytes)
        receipt = await self.client.send_transaction(signed_tx, do_status_polling=True)

        return receipt

    async def get_job(self, job_id: str):
        return await self.client.query("get_job", {"job_id": job_id})

    async def get_all_jobs(self):
        return await self.client.query("get_all_jobs")

    async def update_job_status(self, job_id: str, status: str):
        if status not in ("PENDING", "COMPLETED", "REJECTED"):
            raise ValueError(f"Invalid status: {status}. Must be 'PENDING', 'COMPLETED', or 'REJECTED'.")

        status_map = {"PENDING": 0, "COMPLETED": 1, "REJECTED": 2}
        status_int = status_map[status]

        operation = Operation(
            op_name="update_job_status",
            args=[job_id, status_int]
        )
        transaction = Transaction(
            operations=[operation],
            signers=[public_key],
            signatures=None,
        )
        signed_tx = await self.client.sign_transaction(transaction, private_bytes)
        receipt = await self.client.send_transaction(signed_tx, do_status_polling=True)
        return receipt

if __name__ == "__main__":
    async def main():
        db = Database()
        await db.init()

        try:
            json_result = json.dumps({"result": "success"})
            # await db.create_job("123", "0x1234567890", json_result)
        except Exception as e:
            print(f"Error creating job: {e}")

        job = await db.get_job("1000132603")
        print(f"Job: {job}")
        # await db.update_job_status("123", "COMPLETED")
        # jobs = await db.get_all_jobs()
        # print(f"Jobs: {jobs}")

        total = await db.total_jobs()
        print(f"Total jobs: {total}")

    asyncio.run(main())