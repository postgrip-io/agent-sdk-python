"""Long-running sequential example.

Runs five workflows back-to-back. Each workflow chains five activity calls
separated by 13-second durable timers, so a single workflow lasts ~65-75
seconds and a full run takes ~5-6 minutes. Exercises the Python SDK's
replay, suspension, and durable-timer paths under realistic timing.

Run::

    export POSTGRIP_AGENTORCHESTRATOR_URL=https://agentorchestrator.postgrip.app
    export POSTGRIP_AGENT_AUTH_TOKEN=...
    export POSTGRIP_AGENT_ENROLLMENT_KEY=...
    python -m example.longrun
"""

from __future__ import annotations

import asyncio
import os
import time
import uuid
from datetime import timedelta

from postgrip_agent import Agent, Client, activity, workflow


STEPS_PER_WORKFLOW = 5
WORKFLOW_RUNS = 5
STEP_SLEEP_SECONDS = 13


@activity.defn(name="process_step")
async def process_step(name: str, step: int) -> str:
    return f"processed step {step} for {name}"


@workflow.defn(name="LongRunningWorkflow")
class LongRunningWorkflow:
    @workflow.run
    async def run(self, name: str, steps: int) -> str:
        for i in range(1, steps + 1):
            await workflow.execute_activity(process_step, name, i)
            await workflow.sleep(timedelta(seconds=STEP_SLEEP_SECONDS))
        return f"completed {steps} steps for {name}"


async def main() -> None:
    address = (
        os.environ.get("POSTGRIP_AGENTORCHESTRATOR_URL")
        or os.environ.get("POSTGRIP_AGENT_LIVE_SERVER_URL")
        or "https://agentorchestrator.postgrip.app"
    )
    auth_token = os.environ.get("POSTGRIP_AGENT_AUTH_TOKEN", "")
    queue = os.environ.get("POSTGRIP_AGENT_TASK_QUEUE", "python-longrun")

    headers = {"Authorization": f"Bearer {auth_token}"} if auth_token else {}
    client = await Client.connect(address, headers=headers)
    agent = Agent(
        client,
        task_queue=queue,
        workflows=[LongRunningWorkflow],
        activities=[process_step],
        max_concurrent_tasks=4,
    )

    async def run_all() -> None:
        overall_start = time.monotonic()
        for i in range(1, WORKFLOW_RUNS + 1):
            run_start = time.monotonic()
            workflow_id = f"python-longrun-{uuid.uuid4()}-{i}"
            print(f"[{i}/{WORKFLOW_RUNS}] starting {workflow_id}", flush=True)
            result = await client.execute_workflow(
                LongRunningWorkflow,
                f"PostGrip-{i}",
                STEPS_PER_WORKFLOW,
                id=workflow_id,
                task_queue=queue,
                timeout=300,
            )
            print(f"[{i}/{WORKFLOW_RUNS}] {workflow_id} -> {result!r} ({int(time.monotonic() - run_start)}s)", flush=True)
        print(f"done — {WORKFLOW_RUNS} workflows in {int(time.monotonic() - overall_start)}s", flush=True)

    await agent.run_until(run_all())


if __name__ == "__main__":
    asyncio.run(main())
