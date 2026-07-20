# core/result_accessors.py

from __future__ import annotations

from typing import Any


def get_analysis_type(results: dict[str, Any]) -> str:
    """
    Retorna o tipo de análise.

    Resultados antigos 2D não possuem analysis_type na raiz,
    então o padrão é frame2d.
    """

    return str(results.get("analysis_type", "frame2d"))


def is_frame2d_results(results: dict[str, Any]) -> bool:
    return get_analysis_type(results) == "frame2d"


def is_frame3d_results(results: dict[str, Any]) -> bool:
    return get_analysis_type(results) == "frame3d"


def get_translation_keys(results: dict[str, Any]) -> tuple[str, ...]:
    if is_frame3d_results(results):
        return ("ux", "uy", "uz")

    return ("ux", "uy")


def get_rotation_keys(results: dict[str, Any]) -> tuple[str, ...]:
    if is_frame3d_results(results):
        return ("rx", "ry", "rz")

    return ("rz",)


def find_max_abs_nodal_value(
    rows: list[dict[str, Any]],
    keys: tuple[str, ...],
) -> dict[str, Any] | None:
    """
    Procura o maior valor absoluto em uma lista de resultados nodais.
    """

    best: dict[str, Any] | None = None

    for row in rows:
        for key in keys:
            value = float(row.get(key, 0.0))

            candidate = {
                "node": row.get("node"),
                "key": key,
                "value": value,
                "abs_value": abs(value),
            }

            if best is None or candidate["abs_value"] > best["abs_value"]:
                best = candidate

    return best


def get_max_translation(results: dict[str, Any]) -> dict[str, Any] | None:
    """
    Retorna o maior deslocamento translacional nodal.
    """

    return find_max_abs_nodal_value(
        rows=results.get("displacements", []),
        keys=get_translation_keys(results),
    )


def get_max_rotation(results: dict[str, Any]) -> dict[str, Any] | None:
    """
    Retorna a maior rotação nodal.
    """

    return find_max_abs_nodal_value(
        rows=results.get("displacements", []),
        keys=get_rotation_keys(results),
    )


def get_element_force_groups(results: dict[str, Any]) -> dict[str, tuple[str, ...]]:
    """
    Retorna os grupos de esforços disponíveis conforme o tipo de análise.
    """

    if is_frame3d_results(results):
        return {
            "normal": ("normal_i", "normal_j"),
            "shear_y": ("shear_y_i", "shear_y_j"),
            "shear_z": ("shear_z_i", "shear_z_j"),
            "torsion": ("torsion_i", "torsion_j"),
            "moment_y": ("moment_y_i", "moment_y_j"),
            "moment_z": ("moment_z_i", "moment_z_j"),
        }

    return {
        "normal": ("normal_i", "normal_j"),
        "shear": ("shear_i", "shear_j"),
        "moment": ("moment_i", "moment_j"),
    }


def find_max_abs_element_force(
    elements: list[dict[str, Any]],
    keys: tuple[str, ...],
) -> dict[str, Any] | None:
    """
    Procura o maior valor absoluto de um grupo de esforços de elemento.
    """

    best: dict[str, Any] | None = None

    for element in elements:
        local_end_forces = element.get("local_end_forces", {})

        for key in keys:
            value = float(local_end_forces.get(key, 0.0))

            candidate = {
                "element": element.get("id"),
                "key": key,
                "value": value,
                "abs_value": abs(value),
            }

            if best is None or candidate["abs_value"] > best["abs_value"]:
                best = candidate

    return best


def get_max_element_forces(results: dict[str, Any]) -> dict[str, dict[str, Any] | None]:
    """
    Retorna os esforços máximos por grupo.

    Para frame2d:
    - normal
    - shear
    - moment

    Para frame3d:
    - normal
    - shear_y
    - shear_z
    - torsion
    - moment_y
    - moment_z
    """

    elements = results.get("elements", [])
    groups = get_element_force_groups(results)

    return {
        group_name: find_max_abs_element_force(elements, keys)
        for group_name, keys in groups.items()
    }


def get_equilibrium_status(results: dict[str, Any]) -> str | None:
    """
    Retorna o status de equilíbrio, quando disponível.

    frame3d:
    - usa results["equilibrium"]["status"]

    frame2d:
    - usa results["summary"]["global_equilibrium"]["is_equilibrated"]
    """

    equilibrium = results.get("equilibrium")

    if isinstance(equilibrium, dict):
        status = equilibrium.get("status")

        if status is not None:
            return str(status)

    summary = results.get("summary")

    if isinstance(summary, dict):
        global_equilibrium = summary.get("global_equilibrium")

        if isinstance(global_equilibrium, dict):
            is_equilibrated = global_equilibrium.get("is_equilibrated")

            if is_equilibrated is True:
                return "OK"

            if is_equilibrated is False:
                return "NOT_OK"

    return None


def create_common_result_summary(results: dict[str, Any]) -> dict[str, Any]:
    """
    Cria um resumo comum para resultados 2D e 3D.

    Esta função é a base para módulos futuros como:
    - flecha;
    - fissuração;
    - envoltória 3D;
    - dimensionamento;
    - relatórios unificados.
    """

    return {
        "model_name": results.get("model_name"),
        "analysis_type": get_analysis_type(results),
        "number_of_nodes": results.get("number_of_nodes"),
        "number_of_elements": results.get("number_of_elements"),
        "number_of_dofs": results.get("number_of_dofs"),
        "max_translation": get_max_translation(results),
        "max_rotation": get_max_rotation(results),
        "max_element_forces": get_max_element_forces(results),
        "equilibrium_status": get_equilibrium_status(results),
    }
