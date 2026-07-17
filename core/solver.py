# core/solver.py

from __future__ import annotations

import numpy as np

from core.model import StructuralModel, Element, DistributedLoad


def solve_structure(model: StructuralModel) -> dict:
    """Resolve uma estrutura de pórtico plano 2D pelo método da rigidez direta."""

    K = assemble_global_stiffness(model)
    F = assemble_global_load_vector(model)

    free_dofs = model.free_dofs()
    restrained_dofs = model.restrained_dofs()

    if len(free_dofs) == 0:
        raise ValueError("O modelo não possui graus de liberdade livres.")

    K_ff = K[np.ix_(free_dofs, free_dofs)]
    F_f = F[free_dofs]

    d = np.zeros(model.number_of_dofs())

    try:
        d_f = np.linalg.solve(K_ff, F_f)
    except np.linalg.LinAlgError as error:
        raise ValueError(
            "Não foi possível resolver o sistema estrutural. "
            "A matriz de rigidez pode estar singular. "
            "Verifique apoios, vínculos e estabilidade da estrutura."
        ) from error

    d[free_dofs] = d_f
    reactions = K @ d - F
    element_results = calculate_element_results(model, d)

    return {
        "model_name": model.name,
        "number_of_nodes": len(model.nodes),
        "number_of_elements": len(model.elements),
        "number_of_dofs": model.number_of_dofs(),
        "free_dofs": free_dofs,
        "restrained_dofs": restrained_dofs,
        "displacements": format_nodal_displacements(model, d),
        "reactions": format_support_reactions(model, reactions),
        "elements": element_results,
        "global_displacement_vector": d,
        "global_reaction_vector": reactions,
    }


# ==========================================================
# MATRIZ DE RIGIDEZ GLOBAL
# ==========================================================

def assemble_global_stiffness(model: StructuralModel) -> np.ndarray:
    """Monta a matriz de rigidez global da estrutura."""

    n_dofs = model.number_of_dofs()
    K = np.zeros((n_dofs, n_dofs), dtype=float)

    for element in model.elements:
        k_global = element_global_stiffness(model, element)
        element_dofs = model.element_dofs(element)

        for local_i, global_i in enumerate(element_dofs):
            for local_j, global_j in enumerate(element_dofs):
                K[global_i, global_j] += k_global[local_i, local_j]

    return K


def element_global_stiffness(model: StructuralModel, element: Element) -> np.ndarray:
    """Calcula a matriz de rigidez do elemento no sistema global."""

    k_local = element_local_stiffness(model, element)
    T = transformation_matrix(model, element)

    return T.T @ k_local @ T


def element_local_stiffness(model: StructuralModel, element: Element) -> np.ndarray:
    """Matriz de rigidez local de um elemento de pórtico plano 2D."""

    _, _, L, _, _ = element.geometry(model)

    material = model.get_material(element.material)
    section = model.get_section(element.section)

    E = material.E
    A = section.A
    I = section.I

    EA_L = E * A / L
    EI = E * I

    k = np.array(
        [
            [ EA_L,          0.0,          0.0, -EA_L,          0.0,          0.0],
            [  0.0,  12*EI/L**3,   6*EI/L**2,   0.0, -12*EI/L**3,   6*EI/L**2],
            [  0.0,   6*EI/L**2,    4*EI/L,    0.0,  -6*EI/L**2,    2*EI/L],
            [-EA_L,          0.0,          0.0,  EA_L,          0.0,          0.0],
            [  0.0, -12*EI/L**3,  -6*EI/L**2,   0.0,  12*EI/L**3,  -6*EI/L**2],
            [  0.0,   6*EI/L**2,    2*EI/L,    0.0,  -6*EI/L**2,    4*EI/L],
        ],
        dtype=float,
    )

    return k


def transformation_matrix(model: StructuralModel, element: Element) -> np.ndarray:
    """Matriz que transforma deslocamentos globais em deslocamentos locais."""

    _, _, _, c, s = element.geometry(model)

    T = np.array(
        [
            [ c,  s, 0.0, 0.0, 0.0, 0.0],
            [-s,  c, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0,  c,  s, 0.0],
            [0.0, 0.0, 0.0, -s,  c, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
        ],
        dtype=float,
    )

    return T


# ==========================================================
# VETOR DE CARGAS GLOBAL
# ==========================================================

def assemble_global_load_vector(model: StructuralModel) -> np.ndarray:
    """Monta o vetor global de cargas."""

    F = np.zeros(model.number_of_dofs(), dtype=float)
    dofs = model.dof_map()

    for load in model.nodal_loads:
        ux, uy, rz = dofs[load.node]
        F[ux] += load.fx
        F[uy] += load.fy
        F[rz] += load.mz

    for load in model.distributed_loads:
        element = model.get_element(load.element)
        element_dofs = model.element_dofs(element)
        f_eq_global = equivalent_nodal_load_global(model, element, load)

        for local_i, global_i in enumerate(element_dofs):
            F[global_i] += f_eq_global[local_i]

    return F


def equivalent_nodal_load_global(
    model: StructuralModel,
    element: Element,
    load: DistributedLoad,
) -> np.ndarray:
    """Converte uma carga distribuída uniforme local em carga nodal equivalente global."""

    _, _, L, _, _ = element.geometry(model)

    qx = load.qx
    qy = load.qy

    f_local = np.array(
        [
            qx * L / 2.0,
            qy * L / 2.0,
            qy * L**2 / 12.0,
            qx * L / 2.0,
            qy * L / 2.0,
            -qy * L**2 / 12.0,
        ],
        dtype=float,
    )

    T = transformation_matrix(model, element)
    return T.T @ f_local


def equivalent_nodal_load_local(model: StructuralModel, element: Element) -> np.ndarray:
    """Soma as cargas distribuídas equivalentes locais de um elemento."""

    f_total = np.zeros(6, dtype=float)

    for load in model.distributed_loads:
        if load.element != element.id:
            continue

        _, _, L, _, _ = element.geometry(model)
        qx = load.qx
        qy = load.qy

        f_local = np.array(
            [
                qx * L / 2.0,
                qy * L / 2.0,
                qy * L**2 / 12.0,
                qx * L / 2.0,
                qy * L / 2.0,
                -qy * L**2 / 12.0,
            ],
            dtype=float,
        )

        f_total += f_local

    return f_total


# ==========================================================
# RESULTADOS
# ==========================================================

def calculate_element_results(model: StructuralModel, global_displacements: np.ndarray) -> list[dict]:
    """Calcula deslocamentos locais e esforços locais finais de cada elemento."""

    results: list[dict] = []

    for element in model.elements:
        element_dofs = model.element_dofs(element)
        d_global_element = global_displacements[element_dofs]

        T = transformation_matrix(model, element)
        k_local = element_local_stiffness(model, element)

        d_local = T @ d_global_element
        f_equiv_local = equivalent_nodal_load_local(model, element)
        f_local = k_local @ d_local - f_equiv_local

        _, _, L, c, s = element.geometry(model)

        results.append(
            {
                "id": element.id,
                "node_i": element.node_i,
                "node_j": element.node_j,
                "length": L,
                "cos": c,
                "sin": s,
                "local_displacements": {
                    "u_i": d_local[0],
                    "v_i": d_local[1],
                    "rz_i": d_local[2],
                    "u_j": d_local[3],
                    "v_j": d_local[4],
                    "rz_j": d_local[5],
                },
                "local_end_forces": {
                    "normal_i": f_local[0],
                    "shear_i": f_local[1],
                    "moment_i": f_local[2],
                    "normal_j": f_local[3],
                    "shear_j": f_local[4],
                    "moment_j": f_local[5],
                },
            }
        )

    return results


def format_nodal_displacements(model: StructuralModel, global_displacements: np.ndarray) -> list[dict]:
    """Organiza os deslocamentos por nó."""

    dofs = model.dof_map()
    output: list[dict] = []

    for node_id in model.sorted_node_ids():
        ux, uy, rz = dofs[node_id]
        node = model.get_node(node_id)

        output.append(
            {
                "node": node_id,
                "x": node.x,
                "y": node.y,
                "ux": global_displacements[ux],
                "uy": global_displacements[uy],
                "rz": global_displacements[rz],
            }
        )

    return output


def format_support_reactions(model: StructuralModel, reactions: np.ndarray) -> list[dict]:
    """Organiza as reações apenas nos nós que possuem apoio."""

    dofs = model.dof_map()
    output: list[dict] = []

    for support in model.supports:
        ux, uy, rz = dofs[support.node]

        output.append(
            {
                "node": support.node,
                "rx": reactions[ux] if support.ux else 0.0,
                "ry": reactions[uy] if support.uy else 0.0,
                "mz": reactions[rz] if support.rz else 0.0,
            }
        )

    return output
