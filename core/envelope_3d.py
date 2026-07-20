from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


FRAME3D_FORCE_COMPONENTS = (
    "normal_i",
    "normal_j",
    "shear_y_i",
    "shear_y_j",
    "shear_z_i",
    "shear_z_j",
    "torsion_i",
    "torsion_j",
    "moment_y_i",
    "moment_y_j",
    "moment_z_i",
    "moment_z_j",
)


FRAME3D_FORCE_GROUPS = {
    "normal": ("normal_i", "normal_j"),
    "shear_y": ("shear_y_i", "shear_y_j"),
    "shear_z": ("shear_z_i", "shear_z_j"),
    "torsion": ("torsion_i", "torsion_j"),
    "moment_y": ("moment_y_i", "moment_y_j"),
    "moment_z": ("moment_z_i", "moment_z_j"),
}


def create_envelope_3d(results_by_case: Mapping[str, dict[str, Any]]) -> dict[str, Any]:
    """
    Cria envoltória 3D a partir de um conjunto de resultados frame3d.

    Entrada esperada:
        {
            "CASO_1": results_1,
            "CASO_2": results_2,
            ...
        }

    Funciona também com análise única:
        {
            "ANALISE_UNICA": results
        }
    """

    if not results_by_case:
        raise ValueError("Nenhum resultado fornecido para a envoltória 3D.")

    case_names = list(results_by_case.keys())

    element_ids = sorted(_collect_element_ids(results_by_case))

    elements = []
    for element_id in element_ids:
        elements.append(
            _create_element_envelope(
                element_id=element_id,
                results_by_case=results_by_case,
            )
        )

    envelope = {
        "analysis_type": "frame3d",
        "number_of_cases": len(case_names),
        "cases": case_names,
        "force_components": list(FRAME3D_FORCE_COMPONENTS),
        "force_groups": {
            key: list(value)
            for key, value in FRAME3D_FORCE_GROUPS.items()
        },
        "elements": elements,
        "global": _create_global_envelope(elements),
    }

    return envelope


def save_envelope_3d_json(envelope: dict[str, Any], output_path: str | Path) -> None:
    """
    Salva a envoltória 3D em JSON.
    """

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(envelope, file, indent=4, ensure_ascii=False)


def _collect_element_ids(results_by_case: Mapping[str, dict[str, Any]]) -> set[int]:
    element_ids: set[int] = set()

    for results in results_by_case.values():
        for element in results.get("elements", []):
            element_ids.add(int(element["id"]))

    return element_ids


def _create_element_envelope(
    element_id: int,
    results_by_case: Mapping[str, dict[str, Any]],
) -> dict[str, Any]:
    reference_element = _find_first_element(results_by_case, element_id)

    component_envelopes = {}
    for component in FRAME3D_FORCE_COMPONENTS:
        records = _collect_component_records(
            element_id=element_id,
            component=component,
            results_by_case=results_by_case,
        )

        if records:
            component_envelopes[component] = _summarize_records(records)

    group_envelopes = {}
    for group_name, components in FRAME3D_FORCE_GROUPS.items():
        records = []

        for component in components:
            records.extend(
                _collect_component_records(
                    element_id=element_id,
                    component=component,
                    results_by_case=results_by_case,
                )
            )

        if records:
            group_envelopes[group_name] = _summarize_records(records)

    return {
        "id": element_id,
        "node_i": reference_element.get("node_i"),
        "node_j": reference_element.get("node_j"),
        "length": reference_element.get("length"),
        "components": component_envelopes,
        "groups": group_envelopes,
    }


def _find_first_element(
    results_by_case: Mapping[str, dict[str, Any]],
    element_id: int,
) -> dict[str, Any]:
    for results in results_by_case.values():
        for element in results.get("elements", []):
            if int(element["id"]) == element_id:
                return element

    raise ValueError(f"Elemento {element_id} não encontrado nos resultados.")


def _collect_component_records(
    element_id: int,
    component: str,
    results_by_case: Mapping[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    records = []

    for case_name, results in results_by_case.items():
        element = _find_element_in_results(results, element_id)
        if element is None:
            continue

        local_end_forces = element.get("local_end_forces", {})
        if component not in local_end_forces:
            continue

        value = float(local_end_forces[component])

        records.append(
            {
                "case": case_name,
                "element": element_id,
                "component": component,
                "value": value,
            }
        )

    return records


def _find_element_in_results(
    results: dict[str, Any],
    element_id: int,
) -> dict[str, Any] | None:
    for element in results.get("elements", []):
        if int(element["id"]) == element_id:
            return element

    return None


def _summarize_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    min_record = min(records, key=lambda item: item["value"])
    max_record = max(records, key=lambda item: item["value"])
    abs_record = max(records, key=lambda item: abs(item["value"]))

    return {
        "min": dict(min_record),
        "max": dict(max_record),
        "abs": dict(abs_record),
    }


def _create_global_envelope(elements: list[dict[str, Any]]) -> dict[str, Any]:
    global_envelope = {}

    for group_name in FRAME3D_FORCE_GROUPS:
        records = []

        for element in elements:
            group = element.get("groups", {}).get(group_name)
            if not group:
                continue

            records.extend(
                [
                    group["min"],
                    group["max"],
                    group["abs"],
                ]
            )

        if records:
            global_envelope[group_name] = _summarize_records(records)

    return global_envelope
