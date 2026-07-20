from __future__ import annotations

from pathlib import Path
from typing import Any


GROUP_LABELS = {
    "normal": "Normal N",
    "shear_y": "Cortante local Vy",
    "shear_z": "Cortante local Vz",
    "torsion": "Torção T",
    "moment_y": "Momento local My",
    "moment_z": "Momento local Mz",
}


GROUP_UNITS = {
    "normal": "kN",
    "shear_y": "kN",
    "shear_z": "kN",
    "torsion": "kN.m",
    "moment_y": "kN.m",
    "moment_z": "kN.m",
}


def write_envelope_3d_report_txt(
    envelope: dict[str, Any],
    output_path: str | Path,
) -> None:
    """
    Escreve relatório textual da envoltória 3D.
    """

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    text = format_envelope_3d_report(envelope)

    output_path.write_text(text, encoding="utf-8")


def format_envelope_3d_report(envelope: dict[str, Any]) -> str:
    lines: list[str] = []

    lines.append("RESUMO DA ENVOLTÓRIA 3D - Estruturalis")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"Tipo de análise: {envelope.get('analysis_type', 'frame3d')}")
    lines.append(f"Número de casos: {envelope.get('number_of_cases', 0)}")
    lines.append("Casos considerados:")

    for case_name in envelope.get("cases", []):
        lines.append(f"  - {case_name}")

    lines.append("")
    lines.append("Esforços globais críticos:")
    lines.append("-" * 60)

    global_envelope = envelope.get("global", {})
    for group_name, group in global_envelope.items():
        label = GROUP_LABELS.get(group_name, group_name)
        unit = GROUP_UNITS.get(group_name, "")

        abs_record = group["abs"]

        lines.append(
            f"{label}: "
            f"{abs_record['value']:.6e} {unit} | "
            f"elemento {abs_record['element']} | "
            f"{abs_record['component']} | "
            f"caso {abs_record['case']}"
        )

    lines.append("")
    lines.append("Resumo por elemento:")
    lines.append("-" * 60)

    for element in envelope.get("elements", []):
        lines.append(
            f"Elemento {element['id']} "
            f"(N{element.get('node_i')} -> N{element.get('node_j')}):"
        )

        for group_name, group in element.get("groups", {}).items():
            label = GROUP_LABELS.get(group_name, group_name)
            unit = GROUP_UNITS.get(group_name, "")

            abs_record = group["abs"]

            lines.append(
                f"  - {label}: "
                f"{abs_record['value']:.6e} {unit} | "
                f"{abs_record['component']} | "
                f"caso {abs_record['case']}"
            )

        lines.append("")

    lines.append("Observação:")
    lines.append("Os esforços estão no sistema local de cada barra.")
    lines.append("A envoltória 3D é preliminar e voltada para análise acadêmica.")
    lines.append("")

    return "\n".join(lines)
