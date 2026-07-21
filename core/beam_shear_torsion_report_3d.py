from __future__ import annotations

from pathlib import Path
from typing import Any


def write_beam_shear_torsion_3d_report_txt(
    report: dict[str, Any],
    output_path: str | Path,
) -> None:
    """
    Escreve relatório textual preliminar de cortante e torção em vigas 3D.
    """

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(
        format_beam_shear_torsion_3d_report(report),
        encoding="utf-8",
    )


def format_beam_shear_torsion_3d_report(report: dict[str, Any]) -> str:
    lines: list[str] = []

    lines.append("RESUMO DE CORTANTE E TORÇÃO EM VIGAS 3D - Estruturalis")
    lines.append("=" * 72)
    lines.append("")
    lines.append(f"Tipo de análise: {report.get('analysis_type', 'frame3d')}")
    lines.append(f"Tipo de relatório: {report.get('report_type', '')}")
    lines.append("")

    lines.append("Hipóteses desta versão:")
    for hypothesis in report.get("hypotheses", []):
        lines.append(f"- {hypothesis}")
    lines.append("")

    global_summary = report.get("global", {})

    lines.append("Resumo global:")
    lines.append("-" * 72)
    lines.append(f"Vigas identificadas: {global_summary.get('number_of_beams', 0)}")
    lines.append(f"Vigas com leitura válida: {global_summary.get('number_of_valid_beams', 0)}")
    lines.append(f"Elementos ignorados: {global_summary.get('number_of_skipped_elements', 0)}")
    lines.append("")

    _append_global_item(
        lines,
        global_summary,
        key="max_shear_y",
        label="Maior cortante local Vy",
        unit="kN",
    )
    _append_global_item(
        lines,
        global_summary,
        key="max_shear_z",
        label="Maior cortante local Vz",
        unit="kN",
    )
    _append_global_item(
        lines,
        global_summary,
        key="max_torsion",
        label="Maior torção local T",
        unit="kN.m",
    )
    _append_index_item(lines, global_summary)

    lines.append("")
    lines.append("Resumo por viga:")
    lines.append("-" * 72)

    for record in report.get("elements", []):
        if record.get("classification") != "beam":
            continue

        lines.append(
            f"Elemento {record.get('element')} "
            f"(N{record.get('node_i')} -> N{record.get('node_j')}):"
        )
        lines.append(f"  Status: {record.get('status')}")
        lines.append(f"  Seção: {record.get('section', '')}")

        if record.get("status") != "ok":
            lines.append(f"  Motivo: {record.get('reason', '')}")
            lines.append("")
            continue

        lines.append(
            f"  Vy: {float(record.get('shear_y_kN', 0.0)):.6e} kN | "
            f"|Vy|={float(record.get('shear_y_abs_kN', 0.0)):.6e} kN | "
            f"{record.get('shear_y_component', '')} | "
            f"caso {record.get('shear_y_case', '')}"
        )
        lines.append(
            f"  Vz: {float(record.get('shear_z_kN', 0.0)):.6e} kN | "
            f"|Vz|={float(record.get('shear_z_abs_kN', 0.0)):.6e} kN | "
            f"{record.get('shear_z_component', '')} | "
            f"caso {record.get('shear_z_case', '')}"
        )
        lines.append(
            f"  T:  {float(record.get('torsion_kNm', 0.0)):.6e} kN.m | "
            f"|T|={float(record.get('torsion_abs_kNm', 0.0)):.6e} kN.m | "
            f"{record.get('torsion_component', '')} | "
            f"caso {record.get('torsion_case', '')}"
        )

        terms = record.get("preliminary_index_terms", {})
        lines.append(
            f"  Índice preliminar: "
            f"{float(record.get('preliminary_index', 0.0)):.6e} "
            f"(Vy={float(terms.get('shear_y', 0.0)):.6e}, "
            f"Vz={float(terms.get('shear_z', 0.0)):.6e}, "
            f"T={float(terms.get('torsion', 0.0)):.6e})"
        )
        lines.append("")

    lines.append("Observação:")
    lines.append("Este relatório é preliminar e acadêmico.")
    lines.append("Ele não dimensiona estribos, armadura transversal ou armadura de torção.")
    lines.append("Os esforços são locais da barra e devem ser interpretados conforme os eixos locais.")
    lines.append("Não substitui verificação normativa completa por profissional habilitado.")
    lines.append("")

    return "\n".join(lines)


def _append_global_item(
    lines: list[str],
    global_summary: dict[str, Any],
    key: str,
    label: str,
    unit: str,
) -> None:
    item = global_summary.get(key)

    if not item:
        lines.append(f"{label}: não disponível")
        return

    lines.append(
        f"{label}: "
        f"{float(item.get('value', 0.0)):.6e} {unit} | "
        f"|valor|={float(item.get('abs_value', 0.0)):.6e} {unit} | "
        f"E{item.get('element')} "
        f"(N{item.get('node_i')} -> N{item.get('node_j')}) | "
        f"{item.get('component', '')} | "
        f"caso {item.get('case', '')}"
    )


def _append_index_item(
    lines: list[str],
    global_summary: dict[str, Any],
) -> None:
    item = global_summary.get("max_preliminary_index")

    if not item:
        lines.append("Maior índice preliminar: não disponível")
        return

    terms = item.get("terms", {})

    lines.append(
        "Maior índice preliminar combinado: "
        f"{float(item.get('value', 0.0)):.6e} | "
        f"E{item.get('element')} "
        f"(N{item.get('node_i')} -> N{item.get('node_j')}) | "
        f"parcelas: "
        f"Vy={float(terms.get('shear_y', 0.0)):.6e}, "
        f"Vz={float(terms.get('shear_z', 0.0)):.6e}, "
        f"T={float(terms.get('torsion', 0.0)):.6e}"
    )
