"""End-to-end runnable example for the PostGrip Agent Python SDK.

Registers one activity (``live_greet``) and one workflow class
(``GreetingWorkflow``), starts an in-process Agent that polls the runtime
service, then enqueues a workflow execution and waits for the result.

Run::

    export POSTGRIP_AGENT_LIVE_SERVER_URL=https://postgrip.app
    export POSTGRIP_AGENT_AUTH_TOKEN=...           # management-side bearer
    export POSTGRIP_AGENT_ENROLLMENT_KEY=...       # agent-side enrollment key
    python -m example.greeting

``POSTGRIP_AGENT_ENROLLMENT_KEY`` is read transparently by the Agent — the
worker exchanges it for a refreshable agent session before its first poll.
"""

from __future__ import annotations

import asyncio
import os
import uuid

from postgrip_agent import Agent, Client, activity, workflow


@activity.defn(name="live_greet")
async def live_greet(name: str) -> str:
    return f"Hello, {name}"


@workflow.defn(name="GreetingWorkflow")
class GreetingWorkflow:
    @workflow.run
    async def run(self, name: str) -> str:
        return await workflow.execute_activity(live_greet, name)


async def main() -> None:
    address = os.environ.get("POSTGRIP_AGENTORCHESTRATOR_URL") or os.environ.get("POSTGRIP_AGENT_LIVE_SERVER_URL") or "https://agentorchestrator.postgrip.app"
    auth_token = os.environ.get("POSTGRIP_AGENT_AUTH_TOKEN", "")
    queue = os.environ.get("POSTGRIP_AGENT_TASK_QUEUE", "python-example")

    headers = {"Authorization": f"Bearer {auth_token}"} if auth_token else {}
    client = await Client.connect(address, headers=headers)

    agent = Agent(
        client,
        task_queue=queue,
        workflows=[GreetingWorkflow],
        activities=[live_greet],
        max_concurrent_tasks=4,
    )

    workflow_id = f"python-example-{uuid.uuid4()}"
    result = await agent.run_until(
        client.execute_workflow(
            GreetingWorkflow,
            "PostGrip",
            id=workflow_id,
            task_queue=queue,
            timeout=60,
        )
    )
    print(f"workflow {workflow_id} -> {result!r}")


if __name__ == "__main__":
    asyncio.run(main())
