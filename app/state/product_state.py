from __future__ import annotations

from pathlib import Path
import json
import tempfile
from typing import Any, Dict, List


_STATE_DIR = Path(__file__).resolve().parent
PRODUCTS_PATH = _STATE_DIR / "products.json"


def load_products() -> List[Dict[str, Any]]:
    """
    Load the list of products from ``products.json``.

    Each product is a dict with at least:
      - ``label``: str, name/identifier of the product
      - ``route``: list[str], ordered list of station/node IDs
      - ``color``: str, CSS color used for visualisation

    If the file is missing, empty, or invalid, an empty list is returned.
    """
    if not PRODUCTS_PATH.exists() or PRODUCTS_PATH.stat().st_size == 0:
        return []

    try:
        with PRODUCTS_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        return []

    # Ensure we always return a list of dicts.
    if not isinstance(data, list):
        return []

    return data


def save_products(products: List[Dict[str, Any]]) -> None:
    """
    Persist the list of products to ``products.json``.

    The write is done atomically via a temporary file, so readers will
    either see the old complete file or the new complete file, never a
    half-written JSON blob.
    """
    PRODUCTS_PATH.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=PRODUCTS_PATH.parent,
        delete=False,
        suffix=".tmp",
    ) as f:
        json.dump(products, f, indent=2)
        tmp_name = f.name

    Path(tmp_name).replace(PRODUCTS_PATH)


def reset_products() -> None:
    """
    Clear all products by saving an empty list to ``products.json``.
    """
    save_products([])

