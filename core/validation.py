# core/validation.py

from __future__ import annotations

from core.model import StructuralModel

ALLOWED_LOAD_CASE_TYPES = {
    "generic",
    "permanent",
    "variable",
    "wind",
    "accidental",
}

def validate_model(model: StructuralModel) -> None:
    """
    Valida o modelo estrutural antes da análise.

    A função lança ValueError quando encontra algum problema.
    """

    validate_basic_entities(model)
    validate_unique_ids(model)
    validate_references(model)
    validate_geometry(model)
    validate_materials(model)
    validate_sections(model)
    validate_supports(model)
    validate_loads(model)
    validate_load_cases_and_combinations(model)
    validate_normative_metadata(model)


# ==========================================================
# VALIDAÇÕES BÁSICAS
# ==========================================================

def validate_basic_entities(model: StructuralModel) -> None:
    if len(model.nodes) == 0:
        raise ValueError("O modelo não possui nós.")

    if len(model.elements) == 0:
        raise ValueError("O modelo não possui elementos.")

    if len(model.materials) == 0:
        raise ValueError("O modelo não possui materiais.")

    if len(model.sections) == 0:
        raise ValueError("O modelo não possui seções.")

    if len(model.supports) == 0:
        raise ValueError("O modelo não possui apoios.")


def validate_unique_ids(model: StructuralModel) -> None:
    check_unique_ids([node.id for node in model.nodes], "nós")
    check_unique_ids([element.id for element in model.elements], "elementos")
    check_unique_ids([material.id for material in model.materials], "materiais")
    check_unique_ids([section.id for section in model.sections], "seções")


def check_unique_ids(ids: list[int], entity_name: str) -> None:
    if len(ids) != len(set(ids)):
        raise ValueError(f"Existem IDs repetidos em: {entity_name}.")


# ==========================================================
# REFERÊNCIAS ENTRE OBJETOS
# ==========================================================

def validate_references(model: StructuralModel) -> None:
    node_ids = {node.id for node in model.nodes}
    material_ids = {material.id for material in model.materials}
    section_ids = {section.id for section in model.sections}
    element_ids = {element.id for element in model.elements}

    for element in model.elements:
        if element.node_i not in node_ids:
            raise ValueError(
                f"Elemento {element.id} usa o nó inicial {element.node_i}, "
                "mas esse nó não existe."
            )

        if element.node_j not in node_ids:
            raise ValueError(
                f"Elemento {element.id} usa o nó final {element.node_j}, "
                "mas esse nó não existe."
            )

        if element.material not in material_ids:
            raise ValueError(
                f"Elemento {element.id} usa o material {element.material}, "
                "mas esse material não existe."
            )

        if element.section not in section_ids:
            raise ValueError(
                f"Elemento {element.id} usa a seção {element.section}, "
                "mas essa seção não existe."
            )

    for support in model.supports:
        if support.node not in node_ids:
            raise ValueError(
                f"Apoio aplicado no nó {support.node}, mas esse nó não existe."
            )

    validate_load_references(model.nodal_loads, model.distributed_loads, node_ids, element_ids)

    for load_case in model.load_cases:
        validate_load_references(
            load_case.nodal_loads,
            load_case.distributed_loads,
            node_ids,
            element_ids,
        )


def validate_load_references(
    nodal_loads,
    distributed_loads,
    node_ids: set[int],
    element_ids: set[int],
) -> None:
    for load in nodal_loads:
        if load.node not in node_ids:
            raise ValueError(
                f"Carga nodal aplicada no nó {load.node}, mas esse nó não existe."
            )

    for load in distributed_loads:
        if load.element not in element_ids:
            raise ValueError(
                f"Carga distribuída aplicada no elemento {load.element}, "
                "mas esse elemento não existe."
            )


# ==========================================================
# GEOMETRIA
# ==========================================================

def validate_geometry(model: StructuralModel) -> None:
    for element in model.elements:
        _, _, length, _, _ = element.geometry(model)

        if length <= 0:
            raise ValueError(f"Elemento {element.id} possui comprimento inválido.")


# ==========================================================
# MATERIAIS E SEÇÕES
# ==========================================================

def validate_materials(model: StructuralModel) -> None:
    for material in model.materials:
        if material.E <= 0:
            raise ValueError(
                f"Material {material.id} possui módulo de elasticidade E <= 0."
            )

        if material.gamma < 0:
            raise ValueError(
                f"Material {material.id} possui peso específico gamma < 0."
            )


def validate_sections(model: StructuralModel) -> None:
    for section in model.sections:
        if section.A <= 0:
            raise ValueError(
                f"Seção {section.id} possui área A <= 0."
            )

        if section.I <= 0:
            raise ValueError(
                f"Seção {section.id} possui inércia I <= 0."
            )

        if section.shape == "rectangular":
            if section.b is None or section.h is None:
                raise ValueError(
                    f"Seção retangular {section.id} precisa de b e h."
                )

            if section.b <= 0 or section.h <= 0:
                raise ValueError(
                    f"Seção retangular {section.id} possui b ou h <= 0."
                )


# ==========================================================
# APOIOS
# ==========================================================

def validate_supports(model: StructuralModel) -> None:
    restrained = model.restrained_dofs()

    if len(restrained) == 0:
        raise ValueError("O modelo não possui nenhum grau de liberdade restringido.")

    if len(restrained) < 3:
        raise ValueError(
            "O modelo possui poucos vínculos. "
            "Para pórtico plano 2D, geralmente são necessários pelo menos 3 vínculos."
        )

    support_nodes = [support.node for support in model.supports]

    if len(support_nodes) != len(set(support_nodes)):
        raise ValueError(
            "Existe mais de um apoio definido no mesmo nó. "
            "Use apenas um bloco de apoio por nó."
        )

    for support in model.supports:
        if not support.ux and not support.uy and not support.rz:
            raise ValueError(
                f"Apoio no nó {support.node} não restringe nenhum grau de liberdade."
            )


# ==========================================================
# CARGAS
# ==========================================================

def validate_loads(model: StructuralModel) -> None:
    validate_load_values(model.nodal_loads, model.distributed_loads)

    for load_case in model.load_cases:
        validate_load_values(load_case.nodal_loads, load_case.distributed_loads)


def validate_load_values(nodal_loads, distributed_loads) -> None:
    for load in nodal_loads:
        if load.fx == 0 and load.fy == 0 and load.mz == 0:
            raise ValueError(
                f"Carga nodal no nó {load.node} possui todos os valores iguais a zero."
            )

    for load in distributed_loads:
        if load.qx == 0 and load.qy == 0:
            raise ValueError(
                f"Carga distribuída no elemento {load.element} possui qx e qy iguais a zero."
            )


# ==========================================================
# CASOS E COMBINAÇÕES
# ==========================================================

def validate_load_cases_and_combinations(model: StructuralModel) -> None:
    load_case_names = [load_case.name for load_case in model.load_cases]

    if len(load_case_names) != len(set(load_case_names)):
        raise ValueError("Existem casos de carregamento com nomes repetidos.")

    if len(model.combinations) > 0 and len(model.load_cases) == 0:
        raise ValueError(
            "O modelo possui combinações, mas não possui load_cases."
        )

    load_case_name_set = set(load_case_names)

    for combination in model.combinations:
        if len(combination.factors) == 0:
            raise ValueError(
                f"Combinação {combination.name} não possui fatores."
            )

        for load_case_name in combination.factors:
            if load_case_name not in load_case_name_set:
                raise ValueError(
                    f"Combinação {combination.name} usa o caso '{load_case_name}', "
                    "mas esse caso não existe."
                )

def validate_normative_metadata(model: StructuralModel) -> None:
    for load_case in model.load_cases:
        load_case_type = str(load_case.type).lower()

        if load_case_type not in ALLOWED_LOAD_CASE_TYPES:
            allowed = ", ".join(sorted(ALLOWED_LOAD_CASE_TYPES))

            raise ValueError(
                f"Caso de carregamento '{load_case.name}' possui type='{load_case.type}', "
                f"mas os tipos aceitos são: {allowed}."
            )
