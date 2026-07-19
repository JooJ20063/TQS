from __future__ import annotations

import numpy as np

from core.model import StructuralModel, Element


def solve_structure_3d(model: StructuralModel) -> dict:
    """
    Resolve uma estrutura de pórtico espacial 3D.

    Observação:
    Este solver ainda está em implementação.
    """

    if model.analysis_type != "frame3d":
        raise ValueError(
            "solve_structure_3d deve ser usado apenas com analysis_type='frame3d'."
        )

    raise NotImplementedError(
        "Solver 3D ainda não implementado. "
        "Este arquivo prepara o núcleo para o próximo passo."
    )


def assemble_global_stiffness_3d(model: StructuralModel) -> np.ndarray:
    """
    Monta a matriz de rigidez global 3D.
    """

    if model.analysis_type != "frame3d":
        raise ValueError(
            "assemble_global_stiffness_3d deve ser usado apenas com analysis_type='frame3d'."
        )

    n_dofs = model.number_of_dofs()
    K = np.zeros((n_dofs, n_dofs), dtype=float)

    for element in model.elements:
        k_global = element_global_stiffness_3d(model, element)
        element_dofs = model.element_dofs(element)

        for local_i, global_i in enumerate(element_dofs):
            for local_j, global_j in enumerate(element_dofs):
                K[global_i, global_j] += k_global[local_i, local_j]

    return K

def element_global_stiffness_3d(
    model: StructuralModel,
    element: Element,
) -> np.ndarray:
    """
    Calcula a matriz de rigidez do elemento 3D no sistema global.
    """

    k_local = element_local_stiffness_3d(model, element)
    T = transformation_matrix_3d(model, element)

    return T.T @ k_local @ T

def element_local_stiffness_3d(
    model: StructuralModel,
    element: Element,
) -> np.ndarray:
    """
    Matriz de rigidez local 12x12 de um elemento de pórtico espacial.

    Ordem local dos graus de liberdade:
    [u, v, w, rx, ry, rz] no nó i
    [u, v, w, rx, ry, rz] no nó j

    Convenções:
    - u: deslocamento axial local x
    - v: deslocamento transversal local y
    - w: deslocamento transversal local z
    - rx: torção em torno do eixo local x
    - ry: rotação em torno do eixo local y
    - rz: rotação em torno do eixo local z
    """

    _, _, _, L, _, _, _ = element.geometry_3d(model)

    material = model.get_material(element.material)
    section = model.get_section(element.section)

    E = float(material.E)
    G = get_material_shear_modulus(material)

    A = float(section.A)
    Iy = get_section_property(section, "Iy", fallback=section.I)
    Iz = get_section_property(section, "Iz", fallback=section.I)
    J = get_section_property(section, "J", fallback=Iy + Iz)

    EA_L = E * A / L
    GJ_L = G * J / L

    EIy = E * Iy
    EIz = E * Iz

    k = np.zeros((12, 12), dtype=float)

    # ----------------------------------------------------------
    # Axial: u_i, u_j
    # ----------------------------------------------------------
    k[0, 0] = EA_L
    k[0, 6] = -EA_L
    k[6, 0] = -EA_L
    k[6, 6] = EA_L

    # ----------------------------------------------------------
    # Torção: rx_i, rx_j
    # ----------------------------------------------------------
    k[3, 3] = GJ_L
    k[3, 9] = -GJ_L
    k[9, 3] = -GJ_L
    k[9, 9] = GJ_L

    # ----------------------------------------------------------
    # Flexão em torno do eixo local z
    # Atua no plano local x-y: v e rz
    # DOFs: v_i, rz_i, v_j, rz_j = 1, 5, 7, 11
    # ----------------------------------------------------------
    k[1, 1] = 12.0 * EIz / L**3
    k[1, 5] = 6.0 * EIz / L**2
    k[1, 7] = -12.0 * EIz / L**3
    k[1, 11] = 6.0 * EIz / L**2

    k[5, 1] = 6.0 * EIz / L**2
    k[5, 5] = 4.0 * EIz / L
    k[5, 7] = -6.0 * EIz / L**2
    k[5, 11] = 2.0 * EIz / L

    k[7, 1] = -12.0 * EIz / L**3
    k[7, 5] = -6.0 * EIz / L**2
    k[7, 7] = 12.0 * EIz / L**3
    k[7, 11] = -6.0 * EIz / L**2

    k[11, 1] = 6.0 * EIz / L**2
    k[11, 5] = 2.0 * EIz / L
    k[11, 7] = -6.0 * EIz / L**2
    k[11, 11] = 4.0 * EIz / L

    # ----------------------------------------------------------
    # Flexão em torno do eixo local y
    # Atua no plano local x-z: w e ry
    # DOFs: w_i, ry_i, w_j, ry_j = 2, 4, 8, 10
    # ----------------------------------------------------------
    k[2, 2] = 12.0 * EIy / L**3
    k[2, 4] = -6.0 * EIy / L**2
    k[2, 8] = -12.0 * EIy / L**3
    k[2, 10] = -6.0 * EIy / L**2

    k[4, 2] = -6.0 * EIy / L**2
    k[4, 4] = 4.0 * EIy / L
    k[4, 8] = 6.0 * EIy / L**2
    k[4, 10] = 2.0 * EIy / L

    k[8, 2] = -12.0 * EIy / L**3
    k[8, 4] = 6.0 * EIy / L**2
    k[8, 8] = 12.0 * EIy / L**3
    k[8, 10] = 6.0 * EIy / L**2

    k[10, 2] = -6.0 * EIy / L**2
    k[10, 4] = 2.0 * EIy / L
    k[10, 8] = 6.0 * EIy / L**2
    k[10, 10] = 4.0 * EIy / L

    return k

def get_material_shear_modulus(material) -> float:
    """
    Retorna o módulo de cisalhamento G do material.

    Prioridade:
    1. usa material.G, se existir;
    2. calcula por E/(2*(1 + poisson)), se poisson existir;
    3. lança erro.
    """

    G = getattr(material, "G", None)

    if G is not None:
        return float(G)

    poisson = getattr(material, "poisson", None)

    if poisson is not None:
        return float(material.E) / (2.0 * (1.0 + float(poisson)))

    raise ValueError(
        f"Material {material.id} precisa de G ou poisson para análise frame3d."
    )


def get_section_property(section, name: str, fallback: float | None = None) -> float:
    """
    Retorna uma propriedade da seção.

    Se a propriedade não existir ou for None, usa fallback.
    """

    value = getattr(section, name, None)

    if value is not None:
        return float(value)

    if fallback is not None:
        return float(fallback)

    raise ValueError(
        f"Seção {section.id} precisa da propriedade {name} para análise frame3d."
    )

def transformation_matrix_3d(
    model: StructuralModel,
    element: Element,
) -> np.ndarray:
    """
    Matriz de transformação 3D 12x12.

    Convenção:
    d_local = T @ d_global

    A matriz usa os eixos locais:
    - x local: eixo da barra, do nó i para o nó j;
    - y local: eixo auxiliar perpendicular;
    - z local: completa o sistema ortonormal de mão direita.
    """

    local_axes = local_axis_matrix_3d(model, element)

    T = np.zeros((12, 12), dtype=float)

    # Nó i - translações
    T[0:3, 0:3] = local_axes

    # Nó i - rotações
    T[3:6, 3:6] = local_axes

    # Nó j - translações
    T[6:9, 6:9] = local_axes

    # Nó j - rotações
    T[9:12, 9:12] = local_axes

    return T

def local_axis_matrix_3d(
    model: StructuralModel,
    element: Element,
) -> np.ndarray:
    """
    Retorna a matriz 3x3 dos eixos locais do elemento.

    Cada linha representa um eixo local escrito em coordenadas globais:

    linha 0: eixo x local
    linha 1: eixo y local
    linha 2: eixo z local
    """

    _, _, _, _, lx, ly, lz = element.geometry_3d(model)

    x_axis = np.array([lx, ly, lz], dtype=float)
    x_axis = normalize_vector(x_axis)

    reference = choose_reference_vector(x_axis)

    z_axis = np.cross(x_axis, reference)
    z_axis = normalize_vector(z_axis)

    y_axis = np.cross(z_axis, x_axis)
    y_axis = normalize_vector(y_axis)

    return np.array(
        [
            x_axis,
            y_axis,
            z_axis,
        ],
        dtype=float,
    )


def choose_reference_vector(x_axis: np.ndarray) -> np.ndarray:
    """
    Escolhe um vetor de referência que não seja paralelo ao eixo local x.
    """

    global_z = np.array([0.0, 0.0, 1.0], dtype=float)

    if abs(np.dot(x_axis, global_z)) < 0.90:
        return global_z

    return np.array([0.0, 1.0, 0.0], dtype=float)


def normalize_vector(vector: np.ndarray) -> np.ndarray:
    """
    Normaliza um vetor.
    """

    norm = np.linalg.norm(vector)

    if norm <= 0:
        raise ValueError("Não é possível normalizar vetor nulo.")

    return vector / norm

def assemble_global_load_vector_3d(model: StructuralModel) -> np.ndarray:
    """
    Monta o vetor global de cargas 3D.
    """

    return np.zeros(model.number_of_dofs(), dtype=float)
