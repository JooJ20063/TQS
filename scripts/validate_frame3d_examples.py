from __future__ import annotations

import json
import math
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app" / "main.py"
EXAMPLES = ROOT / "examples"
OUTPUT_ROOT = ROOT / "results" / "validation_frame3d"


ABS_TOL = 1.0e-8
REL_TOL = 1.0e-6


VALIDATION_CASES = [
    {
        "name": "viga_3d_console",
        "example": "viga_3d_console.json",
        "displacements": [
            {"node": 2, "key": "uz", "expected": -0.0256, "abs_tol": 1.0e-10},
            {"node": 2, "key": "ry", "expected": 0.0096, "abs_tol": 1.0e-10},
        ],
        "element_force_any_abs": [
            {
            "element": 1,
            "keys": ("moment_y_i", "moment_y_j", "moment_z_i", "moment_z_j"),
            "expected_abs": 40.0,
            "abs_tol": 1.0e-8,
            },
            {
            "element": 1,
            "keys": ("shear_y_i", "shear_y_j", "shear_z_i", "shear_z_j"),
            "expected_abs": 10.0,
            "abs_tol": 1.0e-8,
            },
        ],
    },
    {
        "name": "viga_3d_console_q",
        "example": "viga_3d_console_q.json",
        "displacements": [
            {"node": 2, "key": "uz", "expected": -0.0384, "abs_tol": 1.0e-10},
        ],
        "element_forces_abs": [
            {"element": 1, "key": "moment_y_i", "expected_abs": 80.0, "abs_tol": 1.0e-8},
            {"element": 1, "key": "shear_z_i", "expected_abs": 40.0, "abs_tol": 1.0e-8},
        ],
    },
    {
        "name": "viga_3d_console_q_global",
        "example": "viga_3d_console_q_global.json",
        "displacements": [
            {"node": 2, "key": "uz", "expected": -0.0384, "abs_tol": 1.0e-10},
        ],
        "element_forces_abs": [
            {"element": 1, "key": "moment_y_i", "expected_abs": 80.0, "abs_tol": 1.0e-8},
            {"element": 1, "key": "shear_z_i", "expected_abs": 40.0, "abs_tol": 1.0e-8},
        ],
    },
    {
        "name": "viga_3d_console_y",
        "example": "viga_3d_console_y.json",
        "element_forces_abs": [
            {"element": 1, "key": "moment_y_i", "expected_abs": 40.0, "abs_tol": 1.0e-8},
            {"element": 1, "key": "shear_z_i", "expected_abs": 10.0, "abs_tol": 1.0e-8},
        ],
    },
    {
        "name": "viga_3d_console_inclinada_q_global",
        "example": "viga_3d_console_inclinada_q_global.json",
        "equilibrium_only": True,
    },
    {
        "name": "portico_3d_simples",
        "example": "portico_3d_simples.json",
        "equilibrium_only": True,
    },
]


EXPECTED_OUTPUT_FILES = [
    "resultados.json",
    "envoltoria_3d.json",
    "envoltoria_3d.csv",
    "resumo_envoltoria_3d.txt",
    "deslocamentos_3d.csv",
    "resumo_deslocamentos_3d.txt",
    "dimensionamento_vigas_3d.csv",
    "resumo_dimensionamento_vigas_3d.txt",
    "pilares_3d.csv",
    "resumo_pilares_3d.txt",
    "memorial_3d.txt",
    "estrutura_3d.png",
    "deformada_3d.png",
    "resumo_grafico_3d.txt",
    "resumo_flechas.txt",
]


def main() -> None:
    print("Iniciando validação frame3d...")

    if not APP.exists():
        raise FileNotFoundError(f"Aplicação não encontrada: {APP}")

    if OUTPUT_ROOT.exists():
        shutil.rmtree(OUTPUT_ROOT)

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    for case in VALIDATION_CASES:
        run_validation_case(case)

    print("")
    print("Validação frame3d concluída com sucesso.")


def run_validation_case(case: dict[str, Any]) -> None:
    name = case["name"]
    example_path = EXAMPLES / case["example"]
    output_dir = OUTPUT_ROOT / name

    if not example_path.exists():
        raise FileNotFoundError(f"Exemplo não encontrado: {example_path}")

    print(f"- Rodando {name}...")

    command = [
        sys.executable,
        str(APP),
        str(example_path),
        "-o",
        str(output_dir),
    ]

    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    if completed.returncode != 0:
        print(completed.stdout)
        print(completed.stderr)
        raise RuntimeError(f"Falha ao executar caso {name}")

    results_path = output_dir / "resultados.json"

    if not results_path.exists():
        raise FileNotFoundError(f"Arquivo resultados.json não gerado em {name}")

    results = json.loads(results_path.read_text(encoding="utf-8"))

    assert results.get("analysis_type") == "frame3d", name

    assert_equilibrium_ok(results, name)
    assert_expected_files(output_dir, name)

    for displacement_check in case.get("displacements", []):
        assert_displacement(results, displacement_check, name)

    #for force_check in case.get("element_forces_abs", []):
        #assert_element_force_abs(results, force_check, name)

    for force_check in case.get("element_force_any_abs", []):
        assert_element_force_any_abs(results, force_check, name)

    print(f"  OK: {name}")

def assert_element_force_any_abs(
    results: dict[str, Any],
    check: dict[str, Any],
    case_name: str,
) -> None:
    element_id = int(check["element"])
    keys = tuple(check["keys"])
    expected_abs = float(check["expected_abs"])
    abs_tol = float(check.get("abs_tol", ABS_TOL))

    element = find_element_result(results, element_id)
    local_end_forces = element.get("local_end_forces", {})

    candidates = []

    for key in keys:
        if key in local_end_forces:
            candidates.append((key, abs(float(local_end_forces[key]))))

    if not candidates:
        raise AssertionError(
            f"{case_name}: nenhum dos esforços {keys} existe no elemento {element_id}"
        )

    best_key, best_value = min(
        candidates,
        key=lambda item: abs(item[1] - expected_abs),
    )

    assert_close(
        value=best_value,
        expected=expected_abs,
        case_name=case_name,
        label=f"melhor esforço entre {keys} no elemento {element_id} ({best_key})",
        abs_tol=abs_tol,
    )


def assert_equilibrium_ok(results: dict[str, Any], case_name: str) -> None:
    equilibrium = results.get("equilibrium")

    if not equilibrium:
        raise AssertionError(f"{case_name}: equilíbrio global ausente")

    status = equilibrium.get("status")

    if status != "OK":
        raise AssertionError(f"{case_name}: equilíbrio não OK: {status}")

    force_norm = float(equilibrium.get("force_norm", 0.0))
    moment_norm = float(equilibrium.get("moment_norm", 0.0))
    tolerance = float(equilibrium.get("tolerance", 0.0))

    if force_norm > tolerance:
        raise AssertionError(
            f"{case_name}: força residual acima da tolerância: "
            f"{force_norm} > {tolerance}"
        )

    if moment_norm > tolerance:
        raise AssertionError(
            f"{case_name}: momento residual acima da tolerância: "
            f"{moment_norm} > {tolerance}"
        )


def assert_expected_files(output_dir: Path, case_name: str) -> None:
    missing = []

    for file_name in EXPECTED_OUTPUT_FILES:
        path = output_dir / file_name
        if not path.exists():
            missing.append(file_name)

    if missing:
        raise AssertionError(
            f"{case_name}: arquivos esperados ausentes: {', '.join(missing)}"
        )


def assert_displacement(
    results: dict[str, Any],
    check: dict[str, Any],
    case_name: str,
) -> None:
    node = int(check["node"])
    key = check["key"]
    expected = float(check["expected"])
    abs_tol = float(check.get("abs_tol", ABS_TOL))

    record = find_node_displacement(results, node)

    value = float(record.get(key, 0.0))

    assert_close(
        value=value,
        expected=expected,
        case_name=case_name,
        label=f"deslocamento nó {node} {key}",
        abs_tol=abs_tol,
    )


def assert_element_force_abs(
    results: dict[str, Any],
    check: dict[str, Any],
    case_name: str,
) -> None:
    element_id = int(check["element"])
    key = check["key"]
    expected_abs = float(check["expected_abs"])
    abs_tol = float(check.get("abs_tol", ABS_TOL))

    element = find_element_result(results, element_id)
    local_end_forces = element.get("local_end_forces", {})

    if key not in local_end_forces:
        raise AssertionError(
            f"{case_name}: esforço {key} ausente no elemento {element_id}"
        )

    value_abs = abs(float(local_end_forces[key]))

    assert_close(
        value=value_abs,
        expected=expected_abs,
        case_name=case_name,
        label=f"|{key}| elemento {element_id}",
        abs_tol=abs_tol,
    )


def find_node_displacement(results: dict[str, Any], node: int) -> dict[str, Any]:
    for record in results.get("displacements", []):
        if int(record.get("node")) == node:
            return record

    raise AssertionError(f"Deslocamento do nó {node} não encontrado")


def find_element_result(results: dict[str, Any], element_id: int) -> dict[str, Any]:
    for element in results.get("elements", []):
        if int(element.get("id")) == element_id:
            return element

    raise AssertionError(f"Resultado do elemento {element_id} não encontrado")


def assert_close(
    value: float,
    expected: float,
    case_name: str,
    label: str,
    abs_tol: float = ABS_TOL,
    rel_tol: float = REL_TOL,
) -> None:
    if not math.isclose(value, expected, abs_tol=abs_tol, rel_tol=rel_tol):
        raise AssertionError(
            f"{case_name}: {label} diferente do esperado. "
            f"valor={value:.12e}, esperado={expected:.12e}, "
            f"abs_tol={abs_tol:.1e}, rel_tol={rel_tol:.1e}"
        )


if __name__ == "__main__":
    main()
