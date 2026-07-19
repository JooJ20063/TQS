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

    n_dofs = model.number_of_dofs()
    return np.zeros((n_dofs, n_dofs), dtype=float)


def element_local_stiffness_3d(
    model: StructuralModel,
    element: Element,
) -> np.ndarray:
    """
    Matriz de rigidez local 12x12 de um elemento de pórtico espacial.

    Ordem local dos graus de liberdade:
    [u, v, w, rx, ry, rz] no nó i
    [u, v, w, rx, ry, rz] no nó j
    """

    return np.zeros((12, 12), dtype=float)


def transformation_matrix_3d(
    model: StructuralModel,
    element: Element,
) -> np.ndarray:
    """
    Matriz de transformação 3D 12x12.

    Ainda será implementada no próximo commit deste PR.
    """

    return np.eye(12, dtype=float)


def assemble_global_load_vector_3d(model: StructuralModel) -> np.ndarray:
    """
    Monta o vetor global de cargas 3D.
    """

    return np.zeros(model.number_of_dofs(), dtype=float)
