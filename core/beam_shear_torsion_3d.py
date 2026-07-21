from __future__ import annotations

from typing import Any

from core.beam_design_3d import classify_element_3d


EPS = 1.0e-12


def create_beam_shear_torsion_report_3d(
    model,
    envelope: dict[str, Any],
) -> dict[str, Any]:
    """
    Cria relatório preliminar de cortante e torção em vigas 3D.

    Esta rotina NÃO dimensiona estribos.
    Ela apenas organiza os esforços críticos de Vy, Vz e T em elementos
    classificados como vigas.
    """

    records: list[dict[str, Any]] = []

    for element in getattr(model, "elements", []):
        classification = classify_element_3d(model, element)

        base_record = {
            "element": element.id,
            "node_i": element.node_i,
            "node_j": element.node_j,
            "classification": classification,
            "status": "ok",
            "section": _get_section_name(model, element),
        }

        if classification != "beam":
            records.append(
                {
                    **base_record,
                    "status": "not_considered",
                    "reason": "Elemento não classificado como viga nesta versão.",
                    "preliminary_index": 0.0,
                }
            )
            continue

        envelope_element = _get_envelope_element(envelope, element.id)

        if envelope_element is None:
            records.append(
                {
                    **base_record,
                    "status": "missing_envelope",
                    "reason": "Elemento não encontrado na envoltória 3D.",
                    "preliminary_index": 0.0,
                }
            )
            continue

        shear_y = _extract_group_abs(envelope_element, "shear_y")
        shear_z = _extract_group_abs(envelope_element, "shear_z")
        torsion = _extract_group_abs(envelope_element, "torsion")

        records.append(
            {
                **base_record,
                "shear_y_kN": shear_y["value"],
                "shear_y_abs_kN": shear_y["abs_value"],
                "shear_y_case": shear_y["case"],
                "shear_y_component": shear_y["component"],
                "shear_z_kN": shear_z["value"],
                "shear_z_abs_kN": shear_z["abs_value"],
                "shear_z_case": shear_z["case"],
                "shear_z_component": shear_z["component"],
                "torsion_kNm": torsion["value"],
                "torsion_abs_kNm": torsion["abs_value"],
                "torsion_case": torsion["case"],
                "torsion_component": torsion["component"],
                "reason": "",
                "preliminary_index": 0.0,
            }
        )

    _add_preliminary_indices(records)

    return {
        "analysis_type": "frame3d",
        "report_type": "preliminary_beam_shear_torsion_3d",
        "hypotheses": [
            "Relatório preliminar de esforços críticos em vigas 3D.",
            "Considera apenas elementos classificados como vigas.",
            "Vy, Vz e T são extraídos da envoltória 3D.",
            "Os esforços são apresentados no sistema local de cada barra.",
            "Esta rotina não dimensiona estribos nem armadura de torção.",
            "O índice preliminar é apenas uma triagem comparativa.",
        ],
        "elements": records,
        "global": _create_global_summary(records),
    }


def _add_preliminary_indices(records: list[dict[str, Any]]) -> None:
    valid_records = [record for record in records if record.get("status") == "ok"]

    max_vy = max(
        (float(record.get("shear_y_abs_kN", 0.0)) for record in valid_records),
        default=0.0,
    )
    max_vz = max(
        (float(record.get("shear_z_abs_kN", 0.0)) for record in valid_records),
        default=0.0,
    )
    max_t = max(
        (float(record.get("torsion_abs_kNm", 0.0)) for record in valid_records),
        default=0.0,
    )

    for record in records:
        if record.get("status") != "ok":
            record["preliminary_index"] = 0.0
            record["preliminary_index_terms"] = {
                "shear_y": 0.0,
                "shear_z": 0.0,
                "torsion": 0.0,
            }
            continue

        vy_term = _safe_ratio(float(record.get("shear_y_abs_kN", 0.0)), max_vy)
        vz_term = _safe_ratio(float(record.get("shear_z_abs_kN", 0.0)), max_vz)
        t_term = _safe_ratio(float(record.get("torsion_abs_kNm", 0.0)), max_t)

        record["preliminary_index_terms"] = {
            "shear_y": vy_term,
            "shear_z": vz_term,
            "torsion": t_term,
        }
        record["preliminary_index"] = vy_term + vz_term + t_term


def _safe_ratio(value: float, reference: float) -> float:
    if abs(reference) <= EPS:
        return 0.0

    return abs(value) / abs(reference)


def _create_global_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    beams = [record for record in records if record.get("classification") == "beam"]
    valid_records = [record for record in records if record.get("status") == "ok"]
    skipped = [record for record in records if record.get("classification") != "beam"]

    return {
        "number_of_beams": len(beams),
        "number_of_valid_beams": len(valid_records),
        "number_of_skipped_elements": len(skipped),
        "max_shear_y": _max_record(
            valid_records,
            value_key="shear_y_kN",
            abs_key="shear_y_abs_kN",
            case_key="shear_y_case",
            component_key="shear_y_component",
        ),
        "max_shear_z": _max_record(
            valid_records,
            value_key="shear_z_kN",
            abs_key="shear_z_abs_kN",
            case_key="shear_z_case",
            component_key="shear_z_component",
        ),
        "max_torsion": _max_record(
            valid_records,
            value_key="torsion_kNm",
            abs_key="torsion_abs_kNm",
            case_key="torsion_case",
            component_key="torsion_component",
        ),
        "max_preliminary_index": _max_index_record(valid_records),
    }


def _max_record(
    records: list[dict[str, Any]],
    value_key: str,
    abs_key: str,
    case_key: str,
    component_key: str,
) -> dict[str, Any] | None:
    if not records:
        return None

    critical = max(
        records,
        key=lambda item: float(item.get(abs_key, 0.0)),
    )

    return {
        "element": critical.get("element"),
        "node_i": critical.get("node_i"),
        "node_j": critical.get("node_j"),
        "value": float(critical.get(value_key, 0.0)),
        "abs_value": float(critical.get(abs_key, 0.0)),
        "case": critical.get(case_key, ""),
        "component": critical.get(component_key, ""),
    }


def _max_index_record(records: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not records:
        return None

    critical = max(
        records,
        key=lambda item: float(item.get("preliminary_index", 0.0)),
    )

    return {
        "element": critical.get("element"),
        "node_i": critical.get("node_i"),
        "node_j": critical.get("node_j"),
        "value": float(critical.get("preliminary_index", 0.0)),
        "terms": critical.get("preliminary_index_terms", {}),
        "shear_y_abs_kN": float(critical.get("shear_y_abs_kN", 0.0)),
        "shear_z_abs_kN": float(critical.get("shear_z_abs_kN", 0.0)),
        "torsion_abs_kNm": float(critical.get("torsion_abs_kNm", 0.0)),
    }


def _extract_group_abs(
    envelope_element: dict[str, Any],
    group_name: str,
) -> dict[str, Any]:
    group = envelope_element.get("groups", {}).get(group_name, {})
    record = group.get("abs", {})

    value = float(record.get("value", 0.0) or 0.0)

    return {
        "value": value,
        "abs_value": abs(value),
        "case": record.get("case", ""),
        "component": record.get("component", ""),
    }


def _get_envelope_element(
    envelope: dict[str, Any],
    element_id: int,
) -> dict[str, Any] | None:
    for element in envelope.get("elements", []):
        if int(element.get("id")) == int(element_id):
            return element

    return None


def _get_section_name(model, element) -> str:
    section_id = getattr(element, "section", None)

    for section in getattr(model, "sections", []):
        if int(getattr(section, "id")) == int(section_id):
            return str(getattr(section, "name", section_id))

    return str(section_id)
