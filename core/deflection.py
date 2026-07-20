# core/deflection.py

from __future__ import annotations

from typing import Any

from core.model import StructuralModel
from core.result_accessors import get_analysis_type


def check_preliminary_deflection(
    model: StructuralModel,
    results: dict[str, Any],
    limit_ratio: float = 250.0,
) -> dict[str, Any]:
    """
    Verificação preliminar de deslocamento vertical.

    Hipótese acadêmica inicial:
    - frame2d: deslocamento vertical = uy;
    - frame3d: deslocamento vertical = uz;
    - limite adotado = L / limit_ratio;
    - L = maior comprimento de elemento do modelo.

    Observação:
    Esta rotina ainda não substitui uma verificação normativa completa.
    """

    if limit_ratio <= 0:
        raise ValueError("limit_ratio deve ser positivo.")

    analysis_type = get_analysis_type(results)
    vertical_key = get_vertical_displacement_key(analysis_type)

    max_span = get_max_element_length(model)

    if max_span <= 0:
        raise ValueError("Não foi possível calcular o vão máximo do modelo.")

    limit = max_span / limit_ratio
    max_displacement = find_max_abs_vertical_displacement(
        results=results,
        key=vertical_key,
    )

    if max_displacement is None:
        return {
            "analysis_type": analysis_type,
            "vertical_key": vertical_key,
            "limit_ratio": limit_ratio,
            "max_span_m": max_span,
            "limit_m": limit,
            "max_displacement": None,
            "utilization": None,
            "status": "not_available",
            "note": "Não foram encontrados deslocamentos nodais.",
        }

    utilization = max_displacement["abs_value"] / limit if limit > 0 else None

    status = "ok"

    if utilization is not None and utilization > 1.0:
        status = "not_ok"

    return {
        "analysis_type": analysis_type,
        "vertical_key": vertical_key,
        "limit_ratio": limit_ratio,
        "max_span_m": max_span,
        "limit_m": limit,
        "max_displacement": max_displacement,
        "utilization": utilization,
        "status": status,
        "note": (
            "Verificação preliminar acadêmica. "
            "Não substitui verificação normativa completa."
        ),
    }


def get_vertical_displacement_key(analysis_type: str) -> str:
    """
    Retorna a chave de deslocamento vertical conforme o tipo de análise.
    """

    if analysis_type == "frame3d":
        return "uz"

    return "uy"


def get_max_element_length(model: StructuralModel) -> float:
    """
    Retorna o maior comprimento de elemento do modelo.
    """

    max_length = 0.0

    for element in model.elements:
        if model.analysis_type == "frame3d":
            _, _, _, length, _, _, _ = element.geometry_3d(model)
        else:
            _, _, length, _, _ = element.geometry(model)

        max_length = max(max_length, length)

    return max_length


def find_max_abs_vertical_displacement(
    results: dict[str, Any],
    key: str,
) -> dict[str, Any] | None:
    """
    Procura o maior deslocamento vertical absoluto.
    """

    best: dict[str, Any] | None = None

    for row in results.get("displacements", []):
        value = float(row.get(key, 0.0))

        candidate = {
            "node": row.get("node"),
            "key": key,
            "value": value,
            "abs_value": abs(value),
        }

        if best is None or candidate["abs_value"] > best["abs_value"]:
            best = candidate

    return best


from pathlib import Path


def write_preliminary_deflection_summary_txt(
    model: StructuralModel,
    results: dict[str, Any],
    file_path: str | Path,
    limit_ratio: float = 250.0,
) -> None:
    """
    Escreve um relatório TXT da verificação preliminar de flecha/deslocamento.
    """

    check = check_preliminary_deflection(
        model=model,
        results=results,
        limit_ratio=limit_ratio,
    )

    text = format_preliminary_deflection_summary(check)

    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with file_path.open("w", encoding="utf-8") as file:
        file.write(text)


def format_preliminary_deflection_summary(check: dict[str, Any]) -> str:
    """
    Formata o resultado da verificação preliminar de flecha.
    """

    lines: list[str] = []

    lines.append("RESUMO PRELIMINAR DE FLECHAS / DESLOCAMENTOS")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"Tipo de análise: {check['analysis_type']}")
    lines.append(f"Direção vertical considerada: {check['vertical_key']}")
    lines.append(f"Maior vão considerado: {check['max_span_m']:.6f} m")
    lines.append(f"Limite adotado: L/{check['limit_ratio']:.0f}")
    lines.append(f"Deslocamento limite: {check['limit_m']:.6e} m")
    lines.append("")

    max_displacement = check.get("max_displacement")

    if max_displacement is None:
        lines.append("Deslocamento máximo: não disponível")
    else:
        lines.append("Deslocamento vertical máximo:")
        lines.append(f"  Nó: {max_displacement['node']}")
        lines.append(f"  Chave: {max_displacement['key']}")
        lines.append(f"  Valor: {max_displacement['value']:.6e} m")
        lines.append(f"  Valor absoluto: {max_displacement['abs_value']:.6e} m")

    lines.append("")

    utilization = check.get("utilization")

    if utilization is None:
        lines.append("Utilização: não disponível")
    else:
        lines.append(f"Utilização: {utilization:.6f}")

    lines.append(f"Status: {check['status']}")
    lines.append("")
    lines.append("Observação:")
    lines.append(str(check["note"]))
    lines.append("")

    return "\n".join(lines)
