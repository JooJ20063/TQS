from __future__ import annotations

from pathlib import Path
from typing import Any

from core.displacement_report_3d import create_displacement_summary_3d


ENVELOPE_LABELS = {
    "normal": ("Normal N", "kN"),
    "shear_y": ("Cortante local Vy", "kN"),
    "shear_z": ("Cortante local Vz", "kN"),
    "torsion": ("Torção T", "kN.m"),
    "moment_y": ("Momento local My", "kN.m"),
    "moment_z": ("Momento local Mz", "kN.m"),
}


def write_frame3d_memorial_txt(
    model,
    results: dict[str, Any],
    envelope: dict[str, Any] | None,
    beam_design: dict[str, Any] | None,
    column_report: dict[str, Any] | None,
    output_path: str | Path,
) -> None:
    """
    Escreve memorial integrado da análise 3D.

    Este memorial não substitui os relatórios específicos.
    Ele apenas organiza os principais resultados em um único arquivo.
    """

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    text = format_frame3d_memorial(
        model=model,
        results=results,
        envelope=envelope,
        beam_design=beam_design,
        column_report=column_report,
    )

    output_path.write_text(text, encoding="utf-8")


def format_frame3d_memorial(
    model,
    results: dict[str, Any],
    envelope: dict[str, Any] | None,
    beam_design: dict[str, Any] | None,
    column_report: dict[str, Any] | None,
) -> str:
    lines: list[str] = []

    lines.append("MEMORIAL INTEGRADO 3D - Estruturalis")
    lines.append("=" * 72)
    lines.append("")
    lines.append("Este memorial reúne os principais resultados da análise frame3d.")
    lines.append("Os relatórios específicos continuam sendo a fonte detalhada de cada etapa.")
    lines.append("")

    _append_general_data(lines, model, results)
    _append_equilibrium(lines, results)
    _append_displacements(lines, results)
    _append_envelope(lines, envelope)
    _append_beam_design(lines, beam_design)
    _append_columns(lines, column_report)
    _append_generated_files(lines)
    _append_limitations(lines)

    return "\n".join(lines)


def _append_general_data(lines: list[str], model, results: dict[str, Any]) -> None:
    lines.append("1. Dados gerais da análise")
    lines.append("-" * 72)

    analysis_type = results.get("analysis_type", getattr(model, "analysis_type", "frame3d"))

    number_of_nodes = len(getattr(model, "nodes", []))
    number_of_elements = len(getattr(model, "elements", []))
    number_of_supports = len(getattr(model, "supports", []))
    number_of_nodal_loads = len(getattr(model, "nodal_loads", []))
    number_of_distributed_loads = len(getattr(model, "distributed_loads", []))

    number_of_dofs = results.get("number_of_dofs")
    if number_of_dofs is None and hasattr(model, "number_of_dofs"):
        number_of_dofs = model.number_of_dofs()

    lines.append(f"Tipo de análise: {analysis_type}")
    lines.append(f"Nós: {number_of_nodes}")
    lines.append(f"Elementos: {number_of_elements}")
    lines.append(f"Apoios: {number_of_supports}")
    lines.append(f"Cargas nodais: {number_of_nodal_loads}")
    lines.append(f"Cargas distribuídas: {number_of_distributed_loads}")

    if number_of_dofs is not None:
        lines.append(f"Graus de liberdade: {number_of_dofs}")

    lines.append("")


def _append_equilibrium(lines: list[str], results: dict[str, Any]) -> None:
    lines.append("2. Equilíbrio global")
    lines.append("-" * 72)

    equilibrium = results.get("equilibrium")

    if not equilibrium:
        lines.append("Equilíbrio global não disponível nos resultados.")
        lines.append("")
        return

    status = equilibrium.get("status", "indefinido")
    force_norm = float(equilibrium.get("force_norm", 0.0))
    moment_norm = float(equilibrium.get("moment_norm", 0.0))
    tolerance = float(equilibrium.get("tolerance", 0.0))

    lines.append(f"Status: {status}")
    lines.append(f"Norma residual de forças: {force_norm:.6e}")
    lines.append(f"Norma residual de momentos: {moment_norm:.6e}")
    lines.append(f"Tolerância adotada: {tolerance:.6e}")

    sum_forces = equilibrium.get("sum_forces", {})
    sum_moments = equilibrium.get("sum_moments", {})

    if sum_forces:
        lines.append(
            "Soma de forças: "
            f"Fx={float(sum_forces.get('fx', 0.0)):.6e}, "
            f"Fy={float(sum_forces.get('fy', 0.0)):.6e}, "
            f"Fz={float(sum_forces.get('fz', 0.0)):.6e}"
        )

    if sum_moments:
        lines.append(
            "Soma de momentos: "
            f"Mx={float(sum_moments.get('mx', 0.0)):.6e}, "
            f"My={float(sum_moments.get('my', 0.0)):.6e}, "
            f"Mz={float(sum_moments.get('mz', 0.0)):.6e}"
        )

    lines.append("")


def _append_displacements(lines: list[str], results: dict[str, Any]) -> None:
    lines.append("3. Deslocamentos e drift")
    lines.append("-" * 72)

    try:
        summary = create_displacement_summary_3d(results)
    except ValueError:
        lines.append("Resumo de deslocamentos não disponível.")
        lines.append("")
        return

    maxima = summary.get("maxima", {})

    _append_component_maximum(lines, maxima, "ux", "Máximo |ux|", "m")
    _append_component_maximum(lines, maxima, "uy", "Máximo |uy|", "m")
    _append_component_maximum(lines, maxima, "uz", "Máximo |uz|", "m")
    _append_resultant_maximum(lines, maxima, "horizontal_resultant", "Máximo deslocamento horizontal", "m")
    _append_resultant_maximum(lines, maxima, "translation_resultant", "Máximo deslocamento translacional", "m")
    _append_resultant_maximum(lines, maxima, "rotation_resultant", "Máxima rotação resultante", "rad")

    story_drifts = summary.get("story_drifts", [])
    if story_drifts:
        critical_drift = max(story_drifts, key=lambda item: float(item.get("drift_ratio", 0.0)))
        lines.append(
            "Maior drift aproximado: "
            f"Z {critical_drift['z_bottom']:.6g} -> {critical_drift['z_top']:.6g} m | "
            f"drift={critical_drift['drift']:.6e} m | "
            f"razão={critical_drift['drift_ratio']:.6e} | "
            f"ponto ({critical_drift['x']:.6g}, {critical_drift['y']:.6g})"
        )
    else:
        lines.append("Drift aproximado: não calculado.")

    lines.append("")


def _append_envelope(lines: list[str], envelope: dict[str, Any] | None) -> None:
    lines.append("4. Envoltória de esforços 3D")
    lines.append("-" * 72)

    if not envelope:
        lines.append("Envoltória 3D não disponível.")
        lines.append("")
        return

    lines.append(f"Número de casos considerados: {envelope.get('number_of_cases', 0)}")

    global_envelope = envelope.get("global", {})

    if not global_envelope:
        lines.append("Críticos globais da envoltória não disponíveis.")
        lines.append("")
        return

    for group_name, (label, unit) in ENVELOPE_LABELS.items():
        group = global_envelope.get(group_name)
        if not group:
            continue

        record = group.get("abs", {})

        lines.append(
            f"{label}: "
            f"{float(record.get('value', 0.0)):.6e} {unit} | "
            f"E{record.get('element')} | "
            f"{record.get('component')} | "
            f"caso {record.get('case')}"
        )

    lines.append("")


def _append_beam_design(lines: list[str], beam_design: dict[str, Any] | None) -> None:
    lines.append("5. Dimensionamento preliminar de vigas 3D")
    lines.append("-" * 72)

    if not beam_design:
        lines.append("Dimensionamento preliminar de vigas 3D não disponível.")
        lines.append("")
        return

    global_summary = beam_design.get("global", {})
    critical = global_summary.get("critical_element")

    lines.append(f"Tipo: {beam_design.get('design_type', '')}")
    lines.append(f"Vigas dimensionadas: {global_summary.get('number_of_designed_beams', 0)}")
    lines.append(f"Elementos ignorados: {global_summary.get('number_of_skipped_elements', 0)}")
    lines.append(f"fyk: {float(beam_design.get('fyk_mpa', 0.0)):.3f} MPa")
    lines.append(f"gamma_s: {float(beam_design.get('gamma_s', 0.0)):.3f}")

    if critical:
        lines.append(
            "Elemento crítico por armadura requerida: "
            f"E{critical['element']} "
            f"(N{critical['node_i']} -> N{critical['node_j']}) | "
            f"eixo {critical['critical_axis']} | "
            f"As_req={critical['as_required_cm2']:.6e} cm² | "
            f"governa={_format_governing_reason(critical.get('governing_reason'))}"
        )
        lines.append(
            "Armadura do elemento crítico: "
            f"As_calc={critical.get('critical_as_calculated_cm2', 0.0):.6e} cm² | "
            f"As_min={critical.get('critical_as_min_cm2', 0.0):.6e} cm² | "
            f"As_max={critical.get('critical_as_max_cm2', 0.0):.6e} cm²"
        )
        lines.append(
            "Momentos do elemento crítico: "
            f"|My|={critical['my_kNm']:.6e} kN.m | "
            f"|Mz|={critical['mz_kNm']:.6e} kN.m"
        )
    else:
        lines.append("Elemento crítico: não disponível.")

    lines.append("")


def _append_columns(lines: list[str], column_report: dict[str, Any] | None) -> None:
    lines.append("6. Pilares 3D - esforços críticos")
    lines.append("-" * 72)

    if not column_report:
        lines.append("Relatório de pilares 3D não disponível.")
        lines.append("")
        return

    lines.append(f"Número de pilares: {column_report.get('number_of_columns', 0)}")
    lines.append(f"Elementos com falha de leitura: {column_report.get('number_of_missing', 0)}")

    global_summary = column_report.get("global", {})

    _append_column_global_item(lines, global_summary, "max_normal", "Maior normal N", "kN")
    _append_column_global_item(lines, global_summary, "max_moment_y", "Maior momento My", "kN.m")
    _append_column_global_item(lines, global_summary, "max_moment_z", "Maior momento Mz", "kN.m")

    index_item = global_summary.get("max_preliminary_index")
    if index_item:
        lines.append(
            "Maior índice preliminar combinado: "
            f"{float(index_item.get('value', 0.0)):.6e} | "
            f"E{index_item.get('element')} "
            f"(N{index_item.get('node_i')} -> N{index_item.get('node_j')})"
        )

    lines.append("")


def _append_generated_files(lines: list[str]) -> None:
    lines.append("7. Arquivos principais gerados")
    lines.append("-" * 72)

    files = [
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
        "estrutura_3d.png",
        "deformada_3d.png",
        "estrutura_3d_interativa.html",
        "resumo_grafico_3d.txt",
        "resumo_flechas.txt",
        "memorial_3d.txt",
    ]

    for file_name in files:
        lines.append(f"- {file_name}")

    lines.append("")


def _append_limitations(lines: list[str]) -> None:
    lines.append("8. Limitações e observações")
    lines.append("-" * 72)

    limitations = [
        "Os esforços internos 3D são apresentados no sistema local de cada barra.",
        "O dimensionamento de vigas 3D é preliminar e acadêmico.",
        "O dimensionamento de vigas considera flexão simples separada em My e Mz.",
        "Cortante, torção, ancoragem e detalhamento ainda não são dimensionados.",
        "Pilares 3D ainda não são dimensionados; apenas seus esforços críticos são listados.",
        "A interação N + My + Mz em pilares ainda não é verificada.",
        "O relatório não substitui verificação normativa completa.",
        "Os resultados devem ser conferidos por profissional habilitado antes de qualquer uso prático.",
    ]

    for limitation in limitations:
        lines.append(f"- {limitation}")

    lines.append("")


def _append_component_maximum(
    lines: list[str],
    maxima: dict[str, Any],
    key: str,
    label: str,
    unit: str,
) -> None:
    record = maxima.get(key)
    if not record:
        return

    lines.append(
        f"{label}: "
        f"{float(record.get('value', 0.0)):.6e} {unit} | "
        f"|valor|={float(record.get('abs_value', 0.0)):.6e} | "
        f"nó {record.get('node')}"
    )


def _append_resultant_maximum(
    lines: list[str],
    maxima: dict[str, Any],
    key: str,
    label: str,
    unit: str,
) -> None:
    record = maxima.get(key)
    if not record:
        return

    lines.append(
        f"{label}: "
        f"{float(record.get('value', 0.0)):.6e} {unit} | "
        f"nó {record.get('node')}"
    )


def _append_column_global_item(
    lines: list[str],
    global_summary: dict[str, Any],
    key: str,
    label: str,
    unit: str,
) -> None:
    item = global_summary.get(key)

    if not item:
        return

    lines.append(
        f"{label}: "
        f"{float(item.get('value', 0.0)):.6e} {unit} | "
        f"|valor|={float(item.get('abs_value', 0.0)):.6e} | "
        f"E{item.get('element')} "
        f"(N{item.get('node_i')} -> N{item.get('node_j')})"
    )


def _format_governing_reason(reason: str | None) -> str:
    labels = {
        "minimum_reinforcement": "armadura mínima preliminar",
        "calculated_reinforcement": "armadura calculada",
        "above_preliminary_maximum": "acima do máximo preliminar",
        "invalid_geometry_or_material": "geometria ou material inválido",
        "unknown": "indefinido",
        None: "indefinido",
    }

    return labels.get(reason, str(reason))
