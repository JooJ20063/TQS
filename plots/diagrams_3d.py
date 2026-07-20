from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import matplotlib.pyplot as plt

from core.model import StructuralModel


def generate_all_diagrams_3d(
    model: StructuralModel,
    results: dict[str, Any],
    output_dir: str | Path,
) -> None:
    """
    Gera todos os diagramas 3D disponíveis.

    Nesta etapa:
    - estrutura_3d.png;
    - deformada_3d.png;
    - resumo_grafico_3d.txt.
    """

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    load_scale = calculate_nodal_load_scale_factor(model)

    generate_structure_plot_3d(
        model=model,
        output_path=output_dir / "estrutura_3d.png",
        load_scale=load_scale,
    )

    generate_deformed_shape_plot_3d(
        model=model,
        results=results,
        output_path=output_dir / "deformada_3d.png",
    )

    write_graphics_summary_3d(
        model=model,
        results=results,
        output_path=output_dir / "resumo_grafico_3d.txt",
        load_scale=load_scale,
    )

def generate_structure_plot_3d(
    model: StructuralModel,
    output_path: str | Path,
    load_scale: float | None = None,
) -> None:
    """
    Gera a visualização da estrutura tridimensional indeformada.
    """

    fig = plt.figure(figsize=(9, 7))
    ax = fig.add_subplot(111, projection="3d")

    all_points: list[np.ndarray] = []

    for element in model.elements:
        node_i = model.get_node(element.node_i)
        node_j = model.get_node(element.node_j)

        xi, yi, zi = node_i.x, node_i.y, node_i.z
        xj, yj, zj = node_j.x, node_j.y, node_j.z

        ax.plot(
            [xi, xj],
            [yi, yj],
            [zi, zj],
            linewidth=2.0,
            marker="o",
        )

        all_points.append(np.array([xi, yi, zi], dtype=float))
        all_points.append(np.array([xj, yj, zj], dtype=float))

        xm = 0.5 * (xi + xj)
        ym = 0.5 * (yi + yj)
        zm = 0.5 * (zi + zj)

        ax.text(xm, ym, zm, f"E{element.id}", fontsize=8)

    for node in model.nodes:
        ax.text(node.x, node.y, node.z, f"N{node.id}", fontsize=8)
        plot_supports_3d(ax, model)
        plot_nodal_loads_3d(ax, model, load_scale=load_scale)
        add_legend_if_needed(ax)

    ax.set_title("Estrutura 3D")
    configure_3d_axes(ax)
    set_equal_3d_axes(ax, all_points)

    save_figure(fig, output_path)


def generate_deformed_shape_plot_3d(
    model: StructuralModel,
    results: dict[str, Any],
    output_path: str | Path,
    scale_factor: float | None = None,
) -> None:
    """
    Gera a visualização da deformada tridimensional.

    A estrutura original é desenhada junto da deformada para comparação.
    """

    displacements = map_displacements_by_node(results)

    if scale_factor is None:
        scale_factor = calculate_deformation_scale_factor(model, results)

    fig = plt.figure(figsize=(9, 7))
    ax = fig.add_subplot(111, projection="3d")

    all_points: list[np.ndarray] = []

    for element in model.elements:
        node_i = model.get_node(element.node_i)
        node_j = model.get_node(element.node_j)

        original_i = np.array([node_i.x, node_i.y, node_i.z], dtype=float)
        original_j = np.array([node_j.x, node_j.y, node_j.z], dtype=float)

        disp_i = get_node_displacement_vector(displacements, node_i.id)
        disp_j = get_node_displacement_vector(displacements, node_j.id)

        deformed_i = original_i + scale_factor * disp_i
        deformed_j = original_j + scale_factor * disp_j

        ax.plot(
            [original_i[0], original_j[0]],
            [original_i[1], original_j[1]],
            [original_i[2], original_j[2]],
            linestyle="--",
            linewidth=1.0,
            alpha=0.5,
        )

        ax.plot(
            [deformed_i[0], deformed_j[0]],
            [deformed_i[1], deformed_j[1]],
            [deformed_i[2], deformed_j[2]],
            linewidth=2.0,
            marker="o",
        )

        all_points.extend([original_i, original_j, deformed_i, deformed_j])

    plot_supports_3d(ax, model)
    add_legend_if_needed(ax)

    ax.set_title(f"Deformada 3D — fator {scale_factor:.3g}")
    configure_3d_axes(ax)
    set_equal_3d_axes(ax, all_points)

    save_figure(fig, output_path)


def map_displacements_by_node(results: dict[str, Any]) -> dict[int, dict[str, float]]:
    """
    Cria um mapa:
    node_id -> deslocamentos do nó.
    """

    output: dict[int, dict[str, float]] = {}

    for row in results.get("displacements", []):
        node_id = int(row["node"])

        output[node_id] = {
            "ux": float(row.get("ux", 0.0)),
            "uy": float(row.get("uy", 0.0)),
            "uz": float(row.get("uz", 0.0)),
        }

    return output


def get_node_displacement_vector(
    displacements: dict[int, dict[str, float]],
    node_id: int,
) -> np.ndarray:
    """
    Retorna o vetor de deslocamento translacional de um nó.
    """

    row = displacements.get(node_id, {})

    return np.array(
        [
            float(row.get("ux", 0.0)),
            float(row.get("uy", 0.0)),
            float(row.get("uz", 0.0)),
        ],
        dtype=float,
    )


def calculate_deformation_scale_factor(
    model: StructuralModel,
    results: dict[str, Any],
) -> float:
    """
    Calcula um fator automático para visualização da deformada.

    A ideia é amplificar a deformada para algo visível, sem distorcer demais.
    """

    structure_size = calculate_structure_size(model)
    max_displacement = calculate_max_translation(results)

    if structure_size <= 0.0 or max_displacement <= 0.0:
        return 1.0

    target_visual_displacement = 0.10 * structure_size

    return target_visual_displacement / max_displacement


def calculate_structure_size(model: StructuralModel) -> float:
    """
    Calcula uma dimensão característica da estrutura.
    """

    points = [
        np.array([node.x, node.y, node.z], dtype=float)
        for node in model.nodes
    ]

    if not points:
        return 1.0

    coordinates = np.array(points, dtype=float)

    ranges = np.ptp(coordinates, axis=0)
    size = float(np.max(ranges))

    if size <= 0.0:
        return 1.0

    return size


def calculate_max_translation(results: dict[str, Any]) -> float:
    """
    Retorna o maior deslocamento translacional absoluto.
    """

    max_value = 0.0

    for row in results.get("displacements", []):
        ux = float(row.get("ux", 0.0))
        uy = float(row.get("uy", 0.0))
        uz = float(row.get("uz", 0.0))

        value = float(np.linalg.norm([ux, uy, uz]))
        max_value = max(max_value, value)

    return max_value


def configure_3d_axes(ax) -> None:
    """
    Configura rótulos e grade dos eixos 3D.
    """

    ax.set_xlabel("X [m]")
    ax.set_ylabel("Y [m]")
    ax.set_zlabel("Z [m]")
    ax.grid(True)
    ax.view_init(elev=25, azim=-60)


def set_equal_3d_axes(ax, points: list[np.ndarray]) -> None:
    """
    Ajusta os eixos 3D para manter escala visual equivalente em X, Y e Z.
    """

    if not points:
        return

    coordinates = np.array(points, dtype=float)

    min_values = coordinates.min(axis=0)
    max_values = coordinates.max(axis=0)

    centers = 0.5 * (min_values + max_values)
    ranges = max_values - min_values

    max_range = float(np.max(ranges))

    if max_range <= 0.0:
        max_range = 1.0

    half_range = 0.55 * max_range

    ax.set_xlim(centers[0] - half_range, centers[0] + half_range)
    ax.set_ylim(centers[1] - half_range, centers[1] + half_range)
    ax.set_zlim(centers[2] - half_range, centers[2] + half_range)

def plot_supports_3d(ax, model: StructuralModel) -> None:
    """
    Desenha apoios no gráfico 3D.

    Convenção visual preliminar:
    - apoio totalmente engastado: marcador quadrado;
    - apoio parcial: marcador triangular;
    - texto mostra os graus de liberdade restringidos.
    """

    for support in model.supports:
        node = model.get_node(support.node)

        restrained_labels = get_restrained_support_labels(support)
        label_text = ",".join(restrained_labels)

        if is_fully_fixed_support_3d(support):
            ax.scatter(
                [node.x],
                [node.y],
                [node.z],
                marker="s",
                s=80,
                label="Engaste 3D",
            )
            ax.text(
                node.x,
                node.y,
                node.z,
                f" Apoio N{node.id}\n engaste",
                fontsize=8,
            )
        else:
            ax.scatter(
                [node.x],
                [node.y],
                [node.z],
                marker="^",
                s=70,
                label="Apoio parcial 3D",
            )
            ax.text(
                node.x,
                node.y,
                node.z,
                f" Apoio N{node.id}\n {label_text}",
                fontsize=8,
            )


def get_restrained_support_labels(support) -> list[str]:
    """
    Retorna os graus de liberdade restringidos por um apoio.
    """

    labels = []

    for name in ("ux", "uy", "uz", "rx", "ry", "rz"):
        if getattr(support, name, False):
            labels.append(name)

    return labels


def is_fully_fixed_support_3d(support) -> bool:
    """
    Verifica se o apoio restringe os 6 graus de liberdade 3D.
    """

    return all(
        getattr(support, name, False)
        for name in ("ux", "uy", "uz", "rx", "ry", "rz")
    )


def add_legend_if_needed(ax) -> None:
    """
    Adiciona legenda removendo rótulos duplicados.
    """

    handles, labels = ax.get_legend_handles_labels()

    if not handles:
        return

    unique = {}

    for handle, label in zip(handles, labels):
        if label not in unique:
            unique[label] = handle

    ax.legend(
        unique.values(),
        unique.keys(),
        loc="best",
        fontsize=8,
    )

def plot_nodal_loads_3d(
    ax,
    model: StructuralModel,
    load_scale: float | None = None,
) -> None:
    """
    Desenha cargas nodais translacionais no gráfico 3D.

    Nesta etapa são representadas:
    - fx;
    - fy;
    - fz.

    Momentos nodais mx, my, mz ficam para um PR separado.
    """

    if not model.nodal_loads:
        return

    if load_scale is None:
        load_scale = calculate_nodal_load_scale_factor(model)

    for load in model.nodal_loads:
        node = model.get_node(load.node)

        force_vector = np.array(
            [
                float(load.fx),
                float(load.fy),
                float(load.fz),
            ],
            dtype=float,
        )

        force_norm = float(np.linalg.norm(force_vector))

        if force_norm <= 0.0:
            continue

        arrow_vector = load_scale * force_vector

        ax.quiver(
            node.x,
            node.y,
            node.z,
            arrow_vector[0],
            arrow_vector[1],
            arrow_vector[2],
            arrow_length_ratio=0.20,
            linewidth=1.8,
            label="Carga nodal 3D",
        )

        label = format_nodal_force_label(load)

        label_position = np.array([node.x, node.y, node.z], dtype=float) + arrow_vector

        ax.text(
            label_position[0],
            label_position[1],
            label_position[2],
            label,
            fontsize=8,
        )


def calculate_nodal_load_scale_factor(model: StructuralModel) -> float:
    """
    Calcula fator de escala visual para setas de cargas nodais.

    A maior carga nodal translacional será desenhada com comprimento
    aproximado de 15% do tamanho característico da estrutura.
    """

    max_force = calculate_max_nodal_force(model)
    structure_size = calculate_structure_size(model)

    if max_force <= 0.0 or structure_size <= 0.0:
        return 1.0

    target_arrow_length = 0.15 * structure_size

    return target_arrow_length / max_force


def calculate_max_nodal_force(model: StructuralModel) -> float:
    """
    Retorna a maior força nodal translacional resultante.
    """

    max_force = 0.0

    for load in model.nodal_loads:
        force_vector = np.array(
            [
                float(load.fx),
                float(load.fy),
                float(load.fz),
            ],
            dtype=float,
        )

        force_norm = float(np.linalg.norm(force_vector))
        max_force = max(max_force, force_norm)

    return max_force


def format_nodal_force_label(load) -> str:
    """
    Formata texto compacto para cargas nodais translacionais.
    """

    parts = []

    if abs(float(load.fx)) > 0.0:
        parts.append(f"Fx={float(load.fx):.2g}")

    if abs(float(load.fy)) > 0.0:
        parts.append(f"Fy={float(load.fy):.2g}")

    if abs(float(load.fz)) > 0.0:
        parts.append(f"Fz={float(load.fz):.2g}")

    if not parts:
        return f"N{load.node}"

    return "\n".join(parts)

def write_graphics_summary_3d(
    model: StructuralModel,
    results: dict[str, Any],
    output_path: str | Path,
    load_scale: float,
) -> None:
    """
    Escreve relatório textual dos gráficos 3D gerados.
    """

    text = format_graphics_summary_3d(
        model=model,
        results=results,
        load_scale=load_scale,
    )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        file.write(text)


def format_graphics_summary_3d(
    model: StructuralModel,
    results: dict[str, Any],
    load_scale: float,
) -> str:
    """
    Formata relatório textual dos gráficos 3D.
    """

    lines: list[str] = []

    lines.append("RESUMO GRÁFICO 3D - Estruturalis")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"Modelo: {results.get('model_name', 'sem_nome')}")
    lines.append(f"Tipo de análise: {results.get('analysis_type', model.analysis_type)}")
    lines.append(f"Nós: {len(model.nodes)}")
    lines.append(f"Elementos: {len(model.elements)}")
    lines.append(f"Apoios: {len(model.supports)}")
    lines.append(f"Cargas nodais: {len(model.nodal_loads)}")
    lines.append(f"Cargas distribuídas: {len(model.distributed_loads)}")
    lines.append("")
    lines.append("Arquivos gráficos gerados:")
    lines.append("- estrutura_3d.png")
    lines.append("- deformada_3d.png")
    lines.append("")
    lines.append("Camadas representadas em estrutura_3d.png:")
    lines.append("- geometria indeformada")
    lines.append("- identificação de nós")
    lines.append("- identificação de elementos")
    lines.append("- apoios 3D")
    lines.append("- cargas nodais translacionais Fx, Fy e Fz")
    lines.append("")
    lines.append("Camadas representadas em deformada_3d.png:")
    lines.append("- geometria indeformada de referência")
    lines.append("- deformada amplificada")
    lines.append("- apoios 3D")
    lines.append("")
    lines.append("Escalas visuais:")
    lines.append(f"- fator visual de cargas nodais: {load_scale:.6e} m/kN")
    lines.append("")
    lines.append("Convenções:")
    lines.append("- cargas nodais são desenhadas como setas aplicadas nos nós")
    lines.append("- o comprimento das setas é visual, não está em escala estrutural real")
    lines.append("- momentos nodais ainda não são representados graficamente")
    lines.append("- cargas distribuídas ainda não são representadas graficamente")
    lines.append("")
    lines.append("Observação:")
    lines.append("Este relatório descreve a geração gráfica 3D preliminar.")
    lines.append("Não substitui interpretação técnica dos resultados numéricos.")
    lines.append("")

    return "\n".join(lines)

def save_figure(fig, output_path: str | Path) -> None:
    """
    Salva e fecha a figura.
    """

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
