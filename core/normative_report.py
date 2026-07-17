from pathlib import Path


def write_normative_summary_txt(model, file_path):
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    text = create_normative_summary_text(model)

    file_path.write_text(text, encoding="utf-8")


def create_normative_summary_text(model):
    lines = []

    lines.append("=" * 72)
    lines.append("RESUMO NORMATIVO - MiniTQS")
    lines.append("=" * 72)
    lines.append("")

    append_design_code(lines, model)
    append_load_cases(lines, model)
    append_combinations(lines, model)
    append_warnings(lines)

    return "\n".join(lines) + "\n"


def append_design_code(lines, model):
    design_code = getattr(model, "design_code", {}) or {}

    lines.append("-" * 72)
    lines.append("Normas e modo de uso declarados")
    lines.append("-" * 72)

    append_design_code_line(
        lines,
        "Concreto armado",
        design_code.get("concrete_code"),
        design_code.get("concrete_code_version"),
    )

    append_design_code_line(
        lines,
        "Ações",
        design_code.get("actions_code"),
        design_code.get("actions_code_version"),
    )

    append_design_code_line(
        lines,
        "Combinações",
        design_code.get("combinations_code"),
        design_code.get("combinations_code_version"),
    )

    append_design_code_line(
        lines,
        "Vento",
        design_code.get("wind_code"),
        design_code.get("wind_code_version"),
    )

    mode = design_code.get("mode", "não informado")
    lines.append(f"Modo de uso: {mode}")
    lines.append("")


def append_design_code_line(lines, label, code, version):
    code_text = code if code else "não informado"
    version_text = version if version else "não informado"

    lines.append(f"{label}: {code_text} | versão: {version_text}")


def append_load_cases(lines, model):
    lines.append("-" * 72)
    lines.append("Casos de carregamento")
    lines.append("-" * 72)

    if not model.load_cases:
        lines.append("Nenhum caso de carregamento declarado.")
        lines.append("")
        return

    for load_case in model.load_cases:
        nodal_count = len(load_case.nodal_loads)
        distributed_count = len(load_case.distributed_loads)

        lines.append(
            f"{load_case.name}: "
            f"type = {load_case.type} | "
            f"cargas nodais = {nodal_count} | "
            f"cargas distribuídas = {distributed_count}"
        )

    lines.append("")


def append_combinations(lines, model):
    lines.append("-" * 72)
    lines.append("Combinações declaradas")
    lines.append("-" * 72)

    if not model.combinations:
        lines.append("Nenhuma combinação declarada.")
        lines.append("")
        return

    for combination in model.combinations:
        expression = format_combination_expression(combination.factors)
        lines.append(f"{combination.name} = {expression}")

    lines.append("")


def format_combination_expression(factors):
    terms = []

    for load_case_name, factor in factors.items():
        terms.append(f"{factor:g}*{load_case_name}")

    return " + ".join(terms)


def append_warnings(lines):
    lines.append("-" * 72)
    lines.append("Avisos")
    lines.append("-" * 72)
    lines.append(
        "As combinações ainda são declaradas manualmente no JSON. "
        "A geração automática de combinações normativas ainda não foi implementada."
    )
    lines.append(
        "Este relatório registra metadados normativos para rastreabilidade acadêmica."
    )
    lines.append("")
