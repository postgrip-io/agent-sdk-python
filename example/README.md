# example/

Runnable examples that exercise the PostGrip Agent Python SDK end-to-end
against a live runtime service. Running an example locally submits a managed
`workflow.runtime` task to an existing agent pool. The SDK Agent path runs only
when a PostGrip host agent launches the example and injects delegated runtime
credentials.

## greeting

A managed-runtime demo: the local process submits the runtime command to an
agent pool, and the host-launched runtime registers one activity and one
workflow class.

```sh
pip install -e .

export POSTGRIP_AGENT_LIVE_SERVER_URL=https://postgrip.app
export POSTGRIP_AGENT_AUTH_TOKEN=...           # management-side bearer token
export SDK_EXAMPLE_RUNTIME_IMAGE=python:3.13-slim # optional; runs via host agent helper
export SDK_EXAMPLE_RUNTIME_ARGS_JSON='["-lc","python -m example.greeting"]'
python -m example.greeting
```

Optional overrides:

| Variable                       | Default            |
|:-------------------------------|:-------------------|
| `POSTGRIP_AGENT_TASK_QUEUE`    | `python-example`   |

When a PostGrip host agent launches the example as a `workflow.runtime` task,
it injects delegated session credentials. The SDK does not enroll standalone
agents.
