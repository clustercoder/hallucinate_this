# NYU CTF Agents — Setup and Run Guide

This document walks you from zero to running experiments for both the multi‑agent D‑CIPHER system and the single‑agent baseline. It also covers the new LangGraph orchestration path.

## 1) Prerequisites

- macOS, Linux, or WSL2 (Docker Desktop installed and running)
- Python 3.10+ recommended
- Disk space: ~10GB for Docker images + dataset
- A shell (zsh/bash)

Optional but recommended:
- A Python virtual environment (venv or conda)

## 2) Quickstart (TL;DR)

```bash
# Clone
git clone https://github.com/NYU-LLM-CTF/llm_ctf_automation
cd llm_ctf_automation

# Multi-agent setup (Docker image + editable install)
./setup_dcipher.sh

# Download dataset
python3 -m nyuctf.download

# Run multi-agent (planner+executor)
python3 run_dcipher.py --split development --challenge <challenge-name> \
  --config configs/dcipher/<category>_planner_executor.yaml

# (Optional) Run with LangGraph orchestration
python3 run_dcipher.py --split development --challenge <challenge-name> \
  --config configs/dcipher/<category>_planner_executor.yaml --use-langgraph
```

See sections below for baseline agent, API keys, logging, and troubleshooting.

## 3) Create and activate a virtualenv (optional)

```bash
# Create venv (macOS/Linux)
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
python3 -m pip install --upgrade pip
```

To leave the venv later:
```bash
deactivate
```

## 4) Install and build

Pick ONE of the following depending on which system you want to run first.

- D‑CIPHER (multi‑agent):
```bash
./setup_dcipher.sh
```
This will:
- Ensure Docker network `ctfnet` exists
- Build Docker image `ctfenv:multiagent`
- Install this package in editable mode (`pip install -e .`)

- Baseline (single‑agent):
```bash
./setup_baseline.sh
```
This will:
- Ensure Docker network `ctfnet` exists
- Build Docker image `ctfenv`
- Download Ghidra for baseline reversing tools
- Install dependencies from `requirements.txt`

## 5) Download the dataset

```bash
python3 -m nyuctf.download
```
This fetches the NYU CTF dataset to the default location used by entrypoints.

## 6) Configure API keys (models)

Set the environment variables for the backends you plan to use. Examples:

```bash
# Pick what you need
export OPENAI_API_KEY=...
export ANTHROPIC_API_KEY=...
export TOGETHER_API_KEY=...
export GOOGLE_API_KEY=...
```

The multi‑agent system also supports keys supplied via CLI or config; see `nyuctf_multiagent/utils.py` and your selected config file in `configs/dcipher/` for model names.

## 7) Run experiments

- Multi‑agent (planner+executor):
```bash
python3 run_dcipher.py --split development --challenge <challenge-name> \
  --config configs/dcipher/<category>_planner_executor.yaml
```

- Multi‑agent (single executor ablation):
```bash
python3 run_single_executor.py --split development --challenge <challenge-name>
```

- Baseline (single‑agent):
```bash
python3 run_baseline.py -c configs/baseline/base_config.yaml \
  --split development --challenge <challenge-name>
```

### Useful flags
- `--enable-autoprompt` to generate an initial prompt automatically
- `--strict` (Together backend) for strict function calling
- Container controls:
  - `--container-image ctfenv:multiagent` (multi‑agent default)
  - `--container-image ctfenv` (baseline default)
  - `--container-network ctfnet` (default network created by setup scripts)

## 8) LangGraph orchestration (optional)

Use the new StateGraph pipeline (planner → router → memory → retrieval → tools → executor → verifier):

```bash
python3 run_dcipher.py --split development --challenge <challenge-name> \
  --config configs/dcipher/<category>_planner_executor.yaml --use-langgraph
```

Synthetic demo (no Docker or tools):
```bash
python3 scripts/langgraph_demo.py
```

Notes:
- When `--use-langgraph` is set, the script constructs the graph and starts the challenge container.
- The graph will run a real `ExecutorAgent` when `environment`, `challenge`, `executor_backend`, and `executor_prompter` are available; otherwise it returns a synthetic summary.
- Extend nodes in `nyuctf_multiagent/langgraph_agent.py` (e.g., improve retrieval and verification).

## 9) Logs and outputs

- Multi‑agent logs: `logs_dcipher/<your-username>/<challenge>.json`
- Baseline logs: `logs_baseline/<your-username>/<challenge>.json`
- With `--use-langgraph`, the log will include a `langgraph_result` object (final state snapshot).

## 10) Troubleshooting

- Docker network missing or wrong image:
  - Re‑run `./setup_dcipher.sh` or `./setup_baseline.sh`
  - Pass explicit flags: `--container-image ctfenv:multiagent` and `--container-network ctfnet`
  - Check with `docker network ls` and remove stale containers

- Dataset not found: run `python3 -m nyuctf.download`

- Model auth errors: verify environment vars (e.g., `OPENAI_API_KEY`) and that your chosen model matches the MODELS registry in `nyuctf_multiagent/backends/`.

- Baseline Ghidra issues: re‑run `./setup_baseline.sh` to re‑download.

- Quick integrity check (no Docker):
```bash
python3 scripts/smoke_test.py
```

## 11) Developer notes

- Editable install: the multi‑agent package is installed via `pip install -e .` in `setup_dcipher.sh`.
- Dependencies:
  - `requirements.txt` (runtime) and `pyproject.toml` (package deps). `langgraph` is included in both.
- Key code paths:
  - Entry points: `run_dcipher.py`, `run_single_executor.py`, `run_baseline.py`
  - Configs: `configs/dcipher/*_planner_executor.yaml`, `configs/single_executor/*_single_executor.yaml`
  - Multi‑agent: `nyuctf_multiagent/`
  - Baseline: `nyuctf_baseline/`
- CI: a lightweight smoke test runs via `.github/workflows/smoke.yml`.

## 12) Clean up

```bash
# Deactivate venv
deactivate 2>/dev/null || true

# Remove Docker containers/images as needed (examples)
docker ps -a
# docker rm -f <container-id>
# docker rmi ctfenv:multiagent ctfenv
```

## 13) Appendix — Common flag reference

- Dataset selection: `--split development|test` (default: development)
- Config override: `--config <path-to-yaml>` (multi‑agent)
- Autoprompter: `--enable-autoprompt`
- Function calling strictness: `--strict` (Together backend)
- Logging directory: `--logdir` (see `run_dcipher.py`)
- Containers: `--container-image`, `--container-network`
- LangGraph: `--use-langgraph`
