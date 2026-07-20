from __future__ import annotations

import math
from typing import Any


DEFAULT_FYK_MPA = 500.0
DEFAULT_GAMMA_S = 1.15
DEFAULT_AS_MIN_RATIO = 0.0015
DEFAULT_AS_MAX_RATIO = 0.04


def design_frame3d_beams_preliminary(
    model,
    envelope: dict[str, Any],
    fyk_mpa: float = DEFAULT_FYK_MPA,
    gamma_s: float = DEFAULT_GAMMA_S,
    as_min_ratio: float = DEFAULT_AS_MIN_RATIO,
    as_max_ratio: float = DEFAULT_AS_MAX_RATIO,
) -> dict[str, Any]:
    """
    Dimensionamento preliminar de vigas 3D em concreto armado.

    Hipóteses desta versão:
    - usa a envoltória 3D já calculada;
    - dimensiona apenas elementos classificados como vigas;
    - elementos predominantemente verticais são tratados como pilares e ignorados;
    - dimensiona flexão simples separada para My e Mz;
    - não considera interação N + My + Mz;
    - não dimensiona cortante nem torção;
    - não substitui dimensionamento normativo completo.
    """

    fyd_kn_cm2 = _mpa_to_kn_cm2(fyk_mpa / gamma_s)

    records = []

    for element in model.elements:
        classification = classify_element_3d(model, element)

        if classification != "beam":
            records.append(
                {
                    "element": element.id,
                    "node_i": element.node_i,
                    "node_j": element.node_j,
                    "classification": classification,
                    "status": "not_designed",
                    "reason": "Elemento não classificado como viga nesta versão.",
                }
            )
            continue

        section = _get_section(model, element.section)
        b_m, h_m = _get_rectangular_section_dimensions(section)

        envelope_element = _get_envelope_element(envelope, element.id)

        if envelope_element is None:
            records.append(
                {
                    "element": element.id,
                    "node_i": element.node_i,
                    "node_j": element.node_j,
                    "classification": classification,
                    "status": "not_designed",
                    "reason": "Elemento não encontrado na envoltória 3D.",
                }
            )
            continue

        my_kNm = abs(_get_group_abs_value(envelope_element, "moment_y"))
        mz_kNm = abs(_get_group_abs_value(envelope_element, "moment_z"))

        # Convenção preliminar adotada:
        # - Mz usa a altura principal h da viga;
        # - My usa a dimensão transversal b como altura resistente secundária.
        design_mz = _design_flexural_axis(
            moment_kNm=mz_kNm,
            width_m=b_m,
            total_depth_m=h_m,
            fyd_kn_cm2=fyd_kn_cm2,
            as_min_ratio=as_min_ratio,
            as_max_ratio=as_max_ratio,
            axis="Mz",
        )

        design_my = _design_flexural_axis(
            moment_kNm=my_kNm,
            width_m=h_m,
            total_depth_m=b_m,
            fyd_kn_cm2=fyd_kn_cm2,
            as_min_ratio=as_min_ratio,
            as_max_ratio=as_max_ratio,
            axis="My",
        )

        critical_axis = "Mz"
        critical_as = design_mz["as_required_cm2"]

        if design_my["as_required_cm2"] > critical_as:
            critical_axis = "My"
            critical_as = design_my["as_required_cm2"]

        status = "ok"
        warnings = []

        if design_my["status"] != "ok":
            warnings.append(f"My: {design_my['status']}")

        if design_mz["status"] != "ok":
            warnings.append(f"Mz: {design_mz['status']}")

        if warnings:
            status = "warning"

        records.append(
            {
                "element": element.id,
                "node_i": element.node_i,
                "node_j": element.node_j,
                "classification": classification,
                "status": status,
                "section": getattr(section, "name", str(getattr(section, "id", ""))),
                "b_m": b_m,
                "h_m": h_m,
                "my_kNm": my_kNm,
                "mz_kNm": mz_kNm,
                "design_my": design_my,
                "design_mz": design_mz,
                "critical_axis": critical_axis,
                "as_required_cm2": critical_as,
                "warnings": warnings,
            }
        )

    return {
        "analysis_type": "frame3d",
        "design_type": "preliminary_reinforced_concrete_beam_design_3d",
        "fyk_mpa": fyk_mpa,
        "gamma_s": gamma_s,
        "fyd_kn_cm2": fyd_kn_cm2,
        "as_min_ratio": as_min_ratio,
        "as_max_ratio": as_max_ratio,
        "hypotheses": [
            "Dimensionamento preliminar por flexão simples separada.",
            "Mz dimensionado usando h como altura principal da seção.",
            "My dimensionado usando b como altura resistente secundária.",
            "Pilares e elementos verticais não são dimensionados nesta versão.",
            "Cortante, torção e interação N + My + Mz não são dimensionados nesta versão.",
        ],
        "elements": records,
        "global": _create_global_summary(records),
    }


def classify_element_3d(model, element) -> str:
    """
    Classifica elemento 3D de forma preliminar.

    - vertical: tratado como pilar;
    - não vertical: tratado como viga nesta versão.
    """

    node_i = _get_node(model, element.node_i)
    node_j = _get_node(model, element.node_j)

    dx = float(node_j.x) - float(node_i.x)
    dy = float(node_j.y) - float(node_i.y)
    dz = float(node_j.z) - float(node_i.z)

    horizontal_length = math.sqrt(dx**2 + dy**2)
    total_length = math.sqrt(dx**2 + dy**2 + dz**2)

    if total_length <= 0.0:
        return "invalid"

    vertical_ratio = abs(dz) / total_length
    horizontal_ratio = horizontal_length / total_length

    if vertical_ratio >= 0.80 and horizontal_ratio <= 0.30:
        return "column"

    return "beam"


def _design_flexural_axis(
    moment_kNm: float,
    width_m: float,
    total_depth_m: float,
    fyd_kn_cm2: float,
    as_min_ratio: float,
    as_max_ratio: float,
    axis: str,
) -> dict[str, Any]:
    """
    Dimensionamento preliminar por flexão simples.

    Fórmula simplificada:
        As = Msd / (fyd * z)

    com:
        z ≈ 0.9 d
        d ≈ 0.9 h
    """

    width_cm = 100.0 * width_m
    total_depth_cm = 100.0 * total_depth_m

    effective_depth_cm = 0.90 * total_depth_cm
    lever_arm_cm = 0.90 * effective_depth_cm

    area_concrete_cm2 = width_cm * total_depth_cm

    as_min_cm2 = as_min_ratio * area_concrete_cm2
    as_max_cm2 = as_max_ratio * area_concrete_cm2

    if moment_kNm <= 0.0:
        return {
            "axis": axis,
            "moment_kNm": moment_kNm,
            "width_cm": width_cm,
            "total_depth_cm": total_depth_cm,
            "effective_depth_cm": effective_depth_cm,
            "lever_arm_cm": lever_arm_cm,
            "as_calculated_cm2": 0.0,
            "as_min_cm2": as_min_cm2,
            "as_max_cm2": as_max_cm2,
            "as_required_cm2": as_min_cm2,
            "status": "minimum_reinforcement",
        }

    if lever_arm_cm <= 0.0 or fyd_kn_cm2 <= 0.0:
        return {
            "axis": axis,
            "moment_kNm": moment_kNm,
            "width_cm": width_cm,
            "total_depth_cm": total_depth_cm,
            "effective_depth_cm": effective_depth_cm,
            "lever_arm_cm": lever_arm_cm,
            "as_calculated_cm2": 0.0,
            "as_min_cm2": as_min_cm2,
            "as_max_cm2": as_max_cm2,
            "as_required_cm2": 0.0,
            "status": "invalid_geometry_or_material",
        }

    moment_kn_cm = 100.0 * moment_kNm
    as_calculated_cm2 = moment_kn_cm / (fyd_kn_cm2 * lever_arm_cm)
    as_required_cm2 = max(as_calculated_cm2, as_min_cm2)

    status = "ok"

    if as_required_cm2 > as_max_cm2:
        status = "above_preliminary_maximum"

    return {
        "axis": axis,
        "moment_kNm": moment_kNm,
        "width_cm": width_cm,
        "total_depth_cm": total_depth_cm,
        "effective_depth_cm": effective_depth_cm,
        "lever_arm_cm": lever_arm_cm,
        "as_calculated_cm2": as_calculated_cm2,
        "as_min_cm2": as_min_cm2,
        "as_max_cm2": as_max_cm2,
        "as_required_cm2": as_required_cm2,
        "status": status,
    }


def _create_global_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    designed = [
        record
        for record in records
        if record.get("classification") == "beam"
        and record.get("status") in {"ok", "warning"}
    ]

    skipped = [
        record
        for record in records
        if record.get("classification") != "beam"
    ]

    if not designed:
        return {
            "number_of_designed_beams": 0,
            "number_of_skipped_elements": len(skipped),
            "critical_element": None,
        }

    critical = max(
        designed,
        key=lambda item: float(item.get("as_required_cm2", 0.0)),
    )

    return {
        "number_of_designed_beams": len(designed),
        "number_of_skipped_elements": len(skipped),
        "critical_element": {
            "element": critical["element"],
            "node_i": critical["node_i"],
            "node_j": critical["node_j"],
            "critical_axis": critical["critical_axis"],
            "as_required_cm2": critical["as_required_cm2"],
            "my_kNm": critical["my_kNm"],
            "mz_kNm": critical["mz_kNm"],
        },
    }


def _get_group_abs_value(envelope_element: dict[str, Any], group_name: str) -> float:
    group = envelope_element.get("groups", {}).get(group_name, {})
    abs_record = group.get("abs", {})

    return float(abs_record.get("value", 0.0))


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


def _get_section(model, section_id: int):
    if hasattr(model, "section_by_id"):
        return model.section_by_id(section_id)

    if hasattr(model, "get_section"):
        return model.get_section(section_id)

    for section in model.sections:
        if int(section.id) == int(section_id):
            return section

    raise ValueError(f"Seção não encontrada: {section_id}")


def _get_rectangular_section_dimensions(section) -> tuple[float, float]:
    """
    Retorna b,h em metros.

    Estratégia:
    1. usa atributos b,h se existirem;
    2. estima a partir de A e Iz, assumindo seção retangular:
       A = b h
       Iz = b h³ / 12
       h = sqrt(12 Iz / A)
    """

    b = getattr(section, "b", None)
    h = getattr(section, "h", None)

    if b is not None and h is not None:
        return float(b), float(h)

    area = float(getattr(section, "A", 0.0))
    iz = getattr(section, "Iz", None)

    if iz is None:
        iz = getattr(section, "I", None)

    if area > 0.0 and iz is not None and float(iz) > 0.0:
        h_estimated = math.sqrt(12.0 * float(iz) / area)
        b_estimated = area / h_estimated
        return b_estimated, h_estimated

    raise ValueError(
        f"Não foi possível obter dimensões retangulares da seção {getattr(section, 'id', '')}."
    )


def _mpa_to_kn_cm2(value_mpa: float) -> float:
    """
    Converte MPa para kN/cm².

    1 MPa = 1 N/mm² = 0.1 kN/cm²
    """

    return 0.1 * value_mpa
