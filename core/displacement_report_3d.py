from __future__ import annotations

import math
from pathlib import Path
from typing import Any


TRANSLATION_KEYS = ("ux", "uy", "uz")
ROTATION_KEYS = ("rx", "ry", "rz")
ALL_DISPLACEMENT_KEYS = TRANSLATION_KEYS + ROTATION_KEYS


def create_displacement_summary_3d(results: dict[str, Any]) -> dict[str, Any]:
    """
    Cria resumo de deslocamentos 3D a partir dos resultados frame3d.
    """

    records = list(results.get("displacements", []))

    if not records:
        raise ValueError("Nenhum deslocamento encontrado nos resultados 3D.")

    maxima = {}

    for key in ALL_DISPLACEMENT_KEYS:
        maxima[key] = _find_max_abs_component(records, key)

    maxima["horizontal_resultant"] = _find_max_resultant(
        records,
        keys=("ux", "uy"),
        label="sqrt(ux² + uy²)",
    )

    maxima["translation_resultant"] = _find_max_resultant(
        records,
        keys=("ux", "uy", "uz"),
        label="sqrt(ux² + uy² + uz²)",
    )

    maxima["rotation_resultant"] = _find_max_resultant(
        records,
        keys=("rx", "ry", "rz"),
        label="sqrt(rx² + ry² + rz²)",
    )

    story_drifts = calculate_story_drifts_3d(records)

    return {
        "analysis_type": results.get("analysis_type", "frame3d"),
        "number_of_nodes": results.get("number_of_nodes", len(records)),
        "maxima": maxima,
        "story_drifts": story_drifts,
    }


def write_displacement_summary_3d_txt(
    results: dict[str, Any],
    output_path: str | Path,
) -> None:
    """
    Escreve relatório textual de deslocamentos 3D.
    """

    summary = create_displacement_summary_3d(results)
    text = format_displacement_summary_3d(summary)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")


def format_displacement_summary_3d(summary: dict[str, Any]) -> str:
    """
    Formata o relatório textual de deslocamentos 3D.
    """

    lines: list[str] = []

    lines.append("RESUMO DE DESLOCAMENTOS 3D - Estruturalis")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"Tipo de análise: {summary.get('analysis_type', 'frame3d')}")
    lines.append(f"Número de nós: {summary.get('number_of_nodes', 0)}")
    lines.append("")

    lines.append("Máximos por componente:")
    lines.append("-" * 60)

    component_labels = {
        "ux": "Deslocamento ux",
        "uy": "Deslocamento uy",
        "uz": "Deslocamento uz",
        "rx": "Rotação rx",
        "ry": "Rotação ry",
        "rz": "Rotação rz",
    }

    component_units = {
        "ux": "m",
        "uy": "m",
        "uz": "m",
        "rx": "rad",
        "ry": "rad",
        "rz": "rad",
    }

    maxima = summary.get("maxima", {})

    for key in ALL_DISPLACEMENT_KEYS:
        record = maxima.get(key)
        if not record:
            continue

        lines.append(
            f"{component_labels[key]}: "
            f"{record['value']:.6e} {component_units[key]} | "
            f"|valor|={record['abs_value']:.6e} | "
            f"nó {record['node']}"
        )

    lines.append("")
    lines.append("Máximos resultantes:")
    lines.append("-" * 60)

    resultant_labels = {
        "horizontal_resultant": "Deslocamento horizontal resultante",
        "translation_resultant": "Deslocamento translacional resultante",
        "rotation_resultant": "Rotação resultante",
    }

    resultant_units = {
        "horizontal_resultant": "m",
        "translation_resultant": "m",
        "rotation_resultant": "rad",
    }

    for key in (
        "horizontal_resultant",
        "translation_resultant",
        "rotation_resultant",
    ):
        record = maxima.get(key)
        if not record:
            continue

        lines.append(
            f"{resultant_labels[key]}: "
            f"{record['value']:.6e} {resultant_units[key]} | "
            f"nó {record['node']} | "
            f"{record['formula']}"
        )

    lines.append("")
    lines.append("Drift aproximado por pavimento:")
    lines.append("-" * 60)

    story_drifts = summary.get("story_drifts", [])

    if not story_drifts:
        lines.append("Nenhum drift calculado.")
    else:
        for drift in story_drifts:
            lines.append(
                f"Z {drift['z_bottom']:.6g} -> {drift['z_top']:.6g} m | "
                f"altura={drift['height']:.6e} m | "
                f"drift máximo={drift['drift']:.6e} m | "
                f"razão={drift['drift_ratio']:.6e} | "
                f"ponto ({drift['x']:.6g}, {drift['y']:.6g})"
            )

    lines.append("")
    lines.append("Observação:")
    lines.append("O drift é calculado comparando nós com mesmas coordenadas x,y em níveis z consecutivos.")
    lines.append("Este relatório é preliminar e voltado para interpretação acadêmica.")
    lines.append("")

    return "\n".join(lines)


def calculate_story_drifts_3d(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Calcula drift aproximado entre níveis z consecutivos.

    Para cada par de pavimentos:
    - procura nós com o mesmo par (x, y);
    - calcula diferença horizontal entre deslocamentos ux, uy;
    - drift = sqrt((ux_top - ux_bottom)^2 + (uy_top - uy_bottom)^2).
    """

    nodes_by_level: dict[float, dict[tuple[float, float], dict[str, Any]]] = {}

    for record in records:
        z = _rounded_coord(record.get("z", 0.0))
        x = _rounded_coord(record.get("x", 0.0))
        y = _rounded_coord(record.get("y", 0.0))

        nodes_by_level.setdefault(z, {})[(x, y)] = record

    levels = sorted(nodes_by_level.keys())

    if len(levels) < 2:
        return []

    drifts = []

    for z_bottom, z_top in zip(levels[:-1], levels[1:]):
        height = float(z_top - z_bottom)

        if height <= 0.0:
            continue

        bottom_nodes = nodes_by_level[z_bottom]
        top_nodes = nodes_by_level[z_top]

        common_positions = sorted(set(bottom_nodes.keys()) & set(top_nodes.keys()))

        if not common_positions:
            continue

        max_record = None

        for x, y in common_positions:
            bottom = bottom_nodes[(x, y)]
            top = top_nodes[(x, y)]

            dux = float(top.get("ux", 0.0)) - float(bottom.get("ux", 0.0))
            duy = float(top.get("uy", 0.0)) - float(bottom.get("uy", 0.0))

            drift = math.sqrt(dux**2 + duy**2)
            drift_ratio = drift / height

            candidate = {
                "z_bottom": float(z_bottom),
                "z_top": float(z_top),
                "height": height,
                "x": float(x),
                "y": float(y),
                "node_bottom": bottom.get("node"),
                "node_top": top.get("node"),
                "dux": dux,
                "duy": duy,
                "drift": drift,
                "drift_ratio": drift_ratio,
            }

            if max_record is None or candidate["drift"] > max_record["drift"]:
                max_record = candidate

        if max_record is not None:
            drifts.append(max_record)

    return drifts


def _find_max_abs_component(
    records: list[dict[str, Any]],
    key: str,
) -> dict[str, Any]:
    record = max(records, key=lambda item: abs(float(item.get(key, 0.0))))
    value = float(record.get(key, 0.0))

    return {
        "node": record.get("node"),
        "x": float(record.get("x", 0.0)),
        "y": float(record.get("y", 0.0)),
        "z": float(record.get("z", 0.0)),
        "key": key,
        "value": value,
        "abs_value": abs(value),
    }


def _find_max_resultant(
    records: list[dict[str, Any]],
    keys: tuple[str, ...],
    label: str,
) -> dict[str, Any]:
    def resultant(record: dict[str, Any]) -> float:
        return math.sqrt(
            sum(float(record.get(key, 0.0)) ** 2 for key in keys)
        )

    record = max(records, key=resultant)
    value = resultant(record)

    return {
        "node": record.get("node"),
        "x": float(record.get("x", 0.0)),
        "y": float(record.get("y", 0.0)),
        "z": float(record.get("z", 0.0)),
        "keys": list(keys),
        "formula": label,
        "value": value,
    }


def _rounded_coord(value: Any, ndigits: int = 9) -> float:
    return round(float(value), ndigits)
