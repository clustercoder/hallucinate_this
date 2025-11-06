# 🧠 GitHub Copilot Prompt — Agentic LangGraph Integration for NYU-CTF System

You are working inside a CTF-solving multi-agent system repository structured like this:
- `nyuctf_multiagent/` (core planner/executor agents)
- `configs/dcipher/` (prompts and configs per challenge category)
- `nyuctf_baseline/` (single-agent baselines)
- `docker/multiagent/` (runtime environment)

Your goal is to **extend the multi-agent workflow with an agentic layer built using LangGraph**.  
This layer orchestrates Planner → Router → Memory → Retrieval → Tool Governor → Executor → Verifier in a stateful graph pipeline.

---

## 🎯 Objective

Create a new file:

```

nyuctf_multiagent/langgraph_agent.py

````

It should:
- Use `langgraph` to build a **StateGraph** that manages the flow between nodes.
- Each node is a self-contained function operating on a shared `CTFState` dict.
- Integrate with existing `nyuctf_multiagent` modules (e.g., backends, tools, prompts, retrieval).
- Add light agentic reasoning: memory, routing, conditional retries, and verification.

---

## 🧩 Graph Nodes Overview

| Node | Role | Input | Output |
|------|------|--------|--------|
| `planner_node` | Parse task, set category, and need for retrieval | `task_text` | `category`, `needs_retrieval` |
| `retrieval_router_node` | Decide KB type (`writeups`, `payloads`, `code`, `graph`) | `task_text`, `category` | `retrieval_source` |
| `memory_node` | Load previous query successes/failures | `task_sig` | `seed_queries` |
| `retrieval_node` | Run Self-RAG retrieval | `task_text`, `source`, `seed_queries` | `hint_text`, `last_query_used`, `retrieval_success` |
| `tool_governor_node` | Select commands/tools | `category`, `hint_text` | `selected_tools` |
| `executor_node` | Use retrieved knowledge + tools | `hint_text`, `tools` | `executor_summary`, `solved` |
| `verifier_node` | Check consistency of executor output vs hint | `executor_summary`, `hint_text` | `needs_retry` |
| `final_node` | Output result / trigger retry | - | `END` |

---

## 🧠 Graph State Definition

Use a TypedDict or dataclass for shared state:

```python
from typing import TypedDict, List, Optional

class CTFState(TypedDict, total=False):
    task_text: str
    category: str
    needs_retrieval: bool
    retrieval_source: Optional[str]
    seed_queries: List[str]
    hint_text: Optional[str]
    last_query_used: Optional[str]
    selected_tools: List[str]
    executor_summary: Optional[str]
    solved: bool
    needs_retry: bool
````

---

## 🧩 Example Node Skeletons

```python
from langgraph.graph import StateGraph, END

def planner_node(state: CTFState) -> CTFState:
    """Identify challenge category and whether retrieval is needed."""
    # Example heuristic
    text = state["task_text"].lower()
    if "crypto" in text: state["category"] = "crypto"
    elif "pwn" in text: state["category"] = "pwn"
    else: state["category"] = "misc"
    state["needs_retrieval"] = True
    return state

def retrieval_router_node(state: CTFState) -> CTFState:
    """Decide knowledge base source."""
    text = state["task_text"].lower()
    if "overflow" in text or "rop" in text:
        state["retrieval_source"] = "payloads"
    elif "aes" in text or "rc4" in text:
        state["retrieval_source"] = "writeups"
    elif "elf" in text or "asm" in text:
        state["retrieval_source"] = "graph"
    else:
        state["retrieval_source"] = "mixed"
    return state
```

---

## ⚙️ LangGraph Construction

```python
def build_ctf_agent_graph():
    g = StateGraph(CTFState)

    g.add_node("planner", planner_node)
    g.add_node("router", retrieval_router_node)
    g.add_node("memory", memory_node)
    g.add_node("retrieval", retrieval_node)
    g.add_node("tools", tool_governor_node)
    g.add_node("executor", executor_node)
    g.add_node("verifier", verifier_node)

    g.set_entry_point("planner")
    g.add_edge("planner", "router")
    g.add_edge("router", "memory")
    g.add_edge("memory", "retrieval")
    g.add_edge("retrieval", "tools")
    g.add_edge("tools", "executor")
    g.add_edge("executor", "verifier")

    g.add_conditional_edges(
        "verifier",
        lambda s: "retry" if s.get("needs_retry") else "done",
        {
            "retry": "retrieval",
            "done": END,
        },
    )
    return g.compile()
```

---

## 🧰 Helper Modules to Create

### 1. `nyuctf_multiagent/retrieval_helpers.py`

Handles Self-RAG or Graph-RAG retrieval.

```python
def retrieve_with_self_rag(task_text, source, seed_queries):
    """
    Perform context-aware retrieval from the correct knowledge base.
    TODO: integrate vectorstore + Graph-RAG backend.
    """
    return ("Sample retrieved hint for demo.", "query used", True)
```

---

### 2. `nyuctf_multiagent/memory_store.py`

Caches successful and failed queries for adaptive retrieval.

```python
import json, hashlib
from pathlib import Path

class MemoryStore:
    def __init__(self, path="~/.nyuctf_memory.json"):
        self.path = Path(path).expanduser()
        self.path.touch(exist_ok=True)
        self.db = json.loads(self.path.read_text() or "{}")

    def _write(self): self.path.write_text(json.dumps(self.db, indent=2))
    def sig(self, text): return hashlib.md5(text.encode()).hexdigest()[:10]

    def get(self, text): return self.db.get(self.sig(text), {}).get("success", [])
    def add_success(self, text, query):
        key = self.sig(text)
        self.db.setdefault(key, {"success": [], "fail": []})
        if query not in self.db[key]["success"]:
            self.db[key]["success"].append(query)
            self._write()
```

---

### 3. `nyuctf_multiagent/tool_governor.py`

Selects external tools to run for a task.

```python
TOOL_MAP = {
    "pwn": ["checksec", "ropper"],
    "web": ["curl -I", "sqlmap --batch"],
    "crypto": ["python3 solve.py"],
    "rev": ["ghidra_headless"],
}

def choose_tools(category, hint=""):
    return TOOL_MAP.get(category, ["strings", "file"])
```

---

### 4. `nyuctf_multiagent/verifier.py`

Ensures executor didn’t drift from retrieved hint.

```python
import difflib

def verify_output(hint, result, threshold=0.25):
    score = difflib.SequenceMatcher(None, hint, result).quick_ratio()
    return score >= threshold
```

---

## 🔗 Conditional Flow Logic

| Condition                 | Next Node                |
| ------------------------- | ------------------------ |
| `needs_retrieval=True`    | `retrieval_router_node`  |
| `retrieval_success=False` | retry retrieval          |
| `solved=True`             | `END`                    |
| `needs_retry=True`        | back to `retrieval_node` |

---

## 🧱 Integration Hook

You can now import this LangGraph agent anywhere:

```python
from nyuctf_multiagent.langgraph_agent import build_ctf_agent_graph

graph = build_ctf_agent_graph()
result = graph.invoke({"task_text": "exploit buffer overflow", "category": "pwn"})
print(result)
```

---

## 🧩 Notes for Copilot

When generating code:

* Follow **LangGraph’s StateGraph** API (`from langgraph.graph import StateGraph, END`).
* Prefer small, composable functions for nodes.
* Use clear logging (reuse `nyuctf_multiagent/logging.py` if available).
* Do not break existing planner/executor logic — the new graph should **wrap** it.
* Add TODO comments where integration with real retrieval or executors is required.
* Ensure the graph supports retries via conditional edges.

---

## ✅ Deliverables

Copilot should generate:

1. `nyuctf_multiagent/langgraph_agent.py`
2. `nyuctf_multiagent/retrieval_helpers.py`
3. `nyuctf_multiagent/memory_store.py`
4. `nyuctf_multiagent/tool_governor.py`
5. `nyuctf_multiagent/verifier.py`

and integrate LangGraph-based orchestration that enables **agentic AI reasoning, adaptive retrieval, and structured task execution**.
