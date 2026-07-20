# io_module/json_reader.py

from __future__ import annotations
from core.norms.config import default_abnt_config

import json
from pathlib import Path

from core.model import (
    StructuralModel,
    Node,
    Material,
    Section,
    Element,
    Support,
    NodalLoad,
    DistributedLoad,
    LoadCase,
    LoadCombination,
)


def read_model_from_json(file_path: str | Path) -> StructuralModel:
    """
    Lê um arquivo JSON e converte para StructuralModel.
    """

    file_path = Path(file_path)

    with file_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return parse_model(data)


def parse_model(data: dict) -> StructuralModel:
    """
    Converte o dicionário lido do JSON em StructuralModel.
    """

    model = StructuralModel(
    name=data.get("name", "modelo_sem_nome"),
    analysis_type=str(data.get("analysis_type", data.get("model_type", "frame2d"))).lower(),
    design_code=parse_design_code(data.get("design_code", {})),
    )

    model.nodes = parse_nodes(data.get("nodes", []))
    model.materials = parse_materials(data.get("materials", []))
    model.sections = parse_sections(data.get("sections", []))
    model.elements = parse_elements(data.get("elements", []))
    model.supports = parse_supports(data.get("supports", []))

    # Modo antigo/legado
    model.nodal_loads = parse_nodal_loads(data.get("nodal_loads", data.get("loads", [])))
    model.distributed_loads = parse_distributed_loads(data.get("distributed_loads", []))

    # Modo novo
    model.load_cases = parse_load_cases(data.get("load_cases", []))
    model.combinations = parse_combinations(data.get("combinations", []))

    apply_self_weight_if_enabled(model, data.get("self_weight", False))

    return model


# ==========================================================
# PARSERS DAS ENTIDADES
# ==========================================================

def parse_design_code(item: dict) -> dict[str, str]:

    config = default_abnt_config()

    design_code = {
        "concrete_code": config.concrete_code,
        "concrete_code_version": config.concrete_code_version,
        "actions_code": config.actions_code,
        "actions_code_version": config.actions_code_version,
        "combinations_code": config.combinations_code,
        "combinations_code_version": config.combinations_code_version,
        "wind_code": config.wind_code,
        "wind_code_version": config.wind_code_version,
        "mode": config.mode,
    }

    if not isinstance(item, dict):
        return design_code

    for key, value in item.items():
        design_code[str(key)] = str(value)

    return design_code

def parse_nodes(items: list[dict]) -> list[Node]:
    nodes: list[Node] = []

    for item in items:
        node = Node(
            id=int(item["id"]),
            x=float(item["x"]),
            y=float(item["y"]),
            z=float(item.get("z", 0.0)),
        )

        nodes.append(node)

    return nodes


def parse_materials(items: list[dict]) -> list[Material]:
    materials: list[Material] = []

    for item in items:
        material = Material(
            id=int(item["id"]),
            name=str(item.get("name", f"material_{item['id']}")),
            E=float(item["E"]),
            gamma=float(item.get("gamma", 0.0)),
            poisson=(float(item["poisson"])
            if "poisson" in item
            else None),
            G=(float(item["G"])
               if "G" in item
                else None
            ),
        )

        materials.append(material)

    return materials


def parse_sections(items: list[dict]) -> list[Section]:
    sections: list[Section] = []

    for item in items:
        section_type = str(item.get("type", item.get("shape", "generic"))).lower()

        if section_type in ["rectangular", "retangular"]:
            b = float(item["b"])
            h = float(item["h"])

            A = float(item.get("A", b * h))
            Iy = float(item.get("Iy", b * h**3 / 12.0))
            Iz = float(item.get("Iz", h * b**3 / 12.0))
            J = float(item.get("J", Iy + Iz))

            I = float(item.get("I", Iy))

            section = Section(
                id=int(item["id"]),
                name=str(item.get("name", f"section_{item['id']}")),
                A=A,
                I=I,
                shape="rectangular",
                b=b,
                h=h,
                Iy=Iy,
                Iz=Iz,
                J=J,
            )
        else:
            I = float(item["I"])

            section = Section(
                id=int(item["id"]),
                name=str(item.get("name", f"section_{item['id']}")),
                A=float(item["A"]),
                I=I,
                shape=section_type,
                b=float(item["b"]) if "b" in item else None,
                h=float(item["h"]) if "h" in item else None,
                Iy=float(item["Iy"]) if "Iy" in item else None,
                Iz=float(item["Iz"]) if "Iz" in item else None,
                J=float(item["J"]) if "J" in item else None,
            )

        sections.append(section)

    return sections


def parse_elements(items: list[dict]) -> list[Element]:
    elements: list[Element] = []

    for item in items:
        element = Element(
            id=int(item["id"]),
            node_i=int(item["node_i"]),
            node_j=int(item["node_j"]),
            material=int(item["material"]),
            section=int(item["section"]),
            kind=str(item.get("kind", "frame2d")),
        )

        elements.append(element)

    return elements


def parse_supports(items: list[dict]) -> list[Support]:
    supports: list[Support] = []

    for item in items:
        support = Support(
            node=int(item["node"]),
            ux=bool(item.get("ux", False)),
            uy=bool(item.get("uy", False)),
            uz=bool(item.get("uz", False)),
            rx=bool(item.get("rx", False)),
            ry=bool(item.get("ry", False)),
            rz=bool(item.get("rz", False)),
        )

        supports.append(support)

    return supports


def parse_nodal_loads(items: list[dict]) -> list[NodalLoad]:
    loads: list[NodalLoad] = []

    for item in items:
        load = NodalLoad(
            node=int(item["node"]),
            fx=float(item.get("fx", 0.0)),
            fy=float(item.get("fy", 0.0)),
            fz=float(item.get("fz", 0.0)),
            mx=float(item.get("mx", 0.0)),
            my=float(item.get("my", 0.0)),
            mz=float(item.get("mz", 0.0)),
        )
        loads.append(load)

    return loads


def parse_distributed_loads(items: list[dict]) -> list[DistributedLoad]:
    loads: list[DistributedLoad] = []

    for item in items:
        load = DistributedLoad(
            element=int(item["element"]),
            qx=float(item.get("qx", 0.0)),
            qy=float(item.get("qy", 0.0)),
            qz=float(item.get("qz", 0.0)),
            coordinate_system=str(
                item.get("coordinate_system", item.get("system", "local"))
            ).lower(),
        )

        loads.append(load)

    return loads


def parse_load_cases(items: list[dict]) -> list[LoadCase]:
    load_cases: list[LoadCase] = []

    for item in items:
        load_case = LoadCase(
            name=str(item["name"]),
            type=str(item.get("type", "generic")),
            nodal_loads=parse_nodal_loads(item.get("nodal_loads", [])),
            distributed_loads=parse_distributed_loads(item.get("distributed_loads", [])),
        )

        load_cases.append(load_case)

    return load_cases


def parse_combinations(items: list[dict]) -> list[LoadCombination]:
    combinations: list[LoadCombination] = []

    for item in items:
        raw_factors = item.get("factors", {})

        factors = {
            str(load_case_name): float(factor)
            for load_case_name, factor in raw_factors.items()
        }

        combination = LoadCombination(
            name=str(item["name"]),
            factors=factors,
        )

        combinations.append(combination)

    return combinations


# ==========================================================
# PESO PRÓPRIO AUTOMÁTICO
# ==========================================================

def apply_self_weight_if_enabled(
    model: StructuralModel,
    self_weight_config: bool | dict,
) -> None:
    """
    Aplica peso próprio automaticamente, caso habilitado no JSON.

    Se o modelo possui load_cases/combinations, o peso próprio entra no
    caso de carregamento definido por self_weight.load_case, por padrão "PP".

    Se o modelo não possui load_cases, o peso próprio entra no modo antigo,
    diretamente em model.distributed_loads.
    """

    if not is_self_weight_enabled(self_weight_config):
        return

    gamma_default = get_self_weight_gamma_default(self_weight_config)
    self_weight_loads = calculate_self_weight_loads(model, gamma_default)

    if len(model.load_cases) > 0 or len(model.combinations) > 0:
        target_case_name = get_self_weight_load_case_name(self_weight_config)
        append_loads_to_load_case(model, target_case_name, self_weight_loads)
    else:
        model.distributed_loads.extend(self_weight_loads)


def calculate_self_weight_loads(
    model: StructuralModel,
    gamma_default: float,
) -> list[DistributedLoad]:
    """
    Calcula as cargas distribuídas equivalentes ao peso próprio.

    frame2d:
    - mantém o comportamento antigo;
    - peso próprio atua no eixo global Y negativo;
    - carga é convertida para o sistema local da barra.

    frame3d:
    - peso próprio atua no eixo global Z negativo;
    - carga é armazenada como carga distribuída global.
    """

    loads: list[DistributedLoad] = []

    for element in model.elements:
        material = model.get_material(element.material)
        section = model.get_section(element.section)

        gamma = material.gamma if material.gamma > 0 else gamma_default

        if gamma <= 0:
            continue

        w = gamma * section.A

        if model.analysis_type == "frame3d":
            loads.append(
                DistributedLoad(
                    element=element.id,
                    qx=0.0,
                    qy=0.0,
                    qz=-w,
                    coordinate_system="global",
                )
            )
            continue

        # Comportamento legado frame2d:
        # carga no sistema global:
        gx = 0.0
        gy = -w

        _, _, _, c, s = element.geometry(model)

        # Conversão global -> local:
        # qx =  c*gx + s*gy
        # qy = -s*gx + c*gy
        qx_local = c * gx + s * gy
        qy_local = -s * gx + c * gy

        loads.append(
            DistributedLoad(
                element=element.id,
                qx=qx_local,
                qy=qy_local,
                coordinate_system="local",
            )
        )

    return loads

def append_loads_to_load_case(
    model: StructuralModel,
    load_case_name: str,
    distributed_loads: list[DistributedLoad],
) -> None:
    """
    Adiciona cargas distribuídas a um caso de carregamento.

    Se o caso não existir, ele é criado automaticamente.
    """

    for index, load_case in enumerate(model.load_cases):
        if load_case.name == load_case_name:
            new_case = LoadCase(
                name=load_case.name,
                type=load_case.type,
                nodal_loads=list(load_case.nodal_loads),
                distributed_loads=list(load_case.distributed_loads) + distributed_loads,
            )

            model.load_cases[index] = new_case
            return

    model.load_cases.append(
        LoadCase(
            name=load_case_name,
            type="permanent",
            nodal_loads=[],
            distributed_loads=distributed_loads,
        )
    )


def is_self_weight_enabled(self_weight_config: bool | dict) -> bool:
    if isinstance(self_weight_config, bool):
        return self_weight_config

    if isinstance(self_weight_config, dict):
        return bool(self_weight_config.get("enabled", False))

    return False


def get_self_weight_gamma_default(self_weight_config: bool | dict) -> float:
    if isinstance(self_weight_config, dict):
        return float(self_weight_config.get("gamma_default", 25.0))

    return 25.0


def get_self_weight_load_case_name(self_weight_config: bool | dict) -> str:
    if isinstance(self_weight_config, dict):
        return str(self_weight_config.get("load_case", "PP"))

    return "PP"
