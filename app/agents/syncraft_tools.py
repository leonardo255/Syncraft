from __future__ import annotations

"""
LangChain tools for manipulating the shared graph stored in ``app/state/graph.json``.

These helpers always:
- Safely resolve the JSON path via ``state.state.GRAPH_PATH`` (robust under Streamlit)
- Load the current graph from disk
- Apply the requested mutation
- Persist the updated graph back to ``graph.json``
"""

from langchain_core.tools import tool
import networkx as nx

from app.state.graph_state import load_graph, save_graph, load_graph_json


@tool
def add_node(label: str, x: float, y: float) -> dict:
    """
    Add a node to the shared graph.

    A node represents a machine or a process in the production process and is
    visualised in the Plotly canvas.

    Args:
        label: Human-readable label (also used as the node id).
        x: X coordinate for the layout.
        y: Y coordinate for the layout.

    Returns:
        True if the node was created or updated.
    """
    print(f"Toolcall: Adding node: {label} at {x},{y}")
    graph: nx.DiGraph = load_graph()

    # Use the label as the node id, and store visual attributes expected by the UI.
    graph.add_node(
        label,
        pos=(x, y),
        label=label,
        color="#4C78A8",
    )

    save_graph(graph)
    return {"ok": True, "exists": label in load_graph().nodes}


@tool
def remove_node(label: str) -> None:
    """
    Remove a node from the simulation graph.

    Args:
        label: Node id / label to remove.
    """
    print(f"Toolcall: Removing node: {label}")
    graph: nx.DiGraph = load_graph()
    if label in graph:
        graph.remove_node(label)
        save_graph(graph)


@tool
def move_node(label: str, x_new: float, y_new: float):
    """
    Move a node to a new position, to change the layout without modifying connections.

    Args:
        label: Node id / label to move.
        x_new: New X coordinate for the layout.
        y_new: New Y coordinate for the layout.
    """
    print(f"Toolcall: Move node {label} to new pos {x_new}, {y_new}")
    graph: nx.DiGraph = load_graph()

    if graph.has_node(label):
        # Update the stored position used by the Plotly UI.
        graph.nodes[label]["pos"] = (x_new, y_new)

    save_graph(graph)



@tool
def add_edge(src: str, dst: str) -> dict:
    """
    Add a directed edge between two existing stations.

    Returns:
        {"ok": true} on success
        {"ok": false, "error": "<reason>"} otherwise
    """
    print(f"Toolcall: Add edge between: {src} - {dst}")
    graph = load_graph()

    # Check node existence
    if not graph.has_node(src):
        print("Return: Source missing")
        return {"ok": False, "error": "source_missing", "source": src}

    if not graph.has_node(dst):
        print("Return: Destination missing")
        return {"ok": False, "error": "destination_missing", "destination": dst}

    # All good, add the edge
    graph.add_edge(src, dst, label="", color="rgba(90,90,90,0.8)")
    save_graph(graph)

    return {"ok": True, "edge_exists": graph.has_edge(src,dst)}



@tool
def remove_edge(src: str, dst: str) -> None:
    """
    Remove a directed edge from the shared graph.

    Args:
        src: Source node id / label.
        dst: Destination node id / label.
    """
    print("Toolcall: Remove edge")
    graph: nx.DiGraph = load_graph()
    if graph.has_edge(src, dst):
        graph.remove_edge(src, dst)
        save_graph(graph)

@tool
def get_graph_json() -> dict:
    """
    Returns the raw adjacency JSON data respresenting the current graph.

    This is the exact structure produced by ``networkx.json_graph.adjacency_data``.
    """
    print("Toolcall: Get graph json")
    graph_json = load_graph_json()
    return graph_json


@tool
def reset_graph() -> None:
    """
    Reset the shared graph to an empty directed graph.
    """
    print("Toolcall: Reset graph")
    graph = nx.DiGraph()
    save_graph(graph)