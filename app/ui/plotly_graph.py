from __future__ import annotations
from typing import Any, Dict, List
import plotly.graph_objects as go
import networkx as nx

def build_graph_figure(
    graph: nx.DiGraph,
    products: List[Dict[str, Any]] | None = None,
    n_steps: int = 50,
    frame_duration_ms: int = 50,
    show_slider: bool = True,  # kept for API compatibility, currently unused
    loop: bool = True,
) -> go.Figure:
    """
    Build a Plotly figure for a graph with optional animated products.

    Args:
        graph: ``nx.DiGraph`` with nodes having ``'pos': (x, y)``.
        products: Optional list of dicts, each with keys:
            - "route": List[str], node IDs along the path
            - "color": str, CSS color
        n_steps: Number of interpolation steps / frames for the animation.
        frame_duration_ms: Playback speed; duration of each frame in ms.
        show_slider: Whether to show a frame slider under the plot.
        loop: Whether the Play button should loop the animation.

    Returns:
        A configured ``go.Figure``.
    """
    # Node positions
    pos = {node: data["pos"] for node, data in graph.nodes(data=True)}

    # --- Base figure ---
    fig = go.Figure()

    # --- Static edges ---
    for u, v, data in graph.edges(data=True):
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        color = data.get("color", "gray")
        fig.add_trace(go.Scatter(
            x=[x0, x1],
            y=[y0, y1],
            mode="lines",
            line=dict(color=color, width=3),
            hoverinfo="skip",
            showlegend=False
        ))

    # --- Static nodes ---
    # Build hover text with node details
    node_ids = list(pos.keys())
    hover_texts = []
    for node_id in node_ids:
        node_data = graph.nodes[node_id]
        process_time_raw = node_data.get("process_time")
        capacity = node_data.get("capacity", "N/A")
        
        # Convert process_time from minutes (float) to mm:ss format
        if process_time_raw is not None:
            minutes = int(process_time_raw)
            seconds = int((process_time_raw - minutes) * 60)
            process_time = f"{minutes:02d}:{seconds:02d}"
        else:
            process_time = "N/A"
        
        hover_text = f"{node_id}<br>Process Time: {process_time}<br>Capacity: {capacity}"
        hover_texts.append(hover_text)
    
    fig.add_trace(go.Scatter(
        x=[p[0] for p in pos.values()],
        y=[p[1] for p in pos.values()],
        mode="markers+text",
        text=node_ids,
        textposition="bottom center",
        marker=dict(size=30, color="#4C78A8"),
        hoverinfo="text",
        hovertext=hover_texts,
        showlegend=False
    ))


    # --- Animation frames (moving products only) ---
    # Normalise products to a list and filter out invalid routes.
    raw_products = products or []
    valid_products = [
        p for p in raw_products
        if len(p.get("route", [])) >= 2
    ]
    if valid_products:
        # Add one scatter trace per product so frames can update them by index.
        product_trace_indices: List[int] = []
        for product in valid_products:
            route = product["route"]
            color = product.get("color", "red")
            start_node = route[0]
            x0, y0 = pos[start_node]

            fig.add_trace(
                go.Scatter(
                    x=[x0],
                    y=[y0],
                    mode="markers",
                    marker=dict(size=18, color=color),
                    hoverinfo="skip",
                    showlegend=False,
                )
            )
            product_trace_indices.append(len(fig.data) - 1)

        # Build animation frames that update only the product traces.
        frames: List[go.Frame] = []
        for step in range(n_steps + 1):
            t = step / n_steps
            frame_traces = []

            for product in valid_products:
                route = product["route"]

                seg_count = len(route) - 1
                seg_float = t * seg_count
                seg_idx = int(seg_float)
                local_t = seg_float - seg_idx
                if seg_idx >= seg_count:
                    seg_idx = seg_count - 1
                    local_t = 1.0

                src, dst = route[seg_idx], route[seg_idx + 1]
                x0, y0 = pos[src]
                x1, y1 = pos[dst]

                x = x0 * (1 - local_t) + x1 * local_t
                y = y0 * (1 - local_t) + y1 * local_t

                # Only need x/y updates; marker style can be inherited.
                frame_traces.append(go.Scatter(x=[x], y=[y]))

            frames.append(
                go.Frame(
                    data=frame_traces,
                    traces=product_trace_indices,
                    name=str(step),
                )
            )

        fig.frames = frames

        # --- Play / Loop controls inside the figure ---
        # Approximate looping by repeating the frame sequence several times.
        frame_names = [str(i) for i in range(len(frames))]
        loop_cycles = 5  # visual looping; not truly infinite
        loop_sequence = frame_names * loop_cycles
        loop_args: Dict[str, Any] = {
            "frame": {"duration": frame_duration_ms, "redraw": True},
            "fromcurrent": False,
            "transition": {"duration": 0},
            "mode": "immediate",
        }

        buttons = [
            dict(
                label="▶",
                method="animate",
                args=[loop_sequence, loop_args],
            ),
            dict(
                label="⏹",
                method="animate",
                args=[
                    [None],
                    {
                        "mode": "immediate",
                        "frame": {"duration": 0, "redraw": False},
                        "transition": {"duration": 0},
                    },
                ],
            ),
        ]

        fig.update_layout(
            updatemenus=[
                dict(
                    type="buttons",
                    showactive=False,
                    buttons=buttons,
                    font={"size": 20},
                    direction="left",
                    x=0,
                    xanchor="left",
                    y=1.08,
                    yanchor="top",
                )
            ]
        )


    # --- Layout ---
    fig.update_layout(
        height=420,
        margin=dict(l=10, r=10, t=20, b=10),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False)
    )

    return fig
