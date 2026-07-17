# core/load_cases.py

from __future__ import annotations

from core.model import (
    StructuralModel,
    LoadCombination,
    NodalLoad,
    DistributedLoad,
)


def has_load_cases(model: StructuralModel) -> bool:
    return len(model.load_cases) > 0


def has_combinations(model: StructuralModel) -> bool:
    return len(model.combinations) > 0


def build_model_for_load_case(
    base_model: StructuralModel,
    load_case_name: str,
) -> StructuralModel:
    """
    Cria um novo StructuralModel contendo apenas as cargas de um caso.
    """

    load_case = base_model.get_load_case(load_case_name)

    return StructuralModel(
        name=f"{base_model.name}_{load_case.name}",
        design_code=dict(base_model.design_code),
        nodes=base_model.nodes,
        materials=base_model.materials,
        sections=base_model.sections,
        elements=base_model.elements,
        supports=base_model.supports,
        nodal_loads=list(load_case.nodal_loads),
        distributed_loads=list(load_case.distributed_loads),
        load_cases=[],
        combinations=[],
    )


def build_model_for_combination(
    base_model: StructuralModel,
    combination: LoadCombination,
) -> StructuralModel:
    """
    Cria um novo StructuralModel contendo as cargas combinadas.

    Exemplo:
    ELU_01 = 1.4*PP + 1.4*SC
    """

    nodal_loads: list[NodalLoad] = []
    distributed_loads: list[DistributedLoad] = []

    for load_case_name, factor in combination.factors.items():
        load_case = base_model.get_load_case(load_case_name)

        nodal_loads.extend(
            scale_nodal_loads(load_case.nodal_loads, factor)
        )

        distributed_loads.extend(
            scale_distributed_loads(load_case.distributed_loads, factor)
        )

    return StructuralModel(
        name=f"{base_model.name}_{combination.name}",
        design_code=dict(base_model.design_code),
        nodes=base_model.nodes,
        materials=base_model.materials,
        sections=base_model.sections,
        elements=base_model.elements,
        supports=base_model.supports,
        nodal_loads=nodal_loads,
        distributed_loads=distributed_loads,
        load_cases=[],
        combinations=[],
    )


def scale_nodal_loads(
    loads: list[NodalLoad],
    factor: float,
) -> list[NodalLoad]:
    scaled_loads: list[NodalLoad] = []

    for load in loads:
        scaled_loads.append(
            NodalLoad(
                node=load.node,
                fx=factor * load.fx,
                fy=factor * load.fy,
                mz=factor * load.mz,
            )
        )

    return scaled_loads


def scale_distributed_loads(
    loads: list[DistributedLoad],
    factor: float,
) -> list[DistributedLoad]:
    scaled_loads: list[DistributedLoad] = []

    for load in loads:
        scaled_loads.append(
            DistributedLoad(
                element=load.element,
                qx=factor * load.qx,
                qy=factor * load.qy,
            )
        )

    return scaled_loads
