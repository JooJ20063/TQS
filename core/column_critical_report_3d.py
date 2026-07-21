from __future__ import annotations

from pathlib import Path
from typing import Any


GLOBAL_LABELS = {
    "max_normal": "Maior normal N",
    "max_moment_y": "Maior momento My",
    "max_moment_z": "Maior momento Mz",
    "max_shear_y": "Maior cortante Vy",
    "max_shear_z": "Maior cortante Vz",
    "max_torsion": "Maior torção T",
}


GLOBAL_UNITS = {
    "max_normal": "kN",
    "max_moment_y": "kN.m",
    "max_moment_z": "kN.m",
    "max_shear_y": "kN",
    "max_shear_z": "kN",
    "max_torsion": "kN.m",
}


def write_column_critical_forces_3d_report_txt(
    report: dict[str, Any],
    output_path: str | Path,
) -> None:
    """
    Escreve relatório textual de esforços críticos em pilares 3D.
    """

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(
        format_column_critical_forces_3d_report(report),
        encoding="utf-8",
    )


def format_column_critical_forces_3d_report(report: dict[str, Any]) -> str:
    lines: list[str] = []

    lines.append("RESUMO DE ESFORÇOS CRÍTICOS EM PILARES 3D - Estruturalis")
    lines.append("=" * 72)
    lines.append("")
    lines.append(f"Tipo de análise: {report.get('analysis_type', 'frame3d')}")
    lines.append(f"Tipo de relatório: {report.get('report_type', '')}")
    lines.append(f"Número de pilares: {report.get('number_of_columns', 0)}")
    lines.append(f"Elementos com falha de leitura: {report.get('number_of_missing', 0)}")
    lines.append("")

    lines.append("Hipóteses desta versão:")
    for hypothesis in report.get("hypotheses", []):
        lines.append(f"- {hypothesis}")
    lines.append("")

    lines.append("Críticos globais:")
    lines.append("-" * 72)

    global_summary = report.get("global", {})

    for key, label in GLOBAL_LABELS.items():
        item = global_summary.get(key)

        if not item:
            lines.append(f"{label}: não disponível")
            continue

        unit = GLOBAL_UNITS.get(key, "")

        lines.append(
            f"{label}: "
            f"{item['value']:.6e} {unit} | "
            f"|valor|={item['abs_value']:.6e} | "
            f"E{item['element']} "
            f"(N{item['node_i']} -> N{item['node_j']}) | "
            f"{item['component']} | "
            f"caso {item['case']}"
        )

    index_item = global_summary.get("max_preliminary_index")
    if index_item:
        lines.append("")
        lines.append(
            "Maior índice preliminar combinado: "
            f"{index_item['value']:.6e} | "
            f"E{index_item['element']} "
            f"(N{index_item['node_i']} -> N{index_item['node_j']})"
        )
        lines.append(
            "  Parcelas: "
            f"N={index_item['normal_ratio']:.6e}, "
            f"My={index_item['moment_y_ratio']:.6e}, "
            f"Mz={index_item['moment_z_ratio']:.6e}"
        )
        lines.append(f"  Fórmula: {index_item['formula']}")

    lines.append("")
    lines.append("Resumo por pilar:")
    lines.append("-" * 72)

    columns = report.get("columns", [])

    if not columns:
        lines.append("Nenhum pilar identificado.")
    else:
        for column in columns:
            lines.append(
                f"Elemento {column.get('element')} "
                f"(N{column.get('node_i')} -> N{column.get('node_j')}):"
            )

            lines.append(f"  Status: {column.get('status')}")

            if column.get("status") != "ok":
                lines.append(f"  Motivo: {column.get('reason')}")
                lines.append("")
                continue

            lines.append(f"  Comprimento: {column.get('length', 0.0):.6e} m")

            forces = column.get("forces", {})

            lines.append(
                f"  N:  {forces.get('normal', {}).get('value', 0.0):.6e} kN "
                f"(|N|={forces.get('normal', {}).get('abs_value', 0.0):.6e})"
            )
            lines.append(
                f"  Vy: {forces.get('shear_y', {}).get('value', 0.0):.6e} kN "
                f"(|Vy|={forces.get('shear_y', {}).get('abs_value', 0.0):.6e})"
            )
            lines.append(
                f"  Vz: {forces.get('shear_z', {}).get('value', 0.0):.6e} kN "
                f"(|Vz|={forces.get('shear_z', {}).get('abs_value', 0.0):.6e})"
            )
            lines.append(
                f"  T:  {forces.get('torsion', {}).get('value', 0.0):.6e} kN.m "
                f"(|T|={forces.get('torsion', {}).get('abs_value', 0.0):.6e})"
            )
            lines.append(
                f"  My: {forces.get('moment_y', {}).get('value', 0.0):.6e} kN.m "
                f"(|My|={forces.get('moment_y', {}).get('abs_value', 0.0):.6e})"
            )
            lines.append(
                f"  Mz: {forces.get('moment_z', {}).get('value', 0.0):.6e} kN.m "
                f"(|Mz|={forces.get('moment_z', {}).get('abs_value', 0.0):.6e})"
            )

            index = column.get("preliminary_index", {})
            lines.append(
                f"  Índice preliminar: {index.get('value', 0.0):.6e} "
                f"(N={index.get('normal_ratio', 0.0):.6e}, "
                f"My={index.get('moment_y_ratio', 0.0):.6e}, "
                f"Mz={index.get('moment_z_ratio', 0.0):.6e})"
            )

            lines.append("")

    lines.append("Observação:")
    lines.append("Este relatório não dimensiona pilares.")
    lines.append("O índice combinado é apenas uma triagem preliminar, não uma verificação normativa.")
    lines.append("A futura verificação de pilares deverá considerar interação N + My + Mz.")
    lines.append("")

    return "\n".join(lines)
