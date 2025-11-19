import AcpClient, {
  AcpJob,
  AcpMemo,
  AcpAgentSort,
  AcpContractClientV2,
  AcpGraduationStatus,
  AcpJobPhases,
  AcpOnlineStatus,
  type DeliverablePayload,
} from "@virtuals-protocol/acp-node";

import dotenv from "dotenv";
dotenv.config({ path: ".env.local" });

const SELLER_WALLET_PRIVATE_KEY = process.env
  .SELLER_WALLET_PRIVATE_KEY as `0x${string}`;
const SELLER_ENTITY_ID = parseInt(process.env.SELLER_ENTITY_ID!);
const SELLER_AGENT_WALLET_ADDRESS = process.env
  .SELLER_AGENT_WALLET_ADDRESS as `0x${string}`;

console.log("Starting ACP client with SELLER_ENTITY_ID", SELLER_ENTITY_ID);

const REJECT_JOB = false;

async function seller() {
  const acpClient = new AcpClient({
    acpContractClient: await AcpContractClientV2.build(
      SELLER_WALLET_PRIVATE_KEY!,
      SELLER_ENTITY_ID!,
      SELLER_AGENT_WALLET_ADDRESS!
    ),
    onNewTask: async (job: AcpJob, memoToSign?: AcpMemo) => {
      if (
        job.phase === AcpJobPhases.REQUEST &&
        memoToSign?.nextPhase === AcpJobPhases.NEGOTIATION
      ) {
        // 1. Respond to the job request
        const response = true;
        console.log(
          `Responding to job ${job.id} with requirement`,
          job.requirement
        );
        if (response) {
          await job.accept("Job requirement matches agent capability");
          await job.createRequirement(
            `Job ${job.id} accepted, please make payment to proceed`
          );
        } else {
          await job.reject("Job requirement does not meet agent capability");
        }
        console.log(`Job ${job.id} responded with ${response}`);
      } else if (
        job.phase === AcpJobPhases.TRANSACTION &&
        memoToSign?.nextPhase === AcpJobPhases.EVALUATION
      ) {
        // 2. Deliver the job
        // to cater cases where agent decide to reject job after payment has been made
        if (REJECT_JOB) {
          // conditional check for job rejection logic
          const reason = "Job requirement does not meet agent capability";
          console.log(`Rejecting job ${job.id} with reason: ${reason}`);
          await job.reject(reason);
          console.log(`Job ${job.id} rejected`);
          return;
        }

        const deliverable: DeliverablePayload = {
          response: "example",
          is_success: true,
        };
        console.log(`Delivering job ${job.id} with deliverable`, deliverable);
        await job.deliver(deliverable);
        console.log(`Job ${job.id} delivered`);
      }
    },
  });
}

seller();
