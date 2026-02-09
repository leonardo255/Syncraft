from __future__ import annotations

from pathlib import Path
import json
import tempfile
from typing import Any, Dict

import networkx as nx
from networkx.readwrite import json_graph


_STATE_DIR = Path(__file__).resolve().parent
GRAPH_PATH = _STATE_DIR / "graph.json"


def load_graph() -> nx.DiGraph:
    """
    Load a directed graph from ``graph.json`` stored in adjacency format.
    If the file does not exist, is empty, or is temporarily corrupted,
    an empty DiGraph is returned.
    """
    if not GRAPH_PATH.exists() or GRAPH_PATH.stat().st_size == 0:
        return nx.DiGraph()

    try:
        with GRAPH_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        # If we ever catch a partially written / corrupted file, avoid
        # crashing the UI or tools and return an empty graph instead.
        return nx.DiGraph()

    graph = json_graph.node_link_graph(data)
    return graph


def load_graph_json() -> Dict[str, Any]:
    """
    Return the raw JSON structure stored in ``graph.json``.
    If the file is missing, empty, or invalid, an empty dict is returned.
    """
    if not GRAPH_PATH.exists() or GRAPH_PATH.stat().st_size == 0:
        return {}

    try:
        with GRAPH_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        return {}

    return data


def save_graph(graph: nx.DiGraph) -> None:
    """
    Persist the given directed graph to ``graph.json`` in adjacency format.

    The write is done atomically via a temporary file, so readers will
    either see the old complete file or the new complete file, never a
    half-written JSON blob.
    """
    GRAPH_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = json_graph.node_link_data(graph)

    # Use a unique temporary file per call to avoid collisions when multiple
    # tool invocations save concurrently.
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=GRAPH_PATH.parent,
        delete=False,
        suffix=".tmp",
    ) as f:
        json.dump(data, f, indent=2)
        tmp_name = f.name

    # Atomic replacement on POSIX (macOS, Linux).
    Path(tmp_name).replace(GRAPH_PATH)