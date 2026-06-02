from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.contracts.graph import GraphState


def build_graph(llm_node, retrieve_node, graph_node):
    builder = StateGraph(GraphState)
    builder.add_node("retrieve", retrieve_node)
    builder.add_node("graph_enrich", graph_node)
    builder.add_node("llm", llm_node)

    builder.add_edge(START, "retrieve")
    builder.add_edge("retrieve", "graph_enrich")
    builder.add_edge("graph_enrich", "llm")
    builder.add_edge("llm", END)

    return builder.compile()
