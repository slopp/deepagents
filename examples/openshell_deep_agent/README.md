# OpenShell Deep Agent

General-purpose coding and analysis agent using **OpenShell as the on-prem sandbox provider**. The agent writes and executes code inside a policy-governed OpenShell sandbox, with local filesystem persistence for memory and skills.

## Architecture

```
create_deep_agent (frontier model)
    |
    |-- backend: OpenShellBackend
    |       Agent writes scripts via write_file, runs them via execute tool
    |       OpenShell sandbox provides: isolated Linux env, policy-governed network
    |
    |-- memory/
    |       AGENTS.md    Persistent agent instructions (self-improving)
    |
    |-- skills/
            (add your own SKILL.md files here)
```

**How sandbox execution works:** The agent uses `write_file` to create scripts in `/workspace/`, then the `execute` tool runs them inside the OpenShell sandbox via `SandboxSession.exec()`. File reads/writes/edits all go through the same channel — `BaseSandbox` translates them into shell commands automatically.

**vs. Modal:** Drop-in replacement. Swap `ModalBackend` → `OpenShellBackend`. The rest of the deepagents stack (memory, skills, subagents) is unchanged. OpenShell runs on-prem; no cloud dependency.

## Prerequisites

- [OpenShell](https://github.com/nvidia/OpenShell) installed (`cargo install --path OpenShell/crates/navigator-cli`)
- Docker running (required for the local k3s gateway)
- `uv` installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)

## Quickstart

### Step 1 — Install dependencies

```bash
cd openshell_deep_agent
uv sync
# Install openshell Python SDK from the repo:
uv pip install -e /path/to/OpenShell/python
```

### Step 2 — Start an OpenShell gateway

```bash
openshell gateway start
```

This provisions a local k3s cluster in Docker and sets it as the active gateway. Verify it's up:

```bash
openshell status
```

### Step 3 — Configure environment

```bash
cp .env.example .env
# Edit .env and set at minimum:
#   AGENT_MODEL=anthropic:claude-sonnet-4-6
#   ANTHROPIC_API_KEY=sk-ant-...
```

### Step 4 — Run the agent

```bash
uv run langgraph dev --allow-blocking
```

Open LangSmith Studio and try:

```
Write a Python script that generates 500 random numbers, computes basic statistics
(mean, median, std dev, min, max), and prints a summary.
```

The agent will write the script to `/workspace/stats.py` in the sandbox and execute it.

---

## Sandbox Modes

### Mode A — Fresh sandbox per run (default)

The backend creates a new sandbox on every agent invocation and leaves it running. Clean up manually:

```bash
openshell sandbox list
openshell sandbox delete <name>
```

No extra configuration needed — just run the agent.

### Mode B — Persistent named sandbox

Pre-create a sandbox and reuse it across runs. Useful for testing (faster startup, preserved state):

```bash
# Create once
openshell sandbox create --name my-agent --keep

# Point the agent at it
export OPENSHELL_SANDBOX_NAME=my-agent

# Run
uv run langgraph dev --allow-blocking

# Clean up when done
openshell sandbox delete my-agent
```

---

## Testing It

### Manual smoke test

Start the agent and send this prompt:

```
Run `uname -a` and `python3 --version` in the sandbox and tell me what you see.
```

Expected: the agent calls `execute("uname -a && python3 --version")` and returns the sandbox's OS and Python version.

### Verify sandbox isolation

```
Try to curl https://example.com and tell me what happens.
```

Expected: the request is blocked or succeeds depending on the active sandbox policy. Use `openshell policy get <sandbox-name>` to inspect the policy and `openshell logs <sandbox-name> --tail` to watch deny events in real time.

### File roundtrip test

```
Write a file /workspace/hello.txt containing "hello from OpenShell", then read it back.
```

Expected: agent uses `write_file` → `read_file`, content is returned correctly.

### Python execution test

```
Write and run a Python script that:
1. Creates a list of 10 squares (1² through 10²)
2. Prints their sum
3. Saves the list to /workspace/squares.json
Then read the JSON file back.
```

Expected: agent writes `/workspace/squares.json` via `write_file`, executes the script, then reads the file. Sum should be 385.

---

## Watching the sandbox

In a second terminal, stream live logs from the sandbox while the agent runs:

```bash
openshell logs <sandbox-name> --tail --source sandbox
```

To find the sandbox name:

```bash
openshell sandbox list
```

---

## Policy Iteration

The agent's network access is controlled by the sandbox policy. To allow or restrict access:

```bash
# View current policy
openshell policy get <sandbox-name> --full > policy.yaml

# Edit policy.yaml to allow/deny endpoints

# Push updated policy (hot-reloads without restarting the sandbox)
openshell policy set <sandbox-name> --policy policy.yaml --wait
```

See the `generate-sandbox-policy` skill in the OpenShell repo for policy authoring guidance.

---

## Adding Skills

Skills teach the agent reusable patterns (API usage, code templates, known limitations):

```
skills/
  my-skill/
    SKILL.md
```

Reference them in `src/agent.py`:

```python
agent = create_deep_agent(
    ...
    skills=["/skills/"],
)
```

## Model Configuration

The agent uses **NVIDIA Nemotron Super 3** (`nvidia/nemotron-3-super-120b-a12b`) via
NVIDIA NIM — an OpenAI-compatible endpoint at `https://integrate.api.nvidia.com/v1`.

Set your key in `.env`:

```bash
NVIDIA_API_KEY=nvapi-...
```

Get a key at [integrate.api.nvidia.com](https://integrate.api.nvidia.com).

## Adding Subagents

To add a researcher subagent (e.g. for web search tasks), see the `nvidia_deep_agent` example for the pattern. The OpenShell backend is orthogonal to the subagent configuration — subagents share the same sandbox backend by default.

## Resources

- [OpenShell repo](https://github.com/nvidia/OpenShell)
- [deepagents documentation](https://docs.langchain.com/oss/python/deepagents/overview)
- [The Two Patterns for Agent Sandboxes](https://blog.langchain.com/the-two-patterns-by-which-agents-connect-sandboxes/)
