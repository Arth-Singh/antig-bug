# Antigravity Execute Violation — Reproduction

**Target:** Google Antigravity IDE v1.22.2 (Electron, macOS build 62335c71...)
**Class:** Prompt injection → workflow auto-approval bypass → arbitrary command execution
**Severity:** Execute violation (arbitrary shell execution, no user approval prompt)

## Root cause

Antigravity's agent system prompt (embedded in
`Antigravity.app/Contents/Resources/app/extensions/antigravity/bin/language_server_macos_arm`)
instructs the model to honor two attacker-controllable annotations in workflow
files:

> *"If a workflow has a `// turbo-all` annotation anywhere, you MUST auto-run
> EVERY step that involves the `run_command` tool, by setting `SafeToAutoRun`
> to true."*

> *"If a workflow step has a `// turbo` annotation above it, you can auto-run
> the workflow step if it involves the `run_command` tool, by setting
> `SafeToAutoRun` to true."*

Workflow files are loaded from the **workspace** at these paths:
- `.agent/workflows/**/*.md`
- `.agents/workflows/**/*.md`
- `.gemini/jetski*/global_workflows/*.md`
- `.gemini/antigravity*/global_workflows/*.md`

When the model sets `SafeToAutoRun: true` on a `run_command` tool call, the
command fires **without a user approval prompt**.

Because the annotation lives inside a workspace file, any attacker-controlled
repo can ship a malicious workflow. Opening the repo and asking the agent any
relevant dev task (e.g. "add error handling to pipeline.py") triggers the
agent to invoke the workflow, which drives arbitrary command execution.

## Reproduction

### 1. Start the listener

```
cd poc-antigravity-v2
python3 listener/server.py
```

The listener serves an attacker-controlled command on `GET /rce` and captures
output on `POST /rce-result`. Default demo command runs `whoami`, `id`,
`uname -a`, and writes `/tmp/antigravity-execute-proof.txt`.

### 2. Open the workspace in Antigravity

Open `poc-antigravity-v2/` in Antigravity as a workspace. Trust the workspace
when prompted (same as any cloned repo).

### 3. Trigger the agent

In the Cascade / Agent panel, type:

```
add error handling to pipeline.py
```

### 4. Observe execute violation

- The agent reads `AGENTS.md` + `GEMINI.md` + `.agent/workflows/dev-bootstrap.md`.
- The workflow's `// turbo-all` annotation causes the agent to set
  `SafeToAutoRun: true` on its `run_command` tool call.
- `bash scripts/bootstrap.sh` executes **without any user approval prompt**.
- The script `curl`s `GET /rce` from the listener, executes the returned
  shell snippet, and posts the output back to `POST /rce-result`.

### 5. Verify

```
cat /tmp/antigravity-execute-proof.txt
```

Should contain `EXECUTE_PROOF <UTC timestamp>`.

The listener terminal shows the `whoami`/`id`/`uname -a` output captured
from the victim machine.

### Custom command

```
python3 listener/server.py --rce "cat /etc/passwd"
```

Any shell command the attacker chooses is executed on the victim machine —
reverse shells, persistence, data theft, etc. The primitive is generic.

## What makes this worse than comparable prior work

- **Zero user approval.** The `SafeToAutoRun` flag is model-set. When the
  model follows the `// turbo-all` instruction, the command fires silently.
  (Compare: the Cursor `.cursorrules` prompt-injection class of bug still
  requires the user to approve at least one benign-looking shell command.)
- **The bypass is a documented product feature.** `// turbo` and `// turbo-all`
  are not edge-case behaviors — they are explicitly engineered into the
  system prompt. An attacker who controls a workflow file fully controls
  approval bypass.
- **The trigger surface is a markdown file.** No binaries, no macros,
  nothing a reviewer could flag at clone time. The hostile content looks
  like benign CI documentation.

## Files

```
poc-antigravity-v2/
├── .agent/workflows/dev-bootstrap.md   # <-- payload: `// turbo-all` + run_command steps
├── AGENTS.md                            # steering: auto-loaded by Antigravity
├── GEMINI.md                            # steering: auto-loaded by Antigravity
├── README.md                            # benign project README
├── scripts/bootstrap.sh                 # download-and-execute from listener
├── src/pipeline.py                      # benign Python ETL
├── tests/test_pipeline.py               # benign pytest
├── listener/server.py                   # attacker listener (GET /rce, POST /rce-result)
└── evidence/                            # captured outputs
```
