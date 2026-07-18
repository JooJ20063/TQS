from pathlib import Path
import csv

from core.norms.nbr6118.flexure import design_rectangular_section_flexure
from core.norms.nbr6118.rebar import (
    select_rebar_options,
    check_single_layer_spacing,
)

CSV_COLUMNS = [
    "elemento",
    "no_i",
    "no_j",
    "comprimento_m",
    "b_m",
    "h_m",
    "d_m",
    "momento_critico_kNm",
    "momento_abs_kNm",
    "caso_momento",
    "posicao_armadura",
    "as_calculado_cm2",
    "as_minimo_cm2",
    "as_maximo_cm2",
    "as_adotado_cm2",
    "sugestao_barras",
    "as_barras_cm2",
    "sobra_barras_percent",
    "espacamento_status",
    "espacamento_livre_cm",
    "largura_disponivel_cm",
    "largura_necessaria_cm",
    "status",
    "observacao",
    ]

def design_beams_from_envelope(
    model,
    envelope,
    csv_path,
    txt_path,
    fck_mpa=25.0,
    fyk_mpa=500.0,
    cover_m=0.03,
    stirrup_diameter_m=0.005,
    longitudinal_bar_diameter_m=0.0125,
):

    rows = create_beam_design_rows(
        model=model,
        envelope=envelope,
        fck_mpa=fck_mpa,
        fyk_mpa=fyk_mpa,
        cover_m=cover_m,
        stirrup_diameter_m=stirrup_diameter_m,
        longitudinal_bar_diameter_m=longitudinal_bar_diameter_m,
    )

    write_beam_design_csv(rows, csv_path)
    write_beam_design_summary(rows, txt_path, fck_mpa, fyk_mpa)


def create_beam_design_rows(
    model,
    envelope,
    fck_mpa,
    fyk_mpa,
    cover_m,
    stirrup_diameter_m,
    longitudinal_bar_diameter_m,
):
    """
    Cria as linhas de dimensionamento preliminar das vigas.
    """

    rows = []

    for element_envelope in envelope.get("elements", []):
        element_id = element_envelope["id"]
        element = model.get_element(element_id)

        if not is_horizontal_element(model, element):
            continue

        section = model.get_section(element.section)

        if section.b is None or section.h is None:
            rows.append(
                create_unavailable_row(
                    element_envelope,
                    "Seção sem b/h. Dimensionamento exige seção retangular.",
                )
            )
            continue

        moment_critical = get_element_moment_critical(element_envelope)

        if moment_critical is None:
            rows.append(
                create_unavailable_row(
                    element_envelope,
                    "Momento crítico não encontrado na envoltória.",
                )
            )
            continue

        b_m = float(section.b)
        h_m = float(section.h)

        d_m = calculate_effective_depth(
            h_m=h_m,
            cover_m=cover_m,
            stirrup_diameter_m=stirrup_diameter_m,
            longitudinal_bar_diameter_m=longitudinal_bar_diameter_m,
        )

        if d_m <= 0:
            rows.append(
                create_unavailable_row(
                    element_envelope,
                    "Altura útil inválida. Verifique cobrimento, estribo e diâmetro da barra.",
                )
            )
            continue

        moment_value = float(moment_critical["value"])
        moment_abs = float(moment_critical["abs_value"])
        moment_case = moment_critical["case"]

        flexure_result = design_rectangular_section_flexure(
            moment_kNm=moment_value,
            b_m=b_m,
            h_m=h_m,
            d_m=d_m,
            fck_mpa=fck_mpa,
            fyk_mpa=fyk_mpa,
        )

        as_calc_cm2 = flexure_result["results"]["as_calc_cm2"]
        as_min_cm2 = flexure_result["results"]["as_min_cm2"]
        as_max_cm2 = flexure_result["results"]["as_max_cm2"]
        as_adopted_cm2 = flexure_result["results"]["as_adopted_cm2"]
        rebar_options = select_rebar_options(as_adopted_cm2)
        best_rebar_option = rebar_options[0] if rebar_options else None

        spacing_check = None

        if best_rebar_option:
            spacing_check = check_single_layer_spacing(
                quantity=best_rebar_option["quantity"],
                diameter_mm=best_rebar_option["diameter_mm"],
                beam_width_m=b_m,
                cover_m=cover_m,
                stirrup_diameter_m=stirrup_diameter_m,
                )

        reinforcement_position = flexure_result["results"]["reinforcement_position"]
        status = flexure_result["status"]

        rows.append(
            {
                "elemento": element_id,
                "no_i": element_envelope.get("node_i"),
                "no_j": element_envelope.get("node_j"),
                "comprimento_m": format_number(element_envelope.get("length")),
                "b_m": format_number(b_m),
                "h_m": format_number(h_m),
                "d_m": format_number(d_m),
                "momento_critico_kNm": format_number(moment_value),
                "momento_abs_kNm": format_number(moment_abs),
                "caso_momento": moment_case,
                "posicao_armadura": reinforcement_position,
                "as_calculado_cm2": format_number(as_calc_cm2),
                "as_minimo_cm2": format_number(as_min_cm2),
                "as_maximo_cm2": format_number(as_max_cm2),
                "as_adotado_cm2": format_number(as_adopted_cm2),
                "sugestao_barras": (
                    best_rebar_option["label"] if best_rebar_option else ""
                ),
                "as_barras_cm2": (
                    format_number(best_rebar_option["total_area_cm2"])
                    if best_rebar_option
                    else ""
                ),
                "sobra_barras_percent": (
                    format_number(best_rebar_option["surplus_percent"])
                    if best_rebar_option
                    else ""),
                "espacamento_status": (
                    spacing_check["status"] if spacing_check else ""
                ),
                "espacamento_livre_cm": (
                    format_number(spacing_check["clear_spacing_m"] * 100.0)
                    if spacing_check
                    else ""
                ),
                "largura_disponivel_cm": (
                    format_number(spacing_check["available_width_m"] * 100.0)
                    if spacing_check
                    else ""
                ),
                "largura_necessaria_cm": (
                    format_number(spacing_check["required_width_m"] * 100.0)
                    if spacing_check
                    else ""
                ),
                "status": status,
                "observacao": (
                    f"Armadura {reinforcement_position}. "
                    "Cálculo preliminar com limites parametrizados; "
                    "verificações normativas completas ainda não implementadas."
                ),
            }
        )

    return rows


def calculate_effective_depth(
    h_m,
    cover_m,
    stirrup_diameter_m,
    longitudinal_bar_diameter_m,
):
    """
    Calcula a altura útil aproximada da seção.

    Modelo:
        d = h - cobrimento - diâmetro do estribo - metade do diâmetro da barra longitudinal

    Unidade:
        metros
    """

    return (
        float(h_m)
        - float(cover_m)
        - float(stirrup_diameter_m)
        - float(longitudinal_bar_diameter_m) / 2.0
    )


def is_horizontal_element(model, element, tolerance=1e-9):
    """
    Retorna True para elementos aproximadamente horizontais.
    """

    _, dy, _, _, _ = element.geometry(model)

    return abs(dy) <= tolerance


def get_element_moment_critical(element_envelope):
    """
    Retorna o maior momento absoluto entre moment_i e moment_j.
    """

    forces = element_envelope.get("forces", {})
    critical = None

    for force_key in ("moment_i", "moment_j"):
        if force_key not in forces:
            continue

        force_data = forces[force_key]

        candidate = {
            "force_key": force_key,
            "value": force_data["max_abs_value"],
            "abs_value": force_data["max_abs"],
            "case": force_data["max_abs_case"],
        }

        if critical is None or candidate["abs_value"] > critical["abs_value"]:
            critical = candidate

    return critical


def create_unavailable_row(element_envelope, observation):
    """
    Cria uma linha indicando que o dimensionamento não foi possível.
    """

    return {
        "elemento": element_envelope.get("id"),
        "no_i": element_envelope.get("node_i"),
        "no_j": element_envelope.get("node_j"),
        "comprimento_m": format_number(element_envelope.get("length")),
        "b_m": "",
        "h_m": "",
        "d_m": "",
        "momento_critico_kNm": "",
        "momento_abs_kNm": "",
        "caso_momento": "",
        "posicao_armadura": "",
        "as_calculado_cm2": "",
        "as_minimo_cm2": "",
        "as_maximo_cm2": "",
        "as_adotado_cm2": "",
        "sugestao_barras": "",
        "as_barras_cm2": "",
        "sobra_barras_percent": "",
        "espacamento_status": "",
        "espacamento_livre_cm": "",
        "largura_disponivel_cm": "",
        "largura_necessaria_cm": "",
        "status": "not_available",
        "observacao": observation,
    }


def write_beam_design_csv(rows, file_path):
    """
    Escreve o dimensionamento preliminar de vigas em CSV.
    """

    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with file_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=CSV_COLUMNS,
            delimiter=";",
        )

        writer.writeheader()
        writer.writerows(rows)


def write_beam_design_summary(rows, file_path, fck_mpa, fyk_mpa):
    """
    Escreve um resumo textual do dimensionamento preliminar.
    """

    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    lines = []

    lines.append("=" * 72)
    lines.append("DIMENSIONAMENTO PRELIMINAR DE VIGAS - MiniTQS")
    lines.append("=" * 72)
    lines.append("")
    lines.append("Base de cálculo:")
    lines.append("  Núcleo: core.norms.nbr6118.flexure")
    lines.append("  Tipo: flexão simples preliminar em seção retangular")
    lines.append("")
    lines.append("Hipóteses adotadas:")
    lines.append(f"  fck = {fck_mpa:.1f} MPa")
    lines.append(f"  fyk = {fyk_mpa:.1f} MPa")
    lines.append("  z ≈ 0.9*d")
    lines.append("  As = Md / (z*fyd)")
    lines.append("")
    lines.append("Aviso:")
    lines.append("  Este relatório é acadêmico e preliminar.")
    lines.append("  Ainda não substitui dimensionamento normativo completo.")
    lines.append("")
    lines.append("Verificações ainda não implementadas:")
    lines.append("  - linha neutra")
    lines.append("  - domínio de deformação")
    lines.append("  - ductilidade")
    lines.append("  - cortante")
    lines.append("  - ancoragem")
    lines.append("  - fissuração")
    lines.append("  - flecha")
    lines.append("  - número de camadas")
    lines.append("")
    lines.append("-" * 72)
    lines.append("Vigas analisadas")
    lines.append("-" * 72)

    if not rows:
        lines.append("Nenhuma viga horizontal encontrada.")
    else:
        for row in rows:
            lines.append("")
            lines.append(
                f"Elemento {row['elemento']} | nós {row['no_i']} -> {row['no_j']} "
                f"| L = {row['comprimento_m']} m"
            )

            if not row["as_adotado_cm2"]:
                lines.append(f"  Observação: {row['observacao']}")
                continue

            lines.append(
                f"  Momento crítico = {row['momento_critico_kNm']} kN.m "
                f"({row['caso_momento']})"
            )
            lines.append(
                f"  Seção = {row['b_m']} x {row['h_m']} m | d = {row['d_m']} m"
            )
            lines.append(
                f"  Posição da armadura = {row['posicao_armadura']}"
            )
            lines.append(
                f"  As calculado = {row['as_calculado_cm2']} cm²"
            )
            lines.append(
                f"  As mínimo = {row['as_minimo_cm2']} cm²"
            )
            lines.append(
                f"  As máximo = {row['as_maximo_cm2']} cm²"
            )
            lines.append(
                f"  As adotado = {row['as_adotado_cm2']} cm²"
            )
            lines.append(
                f"  Sugestão de barras = {row['sugestao_barras']}"
            )
            lines.append(
                f"  As das barras = {row['as_barras_cm2']} cm²"
            )
            lines.append(
                f"  Sobra de aço = {row['sobra_barras_percent']} %"
            )
            lines.append(
                f"  Verificação de espaçamento = {row['espacamento_status']}"
            )
            lines.append(
                f"  Espaçamento livre estimado = {row['espacamento_livre_cm']} cm"
            )
            lines.append(
                f"  Largura disponível = {row['largura_disponivel_cm']} cm"
            )
            lines.append(
                f"  Largura necessária = {row['largura_necessaria_cm']} cm"
            )
            lines.append(
                f"  Status = {row['status']}"
            )
            lines.append(
                f"  Observação: {row['observacao']}"
            )

    lines.append("")

    file_path.write_text("\n".join(lines), encoding="utf-8")


def format_number(value):
    """
    Formata número para saída em CSV/TXT.
    """

    if value is None:
        return ""

    return f"{float(value):.6f}"
