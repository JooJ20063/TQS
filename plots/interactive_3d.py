from __future__ import annotations

from pathlib import Path
from typing import Iterable

import math

import plotly.graph_objects as go


def generate_all_interactive_diagrams_3d(model, results: dict, output_dir: Path) -> dict:
    """
    Gera os gráficos 3D interativos em HTML.

    Nesta primeira versão:
    - gera a estrutura 3D interativa;
    - mantém compatibilidade com a assinatura futura para deformada interativa.
    """

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    structure_html_path = output_dir / "estrutura_3d_interativa.html"
    generate_interactive_structure_3d(model, structure_html_path)

    return {
        "structure_html": structure_html_path,
    }


def generate_interactive_structure_3d(model, output_path: Path) -> None:
    """
    Gera a estrutura 3D interativa em HTML usando Plotly.
    """

    fig = go.Figure()

    clean_mode = _is_large_model(model)

    _add_elements_trace(fig, model)
    _add_nodes_trace(fig, model, show_labels=not clean_mode)
    _add_supports_trace(fig, model)
    _add_nodal_loads_trace(fig, model, visible_by_default=not clean_mode)
    _add_distributed_loads_trace(
        fig,
        model,
        visible_by_default=not clean_mode,
        arrows_per_element=2 if clean_mode else 5,
    )

    fig.update_layout(
        title="Estrutura 3D Interativa",
        scene=dict(
            xaxis_title="X [m]",
            yaxis_title="Y [m]",
            zaxis_title="Z [m]",
            aspectmode="data",
        ),
        margin=dict(l=20, r=20, t=60, b=20),
        legend=dict(
            x=0.01,
            y=0.99,
            bgcolor="rgba(255,255,255,0.8)",
        ),
    )

    fig.write_html(str(output_path), include_plotlyjs="cdn")


def _add_elements_trace(fig: go.Figure, model) -> None:
    """
    Adiciona barras/elementos como linhas 3D.
    """

    x_vals = []
    y_vals = []
    z_vals = []
    texts = []

    for element in model.elements:
        node_i = model.node_by_id(element.node_i)
        node_j = model.node_by_id(element.node_j)

        x_vals.extend([node_i.x, node_j.x, None])
        y_vals.extend([node_i.y, node_j.y, None])
        z_vals.extend([node_i.z, node_j.z, None])

        label = f"E{element.id}"
        texts.extend([label, label, None])

    fig.add_trace(
        go.Scatter3d(
            x=x_vals,
            y=y_vals,
            z=z_vals,
            mode="lines",
            name="Elementos 3D",
            line=dict(width=6),
            text=texts,
            hoverinfo="text",
        )
    )


def _add_nodes_trace(fig: go.Figure, model, show_labels: bool = True) -> None:
    """
    Adiciona nós como marcadores 3D.
    """

    x_vals = [node.x for node in model.nodes]
    y_vals = [node.y for node in model.nodes]
    z_vals = [node.z for node in model.nodes]

    labels = [f"N{node.id}" for node in model.nodes]
    hover_text = [f"Nó {node.id}<br>x={node.x}<br>y={node.y}<br>z={node.z}" for node in model.nodes]

    mode = "markers+text" if show_labels else "markers"

    fig.add_trace(
        go.Scatter3d(
            x=x_vals,
            y=y_vals,
            z=z_vals,
            mode = mode,
            name="Nós 3D",
            marker=dict(size=5),
            text=labels,
            textposition="top center",
            hovertext=hover_text,
            hoverinfo="text",
        )
    )


def _add_supports_trace(fig: go.Figure, model) -> None:
    """
    Adiciona apoios como marcadores especiais.
    """

    if not getattr(model, "supports", None):
        return

    x_vals = []
    y_vals = []
    z_vals = []
    texts = []

    for support in model.supports:
        node = model.node_by_id(support.node)

        x_vals.append(node.x)
        y_vals.append(node.y)
        z_vals.append(node.z)

        restraint_keys = []
        for key in ("ux", "uy", "uz", "rx", "ry", "rz"):
            if getattr(support, key, False):
                restraint_keys.append(key)

        restraint_text = ", ".join(restraint_keys) if restraint_keys else "sem restrições"
        texts.append(f"Apoio N{support.node}<br>Restrições: {restraint_text}")

    fig.add_trace(
        go.Scatter3d(
            x=x_vals,
            y=y_vals,
            z=z_vals,
            mode="markers",
            name="Apoios 3D",
            marker=dict(size=8, symbol="square"),
            hovertext=texts,
            hoverinfo="text",
        )
    )


def _add_nodal_loads_trace(fig: go.Figure, model, visible_by_default: bool = True) -> None:
    """
    Adiciona cargas nodais translacionais como setas simples (segmentos de reta).
    """

    if not getattr(model, "nodal_loads", None):
        return

    max_magnitude = 0.0
    for load in model.nodal_loads:
        fx = float(getattr(load, "fx", 0.0))
        fy = float(getattr(load, "fy", 0.0))
        fz = float(getattr(load, "fz", 0.0))
        magnitude = math.sqrt(fx**2 + fy**2 + fz**2)
        max_magnitude = max(max_magnitude, magnitude)

    if max_magnitude <= 0.0:
        return

    scale = 0.12 * _characteristic_length(model) / max_magnitude

    x_vals = []
    y_vals = []
    z_vals = []
    texts = []

    for load in model.nodal_loads:
        fx = float(getattr(load, "fx", 0.0))
        fy = float(getattr(load, "fy", 0.0))
        fz = float(getattr(load, "fz", 0.0))

        magnitude = math.sqrt(fx**2 + fy**2 + fz**2)
        if magnitude <= 0.0:
            continue

        node = model.node_by_id(load.node)

        # seta desenhada no sentido da carga
        dx = fx * scale
        dy = fy * scale
        dz = fz * scale

        x_vals.extend([node.x, node.x + dx, None])
        y_vals.extend([node.y, node.y + dy, None])
        z_vals.extend([node.z, node.z + dz, None])

        texts.extend([
            f"N{load.node}<br>Fx={fx}<br>Fy={fy}<br>Fz={fz}",
            f"N{load.node}<br>Fx={fx}<br>Fy={fy}<br>Fz={fz}",
            None,
        ])

    if x_vals:
        fig.add_trace(
            go.Scatter3d(
                x=x_vals,
                y=y_vals,
                z=z_vals,
                mode="lines",
                name="Cargas nodais 3D",
                line=dict(width=5),
                hovertext=texts,
                hoverinfo="text",
                visible=True if visible_by_default else "legendonly",
            )
        )


def _add_distributed_loads_trace(fig: go.Figure, model, visible_by_default: bool = True, arrows_per_element: int = 5,) -> None:
    """
    Adiciona cargas distribuídas 3D.

    Nesta primeira versão:
    - plota apenas cargas distribuídas declaradas em coordenadas globais;
    - usa pequenas setas distribuídas ao longo da barra.
    """

    if not getattr(model, "distributed_loads", None):
        return

    # pega maior magnitude
    max_magnitude = 0.0
    for load in model.distributed_loads:
        qx = float(getattr(load, "qx", 0.0))
        qy = float(getattr(load, "qy", 0.0))
        qz = float(getattr(load, "qz", 0.0))
        magnitude = math.sqrt(qx**2 + qy**2 + qz**2)
        max_magnitude = max(max_magnitude, magnitude)

    if max_magnitude <= 0.0:
        return

    arrow_scale = 0.10 * _characteristic_length(model) / max_magnitude

    x_vals = []
    y_vals = []
    z_vals = []
    texts = []

    for load in model.distributed_loads:
        coordinate_system = str(getattr(load, "coordinate_system", "local")).lower()
        if coordinate_system != "global":
            continue

        qx = float(getattr(load, "qx", 0.0))
        qy = float(getattr(load, "qy", 0.0))
        qz = float(getattr(load, "qz", 0.0))

        magnitude = math.sqrt(qx**2 + qy**2 + qz**2)
        if magnitude <= 0.0:
            continue

        element = model.element_by_id(load.element)
        node_i = model.node_by_id(element.node_i)
        node_j = model.node_by_id(element.node_j)

        if arrows_per_element <= 1:
            positions = [0.5]
        else:
            positions = [
                0.15 + i * (0.70 / (arrows_per_element - 1))
                for i in range(arrows_per_element)
            ]

        # 5 posições ao longo do elemento
        for t in positions:
            px = node_i.x + t * (node_j.x - node_i.x)
            py = node_i.y + t * (node_j.y - node_i.y)
            pz = node_i.z + t * (node_j.z - node_i.z)

            dx = qx * arrow_scale
            dy = qy * arrow_scale
            dz = qz * arrow_scale

            x_vals.extend([px, px + dx, None])
            y_vals.extend([py, py + dy, None])
            z_vals.extend([pz, pz + dz, None])

            label = (
                f"E{load.element}<br>"
                f"qx={qx}<br>"
                f"qy={qy}<br>"
                f"qz={qz}<br>"
                f"(global)"
            )
            texts.extend([label, label, None])

    if x_vals:
        fig.add_trace(
            go.Scatter3d(
                x=x_vals,
                y=y_vals,
                z=z_vals,
                mode="lines",
                name="Cargas distribuídas 3D",
                line=dict(width=4, dash="dot"),
                hovertext=texts,
                hoverinfo="text",
                visible=True if visible_by_default else "legendonly",
            )
        )


def _characteristic_length(model) -> float:
    """
    Comprimento característico da estrutura, usado para escalar setas.
    """

    xs = [node.x for node in model.nodes]
    ys = [node.y for node in model.nodes]
    zs = [node.z for node in model.nodes]

    dx = max(xs) - min(xs) if xs else 1.0
    dy = max(ys) - min(ys) if ys else 1.0
    dz = max(zs) - min(zs) if zs else 1.0

    value = math.sqrt(dx**2 + dy**2 + dz**2)
    return value if value > 0.0 else 1.0

def _is_large_model(model) -> bool:
    """
    Decide se o modelo deve usar modo visual limpo por padrão.
    """

    complexity = (
        len(getattr(model, "nodes", []))
        + len(getattr(model, "elements", []))
        + len(getattr(model, "supports", []))
        + len(getattr(model, "nodal_loads", []))
        + len(getattr(model, "distributed_loads", []))
    )

    return complexity > 70
