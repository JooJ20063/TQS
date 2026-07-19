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
    z: float = 0.0


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
    poisson: float | None = None
    G: float | None = None

    def shear_modulus(self) -> float:
        if self.G is not None:
            return self.G

        if self.poisson is not None:
            return self.E / (2.0 * (1.0 + self.poisson))

        raise ValueError(
            f"Material {self.id} não possui G nem coeficiente de Poisson."
            )

@dataclass(frozen=True)
class Section:
    """
    Seção transversal da barra.

    Para frame2d:
    - I é usado pelo solver antigo.

    Para frame3d:
    - Iy: inércia em torno do eixo local y
    - Iz: inércia em torno do eixo local z
    - J: constante de torção
    """

    id: int
    name: str
    A: float
    I: float
    shape: str = "generic"
    b: float | None = None
    h: float | None = None
    Iy: float | None = None
    Iz: float | None = None
    J: float | None = None

@dataclass(frozen=True)
class Element:
    """
    Elemento de barra.

    Tipos previstos:
    - frame2d: pórtico plano
    - frame3d: pórtico espacial
    - truss2d: treliça plana, futuramente
    - truss3d: treliça espacial, futuramente
    """

    id: int
    node_i: int
    node_j: int
    material: int
    section: int
    kind: Literal["frame2d", "frame3d", "truss2d", "truss3d"] = "frame2d"

    def geometry(self, model: StructuralModel) -> tuple[float, float, float, float, float]:
        """
        Geometria 2D legada.

        Mantida para não quebrar solver, plots, peso próprio e exemplos atuais.

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

    def geometry_3d(
        self,
        model: StructuralModel,
    ) -> tuple[float, float, float, float, float, float, float]:
        """
        Geometria 3D.

        Saída:
        dx, dy, dz, L, lx, ly, lz
        """

        node_i = model.get_node(self.node_i)
        node_j = model.get_node(self.node_j)

        dx = node_j.x - node_i.x
        dy = node_j.y - node_i.y
        dz = node_j.z - node_i.z

        L = math.sqrt(dx**2 + dy**2 + dz**2)

        if L <= 0:
            raise ValueError(f"Elemento {self.id} possui comprimento nulo.")

        lx = dx / L
        ly = dy / L
        lz = dz / L

        return dx, dy, dz, L, lx, ly, lz

@dataclass(frozen=True)
class Support:
    """
    Restrição de apoio em um nó.

    frame2d usa:
    - ux, uy, rz

    frame3d usa:
    - ux, uy, uz, rx, ry, rz
    """

    node: int
    ux: bool = False
    uy: bool = False
    uz: bool = False
    rx: bool = False
    ry: bool = False
    rz: bool = False


@dataclass(frozen=True)
class NodalLoad:
    """
    Carga aplicada diretamente em um nó.

    Forças:
    - fx, fy, fz em kN

    Momentos:
    - mx, my, mz em kN.m
    """

    node: int
    fx: float = 0.0
    fy: float = 0.0
    fz: float = 0.0
    mx: float = 0.0
    my: float = 0.0
    mz: float = 0.0


@dataclass(frozen=True)
class DistributedLoad:
    """
    Carga distribuída em uma barra.

    coordinate_system:
    - local: qx, qy, qz no sistema local da barra;
    - global: qx, qy, qz no sistema global da estrutura.

    Unidade recomendada:
    - kN/m
    """

    element: int
    qx: float = 0.0
    qy: float = 0.0
    qz: float = 0.0
    coordinate_system: Literal["local", "global"] = "local"

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
    analysis_type: Literal["frame2d", "frame3d"] = "frame2d"
    design_code: dict[str, str] = field(default_factory=dict)

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

    def dof_labels(self) -> tuple[str, ...]:
        """
        Retorna os rótulos dos graus de liberdade do modelo.

        frame2d:
        - ux, uy, rz

        frame3d:
        - ux, uy, uz, rx, ry, rz
        """

        if self.analysis_type == "frame3d":
            return ("ux", "uy", "uz", "rx", "ry", "rz")

        return ("ux", "uy", "rz")

    def dofs_per_node(self) -> int:
        """
        Retorna a quantidade de graus de liberdade por nó.
        """

        return len(self.dof_labels())

    def dof_map(self) -> dict[int, tuple[int, ...]]:
        """
        Cria o mapa dos graus de liberdade globais.

        frame2d:
        nó n -> (ux, uy, rz)

        frame3d:
        nó n -> (ux, uy, uz, rx, ry, rz)
        """

        mapping: dict[int, tuple[int, ...]] = {}
        dofs_per_node = self.dofs_per_node()

        for index, node_id in enumerate(self.sorted_node_ids()):
            base = dofs_per_node * index
            mapping[node_id] = tuple(
                base + offset for offset in range(dofs_per_node)
            )

        return mapping

    def number_of_dofs(self) -> int:
        """
        Retorna o número total de graus de liberdade do modelo.
        """

        return self.dofs_per_node() * len(self.nodes)

    def element_dofs(self, element: Element) -> list[int]:
        """
        Retorna os graus de liberdade globais de um elemento.

        frame2d:
        [ux_i, uy_i, rz_i, ux_j, uy_j, rz_j]

        frame3d:
        [ux_i, uy_i, uz_i, rx_i, ry_i, rz_i,
         ux_j, uy_j, uz_j, rx_j, ry_j, rz_j]
        """

        dofs = self.dof_map()

        dofs_i = dofs[element.node_i]
        dofs_j = dofs[element.node_j]

        return list(dofs_i) + list(dofs_j)

    def restrained_dofs(self) -> list[int]:
        """
        Retorna os graus de liberdade restringidos pelos apoios.
        """

        dofs = self.dof_map()
        labels = self.dof_labels()
        restrained: list[int] = []

        for support in self.supports:
            node_dofs = dofs[support.node]

            for index, label in enumerate(labels):
                if getattr(support, label):
                    restrained.append(node_dofs[index])

        return sorted(restrained)

    def free_dofs(self) -> list[int]:
        """
        Retorna os graus de liberdade livres.
        """

        total_dofs = set(range(self.number_of_dofs()))
        restrained = set(self.restrained_dofs())

        return sorted(total_dofs - restrained)
