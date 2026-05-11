# Quick start

Two examples: enqueueing a task as a client, and running an agent that registers a workflow + activity.

## Enqueue a task

A program that just hands work to the runtime service needs only the `Client`.

```python
import asyncio
import os
from postgrip_agent import Client


async def main() -> None:
    client = await Client.connect(
        "http://127.0.0.1:4100",
        headers={"Authorization": f"Bearer {os.environ['POSTGRIP_AGENT_AUTH_TOKEN']}"},
    )

    # shell.exec — runs whatever's on the agent's PATH.
    task = await client.task.shell_exec(
        command="echo",
        args=["hello from agent"],
        queue="default",
    )
    print("enqueued", task.id)

    # container.exec — runs in a per-task container. Polyglot without
    # bloating the agent image.
    await client.task.container_exec(
        image="node:22-alpine",
        command="node",
        args=["-e", "console.log('hi from node')"],
        queue="default",
        pull_policy="missing",
        timeout_seconds=60,
    )


asyncio.run(main())
```

!!! note
    `container.exec` requires the agent process to have `DOCKER_HOST` set so the container runs through the worker stack's docker socket proxy. Containers run with `--rm --network=none`, no host volume mounts, and the same env-key allowlist as `shell.exec`.

## Wait for a result

`client.task.result(task_id)` blocks until the task reaches a terminal state and decodes the result value:

```python
result = await client.task.result(task.id)
print("result:", result)
```

Pass an `asyncio` deadline (e.g. via `asyncio.wait_for`) if you want to cap how long you wait.

## Run an agent

Agents register workflow and activity functions, then poll the runtime service for tasks.

```python
import asyncio
import os
from datetime import timedelta

from postgrip_agent import Client, Agent, activity, workflow


# Activities are plain async functions. Use any standard Python; the
# agent passes a per-task contextvar so activity.heartbeat / milestone
# / stdout / stderr / info work from inside the function body.
@activity.defn
async def greet(name: str) -> str:
    await activity.milestone("greeting", index=1, total=1)
    return f"Hello, {name}"


# Workflows are classes with @workflow.run as the entrypoint coroutine.
# Inside the body, use workflow.execute_activity, workflow.sleep,
# workflow.execute_child for durable operations.
@workflow.defn(name="SayHelloWorkflow")
class SayHelloWorkflow:
    @workflow.run
    async def run(self, name: str) -> str:
        return await workflow.execute_activity(
            greet,
            name,
            schedule_to_close_timeout=timedelta(seconds=10),
        )


async def main() -> None:
    client = await Client.connect(
        "http://127.0.0.1:4100",
        headers={"Authorization": f"Bearer {os.environ['POSTGRIP_AGENT_AUTH_TOKEN']}"},
    )

    agent = Agent(
        client,
        task_queue="default",
        workflows=[SayHelloWorkflow],
        activities=[greet],
    )

    # run_until pairs starting an agent with awaiting a workflow handle —
    # convenient for scripts. For long-lived workers, use agent.run() and
    # wire your own shutdown signaling.
    handle = await client.execute_workflow(
        SayHelloWorkflow,
        "PostGrip",
        id="say-hello",
        task_queue="default",
    )
    result = await agent.run_until(handle)
    print(result)


asyncio.run(main())
```

The agent loops forever (or until cancelled), leasing tasks from the configured queue, heartbeating each leased task, and dispatching to your registered functions. Concurrency is bounded by `max_concurrent_tasks` (default 4).

## Start a workflow from elsewhere

From the client side, start the workflow you registered above and wait for its result:

```python
handle = await client.execute_workflow(
    SayHelloWorkflow,
    "world",
    id="say-hello-2",
    task_queue="default",
)

result: str = await handle.result()
print(result)  # Hello, world
```

`execute_workflow` returns a `WorkflowHandle` — use it to wait, signal, query, update, cancel, terminate, or read history.

## Streaming events

Tasks emit ordered events (started / heartbeat / milestone / progress / stdout / stderr / completed / failed). To stream them as they land:

```python
async for event in handle.watch_events():
    print(event.kind, event.message)
```

The async generator closes when the task reaches a terminal state.

## Where to next

- [Workflow runtime](workflow-runtime.md) — the durable replay model: how `execute_activity` / `sleep` work under the hood, what determinism means, the sandbox, signals and queries, ContinueAsNew.
- [API](api.md) — the public surface re-exported from `postgrip_agent`.
