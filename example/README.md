# example/

Runnable examples that exercise the PostGrip Agent Python SDK end-to-end
against a live runtime service.

## greeting

A single-process demo: it starts an Agent that registers one activity and one
workflow class, then enqueues a workflow execution from the same process and
waits for the result.

```sh
pip install -e .

export POSTGRIP_AGENT_LIVE_SERVER_URL=https://postgrip.app
export POSTGRIP_AGENT_AUTH_TOKEN=...           # management-side bearer token
export POSTGRIP_AGENT_ENROLLMENT_KEY=...       # local standalone only
python -m example.greeting
```

Optional overrides:

| Variable                       | Default            |
|:-------------------------------|:-------------------|
| `POSTGRIP_AGENT_TASK_QUEUE`    | `python-example`   |

When a PostGrip host agent launches the example as a `workflow.runtime` task,
it injects delegated session credentials. `POSTGRIP_AGENT_ENROLLMENT_KEY` is
only for local standalone runs where no host agent is supervising the runtime.
