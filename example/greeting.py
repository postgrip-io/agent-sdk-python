"""End-to-end runnable example for the PostGrip Agent Python SDK.

Running it locally submits a workflow.runtime task to an existing agent pool.
When the host agent launches the runtime, it registers one activity
(``live_greet``) and one workflow class (``GreetingWorkflow``) with delegated
agent credentials.

Run::

    export POSTGRIP_AGENT_LIVE_SERVER_URL=https://postgrip.app
    export POSTGRIP_AGENT_AUTH_TOKEN=...           # management-side bearer
    export SDK_EXAMPLE_RUNTIME_ARGS_JSON='["-lc","python -m example.greeting"]'
    python -m example.greeting

The SDK does not enroll standalone agents; host agents inject delegated
managed-runtime credentials.
"""

from __future__ import annotations

import asyncio
import json
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
    if os.environ.get("POSTGRIP_AGENT_MANAGED_RUNTIME") != "true":
        await submit_managed_runtime()
        return

    address = os.environ.get("POSTGRIP_AGENTORCHESTRATOR_URL") or os.environ.get("POSTGRIP_AGENT_LIVE_SERVER_URL") or "https://agentorchestrator.postgrip.app"
    auth_token = os.environ.get("POSTGRIP_AGENT_AUTH_TOKEN", "")
    tenant_id = os.environ.get("POSTGRIP_AGENT_TENANT_ID", "")
    queue = os.environ.get("POSTGRIP_AGENT_TASK_QUEUE", "python-example")
    agent_id = os.environ.get("POSTGRIP_AGENT_ID", "python-example-agent")

    headers = {}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    if tenant_id:
        headers["x-postgrip-agent-tenant-id"] = tenant_id
    client = await Client.connect(address, headers=headers)

    agent = Agent(
        client,
        identity=agent_id,
        name=agent_id,
        task_queue=queue,
        workflows=[GreetingWorkflow],
        activities=[live_greet],
        max_concurrent_tasks=4,
    )

    workflow_id = f"python-example-{uuid.uuid4()}"
    result = await agent.run_until(
        client.execute_workflow(
            GreetingWorkflow,
            os.environ.get("SDK_EXAMPLE_GREETING_NAME", "PostGrip"),
            id=workflow_id,
            task_queue=queue,
            ui={
                "displayName": "Python greeting example",
                "description": "Started from the Python SDK greeting example.",
                "details": {"sdk": "python"},
                "tags": ["sdk-ui-demo", "python"],
            },
            timeout=60,
        )
    )
    print(f"workflow {workflow_id} -> {result!r}")


async def submit_managed_runtime() -> None:
    address = os.environ.get("POSTGRIP_AGENTORCHESTRATOR_URL") or os.environ.get("POSTGRIP_AGENT_LIVE_SERVER_URL") or "https://agentorchestrator.postgrip.app"
    auth_token = os.environ.get("POSTGRIP_AGENT_AUTH_TOKEN", "")
    tenant_id = os.environ.get("POSTGRIP_AGENT_TENANT_ID", "")
    headers = {}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    if tenant_id:
        headers["x-postgrip-agent-tenant-id"] = tenant_id
    client = await Client.connect(address, headers=headers)
    args_json = os.environ.get("SDK_EXAMPLE_RUNTIME_ARGS_JSON") or os.environ.get("POSTGRIP_EXAMPLE_RUNTIME_ARGS_JSON")
    if not args_json:
        raise RuntimeError("SDK_EXAMPLE_RUNTIME_ARGS_JSON is required to submit this runtime to an agent pool")
    args = json.loads(args_json)
    if not isinstance(args, list) or any(not isinstance(item, str) for item in args):
        raise RuntimeError("SDK_EXAMPLE_RUNTIME_ARGS_JSON must be a JSON array of strings")
    queue = os.environ.get("SDK_EXAMPLE_RUNTIME_QUEUE") or os.environ.get("POSTGRIP_EXAMPLE_RUNTIME_QUEUE") or "default"
    runtime_queue = os.environ.get("SDK_EXAMPLE_RUNTIME_CHILD_QUEUE") or os.environ.get("POSTGRIP_EXAMPLE_RUNTIME_CHILD_QUEUE") or f"postgrip-greeting-{uuid.uuid4().hex[:8]}"
    task = client.task.workflow_runtime(
        queue=queue,
        runtime_queue=runtime_queue,
        image=os.environ.get("SDK_EXAMPLE_RUNTIME_IMAGE") or os.environ.get("POSTGRIP_EXAMPLE_RUNTIME_IMAGE"),
        command=os.environ.get("SDK_EXAMPLE_RUNTIME_COMMAND") or os.environ.get("POSTGRIP_EXAMPLE_RUNTIME_COMMAND") or "sh",
        args=args,
        working_dir=os.environ.get("SDK_EXAMPLE_RUNTIME_WORKING_DIR") or os.environ.get("POSTGRIP_EXAMPLE_RUNTIME_WORKING_DIR"),
        pull_policy=os.environ.get("SDK_EXAMPLE_RUNTIME_PULL_POLICY") or os.environ.get("POSTGRIP_EXAMPLE_RUNTIME_PULL_POLICY"),
        timeout_seconds=300,
        lease_timeout_seconds=30,
        env={
            "SDK_EXAMPLE_GREETING_NAME": os.environ.get("SDK_EXAMPLE_GREETING_NAME", "PostGrip"),
        },
    )
    print(f"submitted managed workflow runtime task={task['id']} queue={queue} runtime_queue={runtime_queue}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
