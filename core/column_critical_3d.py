from __future__ import annotations

import math
from typing import Any

from core.beam_design_3d import classify_element_3d


COLUMN_FORCE_GROUPS = (
    "normal",
    "shear_y",
    "shear_z",
    "torsion",
    "moment_y",
    "moment_z",
)


def create_column_critical_forces_3d(model, envelope: dict[str, Any]) -> dict[str, Any]:
    """
    Cria relatório de esforços críticos em pilares 3D.

    Esta rotina NÃO dimensiona pilares.

    Ela apenas:
    - identifica elementos classificados como pilares;
    - extrai N, Vy, Vz, T, My e Mz da envoltória 3D;
    - calcula um índice preliminar normalizado para triagem:
        |N|/Nmax + |My|/Mymax + |Mz|/Mzmax

    O índice é apenas classificatório e não representa verificação normativa.
    """

    records: list[dict[str, Any]] = []

    for element in model.elements:
        classification = classify_element_3d(model, element)

        if classification != "column":
            continue

        envelope_element = _get_envelope_element(envelope, element.id)

        if envelope_element is None:
            records.append(
                {
                    "element": element.id,
                    "node_i": element.node_i,
                    "node_j": element.node_j,
                    "classification": classification,
                    "status": "missing_envelope",
                    "reason": "Elemento não encontrado na envoltória 3D.",
                }
            )
            continue

        node_i = _get_node(model, element.node_i)
        node_j = _get_node(model, element.node_j)

        force_records = {
            group_name: _get_group_record(envelope_element, group_name)
            for group_name in COLUMN_FORCE_GROUPS
        }

        records.append(
            {
                "element": element.id,
                "node_i": element.node_i,
                "node_j": element.node_j,
                "classification": classification,
                "status": "ok",
                "length": _element_length(node_i, node_j),
                "x_i": float(node_i.x),
                "y_i": float(node_i.y),
                "z_i": float(node_i.z),
                "x_j": float(node_j.x),
                "y_j": float(node_j.y),
                "z_j": float(node_j.z),
                "forces": force_records,
            }
        )

    _add_preliminary_interaction_indices(records)

    return {
        "analysis_type": "frame3d",
        "report_type": "column_critical_forces_3d",
        "number_of_columns": len([r for r in records if r.get("status") == "ok"]),
        "number_of_missing": len([r for r in records if r.get("status") != "ok"]),
        "hypotheses": [
            "Elementos predominantemente verticais são classificados como pilares.",
            "Os esforços são extraídos da envoltória 3D no sistema local da barra.",
            "O índice combinado é normalizado e serve apenas para triagem.",
            "Esta rotina não dimensiona pilares.",
            "Não há verificação de interação N + My + Mz nesta versão.",
        ],
        "columns": records,
        "global": _create_global_summary(records),
    }


def _add_preliminary_interaction_indices(records: list[dict[str, Any]]) -> None:
    valid_records = [r for r in records if r.get("status") == "ok"]

    if not valid_records:
        return

    max_n = max(_abs_force(record, "normal") for record in valid_records)
    max_my = max(_abs_force(record, "moment_y") for record in valid_records)
    max_mz = max(_abs_force(record, "moment_z") for record in valid_records)

    max_n = max(max_n, 1.0e-12)
    max_my = max(max_my, 1.0e-12)
    max_mz = max(max_mz, 1.0e-12)

    for record in valid_records:
        n_ratio = _abs_force(record, "normal") / max_n
        my_ratio = _abs_force(record, "moment_y") / max_my
        mz_ratio = _abs_force(record, "moment_z") / max_mz

        record["preliminary_index"] = {
            "normal_ratio": n_ratio,
            "moment_y_ratio": my_ratio,
            "moment_z_ratio": mz_ratio,
            "value": n_ratio + my_ratio + mz_ratio,
            "formula": "|N|/Nmax + |My|/Mymax + |Mz|/Mzmax",
        }


def _create_global_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    valid_records = [r for r in records if r.get("status") == "ok"]

    if not valid_records:
        return {
            "max_normal": None,
            "max_moment_y": None,
            "max_moment_z": None,
            "max_shear_y": None,
            "max_shear_z": None,
            "max_torsion": None,
            "max_preliminary_index": None,
        }

    return {
        "max_normal": _critical_by_group(valid_records, "normal"),
        "max_moment_y": _critical_by_group(valid_records, "moment_y"),
        "max_moment_z": _critical_by_group(valid_records, "moment_z"),
        "max_shear_y": _critical_by_group(valid_records, "shear_y"),
        "max_shear_z": _critical_by_group(valid_records, "shear_z"),
        "max_torsion": _critical_by_group(valid_records, "torsion"),
        "max_preliminary_index": _critical_by_preliminary_index(valid_records),
    }


def _critical_by_group(
    records: list[dict[str, Any]],
    group_name: str,
) -> dict[str, Any]:
    record = max(records, key=lambda item: _abs_force(item, group_name))
    force = record["forces"][group_name]

    return {
        "element": record["element"],
        "node_i": record["node_i"],
        "node_j": record["node_j"],
        "group": group_name,
        "value": force["value"],
        "abs_value": force["abs_value"],
        "component": force["component"],
        "case": force["case"],
    }


def _critical_by_preliminary_index(records: list[dict[str, Any]]) -> dict[str, Any]:
    record = max(
        records,
        key=lambda item: float(item.get("preliminary_index", {}).get("value", 0.0)),
    )

    return {
        "element": record["element"],
        "node_i": record["node_i"],
        "node_j": record["node_j"],
        "value": record.get("preliminary_index", {}).get("value", 0.0),
        "normal_ratio": record.get("preliminary_index", {}).get("normal_ratio", 0.0),
        "moment_y_ratio": record.get("preliminary_index", {}).get("moment_y_ratio", 0.0),
        "moment_z_ratio": record.get("preliminary_index", {}).get("moment_z_ratio", 0.0),
        "formula": record.get("preliminary_index", {}).get("formula", ""),
    }


def _abs_force(record: dict[str, Any], group_name: str) -> float:
    return float(record.get("forces", {}).get(group_name, {}).get("abs_value", 0.0))


def _get_group_record(
    envelope_element: dict[str, Any],
    group_name: str,
) -> dict[str, Any]:
    group = envelope_element.get("groups", {}).get(group_name, {})
    abs_record = group.get("abs", {})

    value = float(abs_record.get("value", 0.0))

    return {
        "value": value,
        "abs_value": abs(value),
        "component": abs_record.get("component", ""),
        "case": abs_record.get("case", ""),
    }


def _get_envelope_element(
    envelope: dict[str, Any],
    element_id: int,
) -> dict[str, Any] | None:
    for element in envelope.get("elements", []):
        if int(element.get("id")) == int(element_id):
            return element

    return None


def _get_node(model, node_id: int):
    if hasattr(model, "node_by_id"):
        return model.node_by_id(node_id)

    if hasattr(model, "get_node"):
        return model.get_node(node_id)

    for node in model.nodes:
        if int(node.id) == int(node_id):
            return node

    raise ValueError(f"Nó não encontrado: {node_id}")


def _element_length(node_i, node_j) -> float:
    dx = float(node_j.x) - float(node_i.x)
    dy = float(node_j.y) - float(node_i.y)
    dz = float(node_j.z) - float(node_i.z)

    return math.sqrt(dx**2 + dy**2 + dz**2)
