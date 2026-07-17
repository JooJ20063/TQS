# core/postprocess.py

from __future__ import annotations

from typing import Any
import math

from core.model import StructuralModel


def enrich_results(model: StructuralModel, results: dict[str, Any]) -> dict[str, Any]:
    """Adiciona resumo técnico aos resultados vindos do solver."""

    enriched = dict(results)
    enriched["summary"] = {
        "model_classification": classify_model(model),
        "max_displacements": calculate_max_displacements(results),
        "max_element_forces": calculate_max_element_forces(results),
        "global_equilibrium": check_global_equilibrium(model, results),
    }
    return enriched


def classify_model(model: StructuralModel) -> dict[str, Any]:
    horizontal_elements = 0
    vertical_elements = 0
    inclined_elements = 0

    for element in model.elements:
        _, _, _, c, s = element.geometry(model)

        if abs(s) < 1e-9:
            horizontal_elements += 1
        elif abs(c) < 1e-9:
            vertical_elements += 1
        else:
            inclined_elements += 1

    if vertical_elements == 0 and inclined_elements == 0:
        structure_type = "viga_plana"
    elif horizontal_elements > 0 and vertical_elements > 0:
        structure_type = "portico_plano"
    elif inclined_elements > 0:
        structure_type = "estrutura_com_barras_inclinadas"
    else:
        structure_type = "estrutura_2d"

    return {
        "structure_type": structure_type,
        "nodes": len(model.nodes),
        "elements": len(model.elements),
        "supports": len(model.supports),
        "horizontal_elements": horizontal_elements,
        "vertical_elements": vertical_elements,
        "inclined_elements": inclined_elements,
    }


def calculate_max_displacements(results: dict[str, Any]) -> dict[str, Any]:
    displacements = results["displacements"]

    max_abs_ux = max(displacements, key=lambda item: abs(item["ux"]))
    max_abs_uy = max(displacements, key=lambda item: abs(item["uy"]))
    max_abs_rz = max(displacements, key=lambda item: abs(item["rz"]))

    max_total_translation = max(
        displacements,
        key=lambda item: math.sqrt(item["ux"] ** 2 + item["uy"] ** 2),
    )

    return {
        "max_abs_ux": {"node": max_abs_ux["node"], "value_m": max_abs_ux["ux"]},
        "max_abs_uy": {"node": max_abs_uy["node"], "value_m": max_abs_uy["uy"]},
        "max_abs_rz": {"node": max_abs_rz["node"], "value_rad": max_abs_rz["rz"]},
        "max_total_translation": {
            "node": max_total_translation["node"],
            "value_m": math.sqrt(max_total_translation["ux"] ** 2 + max_total_translation["uy"] ** 2),
        },
    }


def calculate_max_element_forces(results: dict[str, Any]) -> dict[str, Any]:
    max_normal = {"element": None, "position": None, "value": 0.0}
    max_shear = {"element": None, "position": None, "value": 0.0}
    max_moment = {"element": None, "position": None, "value": 0.0}

    for element in results["elements"]:
        element_id = element["id"]
        forces = element["local_end_forces"]

        for position, value in [("i", forces["normal_i"]), ("j", forces["normal_j"])]:
            if abs(value) > abs(max_normal["value"]):
                max_normal = {"element": element_id, "position": position, "value": value}

        for position, value in [("i", forces["shear_i"]), ("j", forces["shear_j"])]:
            if abs(value) > abs(max_shear["value"]):
                max_shear = {"element": element_id, "position": position, "value": value}

        for position, value in [("i", forces["moment_i"]), ("j", forces["moment_j"])]:
            if abs(value) > abs(max_moment["value"]):
                max_moment = {"element": element_id, "position": position, "value": value}

    return {
        "max_abs_normal_kN": max_normal,
        "max_abs_shear_kN": max_shear,
        "max_abs_moment_kNm": max_moment,
    }


def check_global_equilibrium(model: StructuralModel, results: dict[str, Any]) -> dict[str, Any]:
    loads = calculate_external_load_resultants(model)
    reactions = calculate_reaction_resultants(model, results)

    imbalance_fx = loads["fx"] + reactions["fx"]
    imbalance_fy = loads["fy"] + reactions["fy"]
    imbalance_mz = loads["mz"] + reactions["mz"]

    tolerance = 1e-6
    is_ok = abs(imbalance_fx) < tolerance and abs(imbalance_fy) < tolerance and abs(imbalance_mz) < tolerance

    return {
        "loads": loads,
        "reactions": reactions,
        "imbalance": {"fx": imbalance_fx, "fy": imbalance_fy, "mz": imbalance_mz},
        "tolerance": tolerance,
        "is_equilibrated": is_ok,
    }


def calculate_external_load_resultants(model: StructuralModel) -> dict[str, float]:
    total_fx = 0.0
    total_fy = 0.0
    total_mz = 0.0

    for load in model.nodal_loads:
        node = model.get_node(load.node)
        total_fx += load.fx
        total_fy += load.fy
        total_mz += load.mz + node.x * load.fy - node.y * load.fx

    for load in model.distributed_loads:
        element = model.get_element(load.element)
        node_i = model.get_node(element.node_i)
        node_j = model.get_node(element.node_j)
        _, _, length, c, s = element.geometry(model)

        fx_local = load.qx * length
        fy_local = load.qy * length

        fx_global = c * fx_local - s * fy_local
        fy_global = s * fx_local + c * fy_local

        x_mid = 0.5 * (node_i.x + node_j.x)
        y_mid = 0.5 * (node_i.y + node_j.y)

        total_fx += fx_global
        total_fy += fy_global
        total_mz += x_mid * fy_global - y_mid * fx_global

    return {"fx": total_fx, "fy": total_fy, "mz": total_mz}


def calculate_reaction_resultants(model: StructuralModel, results: dict[str, Any]) -> dict[str, float]:
    reaction_vector = results["global_reaction_vector"]
    dofs = model.dof_map()

    total_fx = 0.0
    total_fy = 0.0
    total_mz = 0.0

    for node_id in model.sorted_node_ids():
        node = model.get_node(node_id)
        ux, uy, rz = dofs[node_id]

        rx = reaction_vector[ux]
        ry = reaction_vector[uy]
        mz = reaction_vector[rz]

        total_fx += rx
        total_fy += ry
        total_mz += mz + node.x * ry - node.y * rx

    return {"fx": total_fx, "fy": total_fy, "mz": total_mz}


def print_analysis_summary(results: dict[str, Any]) -> None:
    summary = results["summary"]
    classification = summary["model_classification"]
    displacements = summary["max_displacements"]
    forces = summary["max_element_forces"]
    equilibrium = summary["global_equilibrium"]

    print()
    print("-" * 60)
    print("Resumo da análise")
    print("-" * 60)
    print(f"Tipo de estrutura: {classification['structure_type']}")
    print(f"Nós:               {classification['nodes']}")
    print(f"Elementos:         {classification['elements']}")
    print()
    print("Deslocamentos máximos:")
    print(f"  |ux|max = {displacements['max_abs_ux']['value_m']:.6e} m no nó {displacements['max_abs_ux']['node']}")
    print(f"  |uy|max = {displacements['max_abs_uy']['value_m']:.6e} m no nó {displacements['max_abs_uy']['node']}")
    print(f"  |rz|max = {displacements['max_abs_rz']['value_rad']:.6e} rad no nó {displacements['max_abs_rz']['node']}")
    print()
    print("Esforços máximos de ponta:")
    print(f"  |N|max = {forces['max_abs_normal_kN']['value']:.6e} kN no elemento {forces['max_abs_normal_kN']['element']}")
    print(f"  |V|max = {forces['max_abs_shear_kN']['value']:.6e} kN no elemento {forces['max_abs_shear_kN']['element']}")
    print(f"  |M|max = {forces['max_abs_moment_kNm']['value']:.6e} kN.m no elemento {forces['max_abs_moment_kNm']['element']}")
    print()
    print("Equilíbrio global:")
    print(f"  ΣFx = {equilibrium['imbalance']['fx']:.6e}")
    print(f"  ΣFy = {equilibrium['imbalance']['fy']:.6e}")
    print(f"  ΣMz = {equilibrium['imbalance']['mz']:.6e}")
    print("  Status: OK" if equilibrium["is_equilibrated"] else "  Status: verificar equilíbrio")
