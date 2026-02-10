from __future__ import annotations

"""
LangChain tools for manipulating the shared product routes stored in ``app/state/products.json``.

Each product route is represented as a simple dict:
  - ``label``: str, product route name/identifier
  - ``route``: list[str], ordered list of station / node IDs
  - ``color``: str, CSS color for visualisation

These helpers always:
  - Safely resolve the JSON path via ``app.state.product_state``
  - Load the current product routes list from disk
  - Apply the requested mutation
  - Persist the updated list back to ``products.json``
"""

from typing import Any, Dict, List

from langchain_core.tools import tool

from app.state.product_state import load_products, save_products
from app.state.graph_state import load_graph


@tool
def add_product_route(label: str, route: List[str], color: str = "red") -> Dict[str, Any]:
    """
    Add or update a product route definition.

    Args:
        label: Name / identifier of the product route.
        route: Ordered list of station / node IDs this product route flows through.
        color: CSS color used when animating this product.

    Returns:
        Dict with either:
          - {"success": True} on success, or
          - {"success": False, "error": str, "missing_nodes": [...]} if some
            stations in the route do not exist in the current graph.
    """
    print("Toolcall: add_product_route")

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
def remove_product_route(label: str) -> None:
    """
    Remove a product route from the configuration by label.
    """
    print("Toolcall: remove_product_route")
    products = load_products()
    products = [p for p in products if p.get("label") != label]
    save_products(products)


@tool
def get_product_routes() -> List[Dict[str, Any]]:
    """
    Return the full list of configured product routes.
    """
    print("Toolcall: get_product_routes")
    return load_products()


@tool
def reset_product_routes() -> None:
    """
    Reset / clear all configured product routes.
    """
    print("Toolcall: reset_product_routes")
    save_products([])