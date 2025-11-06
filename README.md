# NYU CTF Automation Framework

This repository holds the LLM agents for solving CTF challenges developed for the [NYU CTF Bench](https://nyu-llm-ctf.github.io).
The agents are:

 - **D-CIPHER:** The multi-agent framework involving planner, executor, and auto-prompter agent with enhanced interactions.
 - **NYU CTF Baseline:** The baseline agent presented along with the NYU CTF Bench

The LLM agents operate in a docker environment and interact with CTF challenges to solve them.

Quick links:
- Setup guide: see `SETUP.md` for a full walkthrough (venv, Docker, dataset, API keys, commands)
- Agent instructions for AI tools: `.github/copilot-instructions.md`

## Setup and Installation

The setup requires docker to be installed on the system, please follow instructions for your OS.
The code is tested with atleast python 3.10, earlier versions may work but it is not tested.
It is recommended to create a python virtualenv or conda environment for this setup.

Follow these instructions to setup D-CIPHER or the baseline or both:

1. Clone this repository: `git clone https://github.com/NYU-LLM-CTF/llm_ctf_automation`
2. `cd llm_ctf_automation`
3. Run the setup script (will take a few minutes): `./setup_dcipher.sh` or `./setup_baseline.sh`
    1. The setup script will build the corresponding docker image, setup the docker network, and install the python dependencies
    2. You should re-run this setup if the Dockerfile or dependencies are updated
5. Download the NYU CTF dataset (will take a few minutes): `python3 -m nyuctf.download`

## Running D-CIPHER

The main D-CIPHER multi-agent system runs the planner, executor and (optionally) auto-prompter agents.
Use the following command to run it:

```
python3 run_dcipher.py --split <test|development> --challenge <challenge-name> [--enable-autoprompt]
```

To run the ablation experiment of single executor (i.e. without planner), use the following command:

```
python3 run_single_executor.py --split <test|development> --challenge <challenge-name> [--enable-autoprompt]
```

Optional: Use the new LangGraph orchestration (planner→router→memory→retrieval→tools→executor→verifier):

```
python3 run_dcipher.py --split <test|development> --challenge <challenge-name> \
    --config configs/dcipher/<category>_planner_executor.yaml --use-langgraph
```

For a synthetic demo that doesn’t require Docker/tools:

```
python3 scripts/langgraph_demo.py
```

## Running the baseline

Use the following command to run the baseline agent:

```
python3 run_baseline.py -c configs/baseline/base_config.yaml --split <test|development> --challenge <challenge-name>
```

While the baseline agent code is present in the main branch, you can access the baseline's last updated version at [v20250206](https://github.com/NYU-LLM-CTF/llm_ctf_automation/releases/tag/20250206).
This is the code used for the [NYU CTF Bench](https://nyu-llm-ctf.github.io) paper.

## Logs and troubleshooting

- Multi-agent logs: `logs_dcipher/<your-username>/<challenge>.json` (with `--use-langgraph`, contains a `langgraph_result` state)
- Baseline logs: `logs_baseline/<your-username>/<challenge>.json`
- Quick integrity check (no Docker): `python3 scripts/smoke_test.py`

