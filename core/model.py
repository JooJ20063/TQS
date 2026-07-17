# core/model.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal
import math


# ==========================================================
# ENTIDADES BÁSICAS
# ==========================================================

@dataclass(frozen=True)
class Node:
    """
    Nó da estrutura 2D.

    Cada nó possui 3 graus de liberdade:
    - ux: deslocamento horizontal
    - uy: deslocamento vertical
    - rz: rotação em torno do eixo z
    """

    id: int
    x: float
    y: float


@dataclass(frozen=True)
class Material:
    """
    Material estrutural.

    Unidades recomendadas:
    - E em kN/m²
    - gamma em kN/m³
    """

    id: int
    name: str
    E: float
    gamma: float = 0.0


@dataclass(frozen=True)
class Section:
    """
    Seção transversal da barra.

    Unidades recomendadas:
    - A em m²
    - I em m⁴

    Para seções retangulares:
    - b em m
    - h em m
    - A = b*h
    - I = b*h³/12
    """

    id: int
    name: str
    A: float
    I: float
    shape: str = "generic"
    b: float | None = None
    h: float | None = None


@dataclass(frozen=True)
class Element:
    """
    Elemento de barra 2D.

    Tipos previstos:
    - frame2d: pórtico plano
    - truss2d: treliça plana, futuramente
    """

    id: int
    node_i: int
    node_j: int
    material: int
    section: int
    kind: Literal["frame2d", "truss2d"] = "frame2d"

    def geometry(self, model: StructuralModel) -> tuple[float, float, float, float, float]:
        """
        Retorna a geometria do elemento.

        Saída:
        dx, dy, L, c, s
        """

        node_i = model.get_node(self.node_i)
        node_j = model.get_node(self.node_j)

        dx = node_j.x - node_i.x
        dy = node_j.y - node_i.y

        L = math.sqrt(dx**2 + dy**2)

        if L <= 0:
            raise ValueError(f"Elemento {self.id} possui comprimento nulo.")

        c = dx / L
        s = dy / L

        return dx, dy, L, c, s


@dataclass(frozen=True)
class Support:
    """
    Restrição de apoio em um nó.

    True  = grau de liberdade restringido
    False = grau de liberdade livre
    """

    node: int
    ux: bool = False
    uy: bool = False
    rz: bool = False


@dataclass(frozen=True)
class NodalLoad:
    """
    Carga aplicada diretamente em um nó.

    Unidades recomendadas:
    - fx em kN
    - fy em kN
    - mz em kN.m
    """

    node: int
    fx: float = 0.0
    fy: float = 0.0
    mz: float = 0.0


@dataclass(frozen=True)
class DistributedLoad:
    """
    Carga distribuída em uma barra.

    qx e qy são interpretados no sistema local da barra.

    Unidade recomendada:
    - qx em kN/m
    - qy em kN/m
    """

    element: int
    qx: float = 0.0
    qy: float = 0.0


@dataclass(frozen=True)
class LoadCase:
    """
    Caso de carregamento.

    Exemplos:
    - PP
    - SC
    - VENTO_X
    """

    name: str
    type: str = "generic"
    nodal_loads: list[NodalLoad] = field(default_factory=list)
    distributed_loads: list[DistributedLoad] = field(default_factory=list)


@dataclass(frozen=True)
class LoadCombination:
    """
    Combinação de ações.

    Exemplo:
    ELU_01 = 1.4*PP + 1.4*SC

    factors:
    {
        "PP": 1.4,
        "SC": 1.4
    }
    """

    name: str
    factors: dict[str, float]


# ==========================================================
# MODELO ESTRUTURAL COMPLETO
# ==========================================================

@dataclass
class StructuralModel:
    """
    Modelo estrutural completo.

    Este objeto guarda todos os dados da estrutura.
    Ele não resolve a estrutura; apenas organiza os dados.
    """

    name: str = "modelo_sem_nome"

    nodes: list[Node] = field(default_factory=list)
    materials: list[Material] = field(default_factory=list)
    sections: list[Section] = field(default_factory=list)
    elements: list[Element] = field(default_factory=list)
    supports: list[Support] = field(default_factory=list)

    # Modo antigo/legado:
    nodal_loads: list[NodalLoad] = field(default_factory=list)
    distributed_loads: list[DistributedLoad] = field(default_factory=list)

    # Modo novo:
    load_cases: list[LoadCase] = field(default_factory=list)
    combinations: list[LoadCombination] = field(default_factory=list)

    # ------------------------------------------------------
    # MAPAS DE BUSCA
    # ------------------------------------------------------

    def node_map(self) -> dict[int, Node]:
        return {node.id: node for node in self.nodes}

    def material_map(self) -> dict[int, Material]:
        return {material.id: material for material in self.materials}

    def section_map(self) -> dict[int, Section]:
        return {section.id: section for section in self.sections}

    def element_map(self) -> dict[int, Element]:
        return {element.id: element for element in self.elements}

    def load_case_map(self) -> dict[str, LoadCase]:
        return {load_case.name: load_case for load_case in self.load_cases}

    # ------------------------------------------------------
    # BUSCAS INDIVIDUAIS
    # ------------------------------------------------------

    def get_node(self, node_id: int) -> Node:
        nodes = self.node_map()

        if node_id not in nodes:
            raise KeyError(f"Nó {node_id} não encontrado no modelo.")

        return nodes[node_id]

    def get_material(self, material_id: int) -> Material:
        materials = self.material_map()

        if material_id not in materials:
            raise KeyError(f"Material {material_id} não encontrado no modelo.")

        return materials[material_id]

    def get_section(self, section_id: int) -> Section:
        sections = self.section_map()

        if section_id not in sections:
            raise KeyError(f"Seção {section_id} não encontrada no modelo.")

        return sections[section_id]

    def get_element(self, element_id: int) -> Element:
        elements = self.element_map()

        if element_id not in elements:
            raise KeyError(f"Elemento {element_id} não encontrado no modelo.")

        return elements[element_id]

    def get_load_case(self, name: str) -> LoadCase:
        load_cases = self.load_case_map()

        if name not in load_cases:
            raise KeyError(f"Caso de carregamento '{name}' não encontrado.")

        return load_cases[name]

    # ------------------------------------------------------
    # GRAUS DE LIBERDADE
    # ------------------------------------------------------

    def sorted_node_ids(self) -> list[int]:
        return sorted(node.id for node in self.nodes)

    def dof_map(self) -> dict[int, tuple[int, int, int]]:
        """
        Cria o mapa dos graus de liberdade globais.

        Para cada nó:
        nó n -> (ux, uy, rz)
        """

        mapping: dict[int, tuple[int, int, int]] = {}

        for index, node_id in enumerate(self.sorted_node_ids()):
            base = 3 * index
            mapping[node_id] = (base, base + 1, base + 2)

        return mapping

    def number_of_dofs(self) -> int:
        return 3 * len(self.nodes)

    def element_dofs(self, element: Element) -> list[int]:
        """
        Retorna os 6 graus de liberdade globais de um elemento de pórtico 2D.

        Ordem:
        [ux_i, uy_i, rz_i, ux_j, uy_j, rz_j]
        """

        dofs = self.dof_map()

        dofs_i = dofs[element.node_i]
        dofs_j = dofs[element.node_j]

        return [
            dofs_i[0],
            dofs_i[1],
            dofs_i[2],
            dofs_j[0],
            dofs_j[1],
            dofs_j[2],
        ]

    def restrained_dofs(self) -> list[int]:
        dofs = self.dof_map()
        restrained: list[int] = []

        for support in self.supports:
            ux, uy, rz = dofs[support.node]

            if support.ux:
                restrained.append(ux)

            if support.uy:
                restrained.append(uy)

            if support.rz:
                restrained.append(rz)

        return sorted(restrained)

    def free_dofs(self) -> list[int]:
        total_dofs = set(range(self.number_of_dofs()))
        restrained = set(self.restrained_dofs())

        return sorted(total_dofs - restrained)
