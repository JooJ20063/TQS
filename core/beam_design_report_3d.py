from __future__ import annotations

from pathlib import Path
from typing import Any


def write_beam_design_3d_report_txt(
    design: dict[str, Any],
    output_path: str | Path,
) -> None:
    """
    Escreve relatório textual do dimensionamento preliminar de vigas 3D.
    """

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(
        format_beam_design_3d_report(design),
        encoding="utf-8",
    )


def format_beam_design_3d_report(design: dict[str, Any]) -> str:
    lines: list[str] = []

    lines.append("RESUMO DO DIMENSIONAMENTO PRELIMINAR DE VIGAS 3D - Estruturalis")
    lines.append("=" * 72)
    lines.append("")
    lines.append(f"Tipo de análise: {design.get('analysis_type', 'frame3d')}")
    lines.append(f"Tipo de dimensionamento: {design.get('design_type', '')}")
    lines.append("")
    lines.append("Parâmetros adotados:")
    lines.append(f"- fyk: {float(design.get('fyk_mpa', 0.0)):.3f} MPa")
    lines.append(f"- gamma_s: {float(design.get('gamma_s', 0.0)):.3f}")
    lines.append(f"- fyd: {float(design.get('fyd_kn_cm2', 0.0)):.6e} kN/cm²")
    lines.append(f"- taxa mínima preliminar: {float(design.get('as_min_ratio', 0.0)):.6e}")
    lines.append(f"- taxa máxima preliminar: {float(design.get('as_max_ratio', 0.0)):.6e}")
    lines.append("")

    lines.append("Hipóteses desta versão:")
    for hypothesis in design.get("hypotheses", []):
        lines.append(f"- {hypothesis}")
    lines.append("")

    global_summary = design.get("global", {})
    critical = global_summary.get("critical_element")

    lines.append("Resumo global:")
    lines.append("-" * 72)
    lines.append(f"Vigas dimensionadas: {global_summary.get('number_of_designed_beams', 0)}")
    lines.append(f"Elementos ignorados: {global_summary.get('number_of_skipped_elements', 0)}")

    if critical:
        lines.append(
            "Elemento crítico: "
            f"E{critical['element']} "
            f"(N{critical['node_i']} -> N{critical['node_j']}) | "
            f"eixo {critical['critical_axis']} | "
            f"As={critical['as_required_cm2']:.6e} cm²"
        )
    else:
        lines.append("Elemento crítico: nenhum")

    lines.append("")
    lines.append("Resumo por elemento:")
    lines.append("-" * 72)

    for record in design.get("elements", []):
        lines.append(
            f"Elemento {record.get('element')} "
            f"(N{record.get('node_i')} -> N{record.get('node_j')}):"
        )

        lines.append(f"  Classificação: {record.get('classification')}")
        lines.append(f"  Status: {record.get('status')}")

        if record.get("status") == "not_designed":
            lines.append(f"  Motivo: {record.get('reason')}")
            lines.append("")
            continue

        lines.append(f"  Seção: {record.get('section')}")
        lines.append(
            f"  Dimensões estimadas/adotadas: "
            f"b={record.get('b_m', 0.0):.6e} m | "
            f"h={record.get('h_m', 0.0):.6e} m"
        )

        lines.append(
            f"  Momentos críticos: "
            f"|My|={record.get('my_kNm', 0.0):.6e} kN.m | "
            f"|Mz|={record.get('mz_kNm', 0.0):.6e} kN.m"
        )

        design_my = record.get("design_my", {})
        design_mz = record.get("design_mz", {})

        lines.append(
            f"  Flexão My: "
            f"As_calc={design_my.get('as_calculated_cm2', 0.0):.6e} cm² | "
            f"As_req={design_my.get('as_required_cm2', 0.0):.6e} cm² | "
            f"status={design_my.get('status')}"
        )

        lines.append(
            f"  Flexão Mz: "
            f"As_calc={design_mz.get('as_calculated_cm2', 0.0):.6e} cm² | "
            f"As_req={design_mz.get('as_required_cm2', 0.0):.6e} cm² | "
            f"status={design_mz.get('status')}"
        )

        lines.append(
            f"  Crítico: eixo {record.get('critical_axis')} | "
            f"As={record.get('as_required_cm2', 0.0):.6e} cm²"
        )

        warnings = record.get("warnings", [])
        if warnings:
            lines.append(f"  Avisos: {'; '.join(warnings)}")

        lines.append("")

    lines.append("Observação:")
    lines.append("Este dimensionamento é preliminar e acadêmico.")
    lines.append("Não considera cortante, torção, ancoragem, detalhamento ou interação N + My + Mz.")
    lines.append("Não substitui verificação normativa completa por profissional habilitado.")
    lines.append("")

    return "\n".join(lines)
