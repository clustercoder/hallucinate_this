#!/usr/bin/env python3
"""Small demo to exercise the LangGraph agent in synthetic mode.

This demo doesn't require Docker or the full environment; it uses the
placeholders implemented in `nyuctf_multiagent` and will run the graph with
a simple `task_text`.
"""
import sys
import os
# Ensure repository root is on sys.path for local imports
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from nyuctf_multiagent.langgraph_agent import build_ctf_agent_graph


def main():
    try:
        graph = build_ctf_agent_graph()
    except Exception as e:
        print("Could not build graph:", e)
        return

    state = {"task_text": "exploit a buffer overflow in a remote server"}
    out = graph.invoke(state)
    print("Graph output state:")
    print(out)


if __name__ == "__main__":
    main()
