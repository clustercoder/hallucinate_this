"""langgraph-based agent wrapper for nyu-ctf multiagent.

this module builds a simple stategraph to sequence planning, retrieval, memory,
tool selection, execution and verification. nodes are intentionally lightweight
with clear spots to integrate deeper logic.

note: langgraph is optional; if missing, the builder raises an informative error.
"""
from typing import TypedDict, List, Optional, Dict, Any

try:
    from langgraph.graph import StateGraph, END
except Exception as e:  # pragma: no cover - informative runtime error
    StateGraph = None  # type: ignore
    END = None  # type: ignore

from .memory_store import MemoryStore
from .retrieval_helpers import retrieve_with_self_rag
from .tool_governor import choose_tools
from .verifier import verify_output
from nyuctf_multiagent import logging as _logging
from .agent import ExecutorAgent

logger = getattr(_logging, "logger", None)


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


_mem = MemoryStore()


def planner_node(state: CTFState) -> CTFState:
    text = state.get("task_text", "").lower()
    if "crypto" in text:
        state["category"] = "crypto"
    elif "pwn" in text or "overflow" in text:
        state["category"] = "pwn"
    elif "web" in text or "sql" in text:
        state["category"] = "web"
    elif "elf" in text or "asm" in text:
        state["category"] = "rev"
    else:
        state["category"] = "misc"
    # basic heuristic: retrieval for anything non-trivial
    state["needs_retrieval"] = True
    if logger:
        logger.print(f"[langgraph] planner -> category={state['category']}")
    return state


def retrieval_router_node(state: CTFState) -> CTFState:
    text = state.get("task_text", "").lower()
    if "overflow" in text or "rop" in text:
        state["retrieval_source"] = "payloads"
    elif "aes" in text or "rc4" in text:
        state["retrieval_source"] = "writeups"
    elif "elf" in text or "asm" in text:
        state["retrieval_source"] = "graph"
    else:
        state["retrieval_source"] = "mixed"
    if logger:
        logger.print(f"[langgraph] router -> source={state['retrieval_source']}")
    return state


def memory_node(state: CTFState) -> CTFState:
    sig_src = state.get("task_text", "")
    seeds = _mem.get(sig_src)
    state["seed_queries"] = seeds
    if logger:
        logger.print(f"[langgraph] memory -> seeds={seeds}")
    return state


def retrieval_node(state: CTFState) -> CTFState:
    task = state.get("task_text", "")
    src = state.get("retrieval_source", "mixed")
    seeds = state.get("seed_queries", [])
    hint, q, ok = retrieve_with_self_rag(task, src, seeds)
    state["hint_text"] = hint
    state["last_query_used"] = q
    state["retrieval_success"] = ok
    if ok and q:
        _mem.add_success(task, q)
    if logger:
        logger.print(f"[langgraph] retrieval -> ok={ok} q={q}")
    return state


def tool_governor_node(state: CTFState) -> CTFState:
    cat = state.get("category", "misc")
    hint = state.get("hint_text", "") or ""
    tools = choose_tools(cat, hint)
    state["selected_tools"] = tools
    if logger:
        logger.print(f"[langgraph] tools -> selected={tools}")
    return state


def executor_node(state: CTFState) -> CTFState:
    hint = state.get("hint_text", "") or ""
    tools = state.get("selected_tools", [])
    # if an environment and executor backend/prompter are supplied, run a real executor
    env = state.get("environment")
    challenge = state.get("challenge")
    executor_prompter = state.get("executor_prompter")
    executor_backend = state.get("executor_backend")
    max_rounds = state.get("executor_max_rounds", 10)
    if env is not None and challenge is not None and executor_prompter is not None and executor_backend is not None:
    # create an executor agent and run it similarly to plannerexecutorsystem.run_executor
        try:
            executor = ExecutorAgent(env, challenge, executor_prompter, executor_backend, max_rounds=max_rounds)
            # add executor prompts
            task_description = state.get("task_text", "")
            executor.add_system_message(executor.prompter.get("system"))
            executor.add_user_message(executor.prompter.get("initial", task_description=task_description))

            # run executor loop (bounded)
            while not env.solved and not executor.finished and executor.conversation.round <= executor.max_rounds:
                executor.conversation.next_round()
                executor.run_one_round()

            if not env.solved and executor.finish_summary is None:
                executor.run_for_finish_summary()

            if executor.finished and executor.finish_summary is not None:
                summary = executor.finish_summary
            elif executor.error is not None:
                summary = executor.prompter.get("finish_error", error=executor.error)
            else:
                summary = executor.prompter.get("finish_empty")

            state["executor_summary"] = summary
            state["solved"] = env.solved
            if logger:
                logger.print(f"[langgraph] executor -> real executor finished solved={env.solved}")
            return state
        except Exception as e:
            # fallback to synthetic summary on error
            if logger:
                logger.print(f"[langgraph] executor -> real executor failed: {e}", style="red")

    # fallback synthetic executor summary
    summary = f"Executor simulated run. Used tools={tools}. Hint excerpt: {hint[:140]}"
    state["executor_summary"] = summary
    state["solved"] = False
    if logger:
        logger.print(f"[langgraph] executor -> summary(len)={len(summary)}")
    return state


def verifier_node(state: CTFState) -> CTFState:
    hint = state.get("hint_text", "") or ""
    result = state.get("executor_summary", "") or ""
    ok, score = verify_output(hint, result)
    state["needs_retry"] = not ok
    state["verify_score"] = score
    if logger:
        logger.print(f"[langgraph] verifier -> ok={ok} score={score:.3f}")
    return state


def build_ctf_agent_graph() -> Any:
    """build and compile the stategraph for ctf tasks.

    raises an importerror if `langgraph` is not installed.
    """
    if StateGraph is None:
        raise ImportError(
            "langgraph is required to build the CTF agent graph."
            " Install with `pip install langgraph` or run without the LangGraph agent."
        )

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


if __name__ == "__main__":
    # quick demo when run directly (will raise if langgraph missing)
    try:
        graph = build_ctf_agent_graph()
    except ImportError as e:
        print(e)
    else:
        state = {"task_text": "exploit buffer overflow in challenge xyz"}
        out = graph.invoke(state)
        print("Graph result:", out)
