# plots/diagrams.py

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import matplotlib.pyplot as plt

from core.model import StructuralModel, Element


def generate_all_diagrams(
    model: StructuralModel,
    results: dict[str, Any],
    output_dir: str | Path,
) -> None:
    """
    Gera os principais desenhos da análise estrutural.

    Arquivos gerados:
    - estrutura.png
    - deformada.png
    - cortante.png
    - momento_fletor.png
    """

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    plot_structure(model, output_dir / "estrutura.png")
    plot_deformed_shape(model, results, output_dir / "deformada.png")
    plot_shear_diagram(model, results, output_dir / "cortante.png")
    plot_moment_diagram(model, results, output_dir / "momento_fletor.png")


# ==========================================================
# ESTRUTURA ORIGINAL
# ==========================================================

def plot_structure(model: StructuralModel, file_path: str | Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 6))

    for element in model.elements:
        ni = model.get_node(element.node_i)
        nj = model.get_node(element.node_j)

        ax.plot([ni.x, nj.x], [ni.y, nj.y], marker="o", linewidth=2)

        xm = 0.5 * (ni.x + nj.x)
        ym = 0.5 * (ni.y + nj.y)

        ax.text(xm, ym, f"E{element.id}", fontsize=9, ha="center", va="bottom")

    for node in model.nodes:
        ax.text(node.x, node.y, f"N{node.id}", fontsize=9, ha="right", va="top")

    draw_supports(ax, model)

    finish_axes(ax, model, "Geometria da estrutura")
    save_figure(fig, file_path)


# ==========================================================
# DEFORMADA
# ==========================================================

def plot_deformed_shape(
    model: StructuralModel,
    results: dict[str, Any],
    file_path: str | Path,
) -> None:
    fig, ax = plt.subplots(figsize=(10, 6))

    displacement_map = {item["node"]: item for item in results["displacements"]}
    scale = calculate_deformation_scale(model, results)

    for element in model.elements:
        ni = model.get_node(element.node_i)
        nj = model.get_node(element.node_j)

        ax.plot(
            [ni.x, nj.x],
            [ni.y, nj.y],
            linestyle="--",
            linewidth=1,
            label="Original" if element.id == model.elements[0].id else None,
        )

    for element in model.elements:
        ni = model.get_node(element.node_i)
        nj = model.get_node(element.node_j)

        di = displacement_map[element.node_i]
        dj = displacement_map[element.node_j]

        xi = ni.x + scale * di["ux"]
        yi = ni.y + scale * di["uy"]

        xj = nj.x + scale * dj["ux"]
        yj = nj.y + scale * dj["uy"]

        ax.plot(
            [xi, xj],
            [yi, yj],
            marker="o",
            linewidth=2,
            label="Deformada" if element.id == model.elements[0].id else None,
        )

    draw_supports(ax, model)

    finish_axes(ax, model, f"Deformada da estrutura - fator {scale:.2e}")
    ax.legend()
    save_figure(fig, file_path)


def calculate_deformation_scale(
    model: StructuralModel,
    results: dict[str, Any],
) -> float:
    max_dimension = calculate_model_dimension(model)

    max_displacement = 0.0

    for item in results["displacements"]:
        displacement = np.sqrt(item["ux"] ** 2 + item["uy"] ** 2)
        max_displacement = max(max_displacement, displacement)

    if max_displacement <= 0:
        return 1.0

    return 0.12 * max_dimension / max_displacement


# ==========================================================
# DIAGRAMA DE CORTANTE
# ==========================================================

def plot_shear_diagram(
    model: StructuralModel,
    results: dict[str, Any],
    file_path: str | Path,
) -> None:
    fig, ax = plt.subplots(figsize=(10, 6))

    max_abs_shear = get_max_abs_diagram_value(model, results, diagram_type="shear")
    scale = calculate_diagram_scale(model, max_abs_shear)

    for element in model.elements:
        element_result = get_element_result(results, element.id)
        qy = get_total_local_qy(model, element)

        x_local, values = sample_shear_values(element_result, qy, n_points=30)

        draw_element_diagram(
            ax=ax,
            model=model,
            element=element,
            x_local=x_local,
            values=values,
            scale=scale,
            value_suffix="",
        )

    draw_structure_base(ax, model)
    draw_supports(ax, model)

    finish_axes(ax, model, "Diagrama de esforço cortante V [kN]")
    save_figure(fig, file_path)


def sample_shear_values(
    element_result: dict[str, Any],
    qy: float,
    n_points: int = 30,
) -> tuple[np.ndarray, np.ndarray]:
    length = element_result["length"]
    forces = element_result["local_end_forces"]

    x_local = np.linspace(0.0, length, n_points)

    v_i = forces["shear_i"]
    values = v_i + qy * x_local

    return x_local, values


# ==========================================================
# DIAGRAMA DE MOMENTO FLETOR
# ==========================================================

def plot_moment_diagram(
    model: StructuralModel,
    results: dict[str, Any],
    file_path: str | Path,
) -> None:
    fig, ax = plt.subplots(figsize=(10, 6))

    max_abs_moment = get_max_abs_diagram_value(model, results, diagram_type="moment")
    scale = calculate_diagram_scale(model, max_abs_moment)

    for element in model.elements:
        element_result = get_element_result(results, element.id)
        qy = get_total_local_qy(model, element)

        x_local, values = sample_moment_values(element_result, qy, n_points=40)

        draw_element_diagram(
            ax=ax,
            model=model,
            element=element,
            x_local=x_local,
            values=values,
            scale=scale,
            value_suffix="",
        )

    draw_structure_base(ax, model)
    draw_supports(ax, model)

    finish_axes(ax, model, "Diagrama de momento fletor M [kN.m]")
    save_figure(fig, file_path)


def sample_moment_values(
    element_result: dict[str, Any],
    qy: float,
    n_points: int = 40,
) -> tuple[np.ndarray, np.ndarray]:
    length = element_result["length"]
    forces = element_result["local_end_forces"]

    x_local = np.linspace(0.0, length, n_points)

    m_0 = -forces["moment_i"]
    v_0 = forces["shear_i"]

    values = m_0 + v_0 * x_local + 0.5 * qy * x_local**2

    return x_local, values


# ==========================================================
# DESENHO DOS DIAGRAMAS
# ==========================================================

def draw_element_diagram(
    ax,
    model: StructuralModel,
    element: Element,
    x_local: np.ndarray,
    values: np.ndarray,
    scale: float,
    value_suffix: str = "",
) -> None:
    ni = model.get_node(element.node_i)

    _, _, _, c, s = element.geometry(model)

    # Vetor normal à barra
    nx = -s
    ny = c

    base_x = ni.x + c * x_local
    base_y = ni.y + s * x_local

    diagram_x = base_x + nx * values * scale
    diagram_y = base_y + ny * values * scale

    ax.plot(diagram_x, diagram_y, linewidth=2)

    # Fechamento nas extremidades
    ax.plot([base_x[0], diagram_x[0]], [base_y[0], diagram_y[0]], linewidth=1)
    ax.plot([base_x[-1], diagram_x[-1]], [base_y[-1], diagram_y[-1]], linewidth=1)

    # Linha base do elemento
    ax.plot(base_x, base_y, linewidth=1)

    # Preenche visualmente o diagrama com linhas discretas
    step = max(1, len(x_local) // 8)

    for i in range(0, len(x_local), step):
        ax.plot(
            [base_x[i], diagram_x[i]],
            [base_y[i], diagram_y[i]],
            linewidth=0.6,
        )

    # Valores nas extremidades
    ax.text(
        diagram_x[0],
        diagram_y[0],
        f"{values[0]:.2f}{value_suffix}",
        fontsize=8,
        ha="center",
        va="bottom",
    )

    ax.text(
        diagram_x[-1],
        diagram_y[-1],
        f"{values[-1]:.2f}{value_suffix}",
        fontsize=8,
        ha="center",
        va="bottom",
    )

    # Valor máximo no trecho
    idx_max = int(np.argmax(np.abs(values)))

    if 0 < idx_max < len(values) - 1:
        ax.text(
            diagram_x[idx_max],
            diagram_y[idx_max],
            f"{values[idx_max]:.2f}{value_suffix}",
            fontsize=8,
            ha="center",
            va="bottom",
        )


def draw_structure_base(ax, model: StructuralModel) -> None:
    for element in model.elements:
        ni = model.get_node(element.node_i)
        nj = model.get_node(element.node_j)

        ax.plot([ni.x, nj.x], [ni.y, nj.y], linewidth=1)


def draw_supports(ax, model: StructuralModel) -> None:
    max_dimension = calculate_model_dimension(model)
    size = 0.035 * max_dimension

    for support in model.supports:
        node = model.get_node(support.node)

        if support.ux and support.uy and support.rz:
            label = "Engaste"
        elif support.ux and support.uy:
            label = "Apoio fixo"
        elif support.uy:
            label = "Rolete"
        elif support.ux:
            label = "Apoio horizontal"
        else:
            label = "Apoio"

        ax.scatter(node.x, node.y, marker="s", s=50)

        ax.text(
            node.x,
            node.y - size,
            label,
            fontsize=8,
            ha="center",
            va="top",
        )


# ==========================================================
# HELPERS
# ==========================================================

def get_element_result(
    results: dict[str, Any],
    element_id: int,
) -> dict[str, Any]:
    for item in results["elements"]:
        if item["id"] == element_id:
            return item

    raise KeyError(f"Resultado do elemento {element_id} não encontrado.")


def get_total_local_qy(
    model: StructuralModel,
    element: Element,
) -> float:
    total_qy = 0.0

    for load in model.distributed_loads:
        if load.element == element.id:
            total_qy += load.qy

    return total_qy


def get_max_abs_diagram_value(
    model: StructuralModel,
    results: dict[str, Any],
    diagram_type: str,
) -> float:
    max_value = 0.0

    for element in model.elements:
        element_result = get_element_result(results, element.id)
        qy = get_total_local_qy(model, element)

        if diagram_type == "shear":
            _, values = sample_shear_values(element_result, qy, n_points=40)
        elif diagram_type == "moment":
            _, values = sample_moment_values(element_result, qy, n_points=40)
        else:
            raise ValueError(f"Tipo de diagrama desconhecido: {diagram_type}")

        max_value = max(max_value, float(np.max(np.abs(values))))

    return max_value


def calculate_model_dimension(model: StructuralModel) -> float:
    xs = [node.x for node in model.nodes]
    ys = [node.y for node in model.nodes]

    dx = max(xs) - min(xs)
    dy = max(ys) - min(ys)

    dimension = max(dx, dy)

    if dimension <= 0:
        return 1.0

    return dimension


def calculate_diagram_scale(
    model: StructuralModel,
    max_abs_value: float,
) -> float:
    if max_abs_value <= 0:
        return 1.0

    max_dimension = calculate_model_dimension(model)

    return 0.18 * max_dimension / max_abs_value


def finish_axes(ax, model: StructuralModel, title: str) -> None:
    """
    Finaliza o gráfico com margens automáticas melhores.

    Isso evita aquele efeito de gráfico espremido ou cortado.
    """

    ax.set_title(title)
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")

    ax.grid(True)

    add_plot_margins(ax, model)
    ax.set_aspect("equal", adjustable="box")


def add_plot_margins(ax, model: StructuralModel) -> None:
    xs = [node.x for node in model.nodes]
    ys = [node.y for node in model.nodes]

    dimension = calculate_model_dimension(model)
    margin = 0.25 * dimension

    x_min = min(xs) - margin
    x_max = max(xs) + margin
    y_min = min(ys) - margin
    y_max = max(ys) + margin

    # Se a estrutura for muito horizontal, damos mais espaço vertical.
    if abs(y_max - y_min) < 0.40 * dimension:
        y_mid = 0.5 * (y_min + y_max)
        y_min = y_mid - 0.30 * dimension
        y_max = y_mid + 0.30 * dimension

    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)


def save_figure(fig, file_path: str | Path) -> None:
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    fig.tight_layout()
    fig.savefig(file_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
