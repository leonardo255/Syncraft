from __future__ import annotations

"""
LangChain tools for manipulating the shared products stored in ``app/state/products.json``.

Each product is represented as a simple dict:
  - ``label``: str, product name/identifier
  - ``route``: list[str], ordered list of station / node IDs
  - ``color``: str, CSS color for visualisation

These helpers always:
  - Safely resolve the JSON path via ``app.state.product_state``
  - Load the current products list from disk
  - Apply the requested mutation
  - Persist the updated list back to ``products.json``
"""

from typing import Any, Dict, List

from langchain_core.tools import tool

from app.state.product_state import load_products, save_products
from app.state.graph_state import load_graph


@tool
def add_product(label: str, route: List[str], color: str = "red") -> Dict[str, Any]:
    """
    Add or update a product definition.

    Args:
        label: Name / identifier of the product.
        route: Ordered list of station / node IDs this product flows through.
        color: CSS color used when animating this product.

    Returns:
        Dict with either:
          - {"success": True} on success, or
          - {"success": False, "error": str, "missing_nodes": [...]} if some
            stations in the route do not exist in the current graph.
    """
    print("Toolcall: add_product")

    # Validate that all stations in the route exist as nodes in the graph.
    graph = load_graph()
    missing_nodes = [station for station in route if station not in graph.nodes]
    if missing_nodes:
        return {
            "success": False,
            "error": "Some stations in the product route do not exist in the simulation graph.",
            "missing_nodes": missing_nodes,
            "available_nodes": sorted(list(graph.nodes)),
        }

    products = load_products()

    # Overwrite existing product with same label, if any.
    updated = False
    for p in products:
        if p.get("label") == label:
            p["route"] = list(route)
            p["color"] = color
            updated = True
            break

    if not updated:
        products.append(
            {
                "label": label,
                "route": list(route),
                "color": color,
            }
        )

    save_products(products)
    return {"success": True}


@tool
def remove_product(label: str) -> None:
    """
    Remove a product from the configuration by label.
    """
    print("Toolcall: remove_product")
    products = load_products()
    products = [p for p in products if p.get("label") != label]
    save_products(products)


@tool
def get_products() -> List[Dict[str, Any]]:
    """
    Return the full list of configured products.
    """
    print("Toolcall: get_products")
    return load_products()


@tool
def reset_products() -> None:
    """
    Reset / clear all configured products.
    """
    print("Toolcall: reset_products")
    save_products([])

