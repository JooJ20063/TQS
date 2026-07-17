# core/envelope_report.py

from pathlib import Path


FORCE_LABELS = {
    "normal_i": "Normal no nó i",
    "normal_j": "Normal no nó j",
    "shear_i": "Cortante no nó i",
    "shear_j": "Cortante no nó j",
    "moment_i": "Momento no nó i",
    "moment_j": "Momento no nó j",
}


def write_envelope_summary_txt(envelope, file_path):
    """
    Escreve um resumo textual da envoltória de esforços.
    """

    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    text = create_envelope_summary_text(envelope)

    file_path.write_text(text, encoding="utf-8")


def create_envelope_summary_text(envelope):
    """
    Cria o texto completo do resumo da envoltória.
    """

    lines = []

    lines.append("=" * 72)
    lines.append("ENVOLTÓRIA DE ESFORÇOS - MiniTQS")
    lines.append("=" * 72)
    lines.append("")

    append_cases(lines, envelope)
    append_global_critical(lines, envelope)
    append_element_summaries(lines, envelope)

    return "\n".join(lines) + "\n"


def append_cases(lines, envelope):
    """
    Adiciona as combinações/casos analisados ao resumo.
    """

    cases = envelope.get("cases", [])

    lines.append("Combinações/casos analisados:")

    if not cases:
        lines.append("  Nenhum caso informado.")
    else:
        for case_name in cases:
            lines.append(f"  - {case_name}")

    lines.append("")


def append_global_critical(lines, envelope):
    """
    Adiciona os esforços críticos globais.
    """

    global_critical = envelope.get("global_critical", {})

    lines.append("-" * 72)
    lines.append("Críticos globais")
    lines.append("-" * 72)

    labels = {
        "normal": "Normal",
        "shear": "Cortante",
        "moment": "Momento",
    }

    for group_name, label in labels.items():
        critical = global_critical.get(group_name)

        if critical is None:
            lines.append(f"{label}: não encontrado.")
            continue

        force_key = critical["force_key"]
        value = critical["value"]
        abs_value = critical["abs_value"]
        element = critical["element"]
        case = critical["case"]

        lines.append(
            f"{label}: elemento {element}, "
            f"{FORCE_LABELS.get(force_key, force_key)}, "
            f"valor = {format_force_value(force_key, value)}, "
            f"|valor| = {format_force_value(force_key, abs_value)}, "
            f"combinação/caso = {case}"
        )

    lines.append("")


def append_element_summaries(lines, envelope):
    """
    Adiciona um resumo por elemento.
    """

    elements = envelope.get("elements", [])

    lines.append("-" * 72)
    lines.append("Resumo por elemento")
    lines.append("-" * 72)

    if not elements:
        lines.append("Nenhum elemento encontrado.")
        lines.append("")
        return

    for element in elements:
        element_id = element["id"]
        node_i = element.get("node_i")
        node_j = element.get("node_j")
        length = element.get("length")

        if length is None:
            length_text = "não informado"
        else:
            length_text = f"{length:.3f} m"

        lines.append("")
        lines.append(
            f"Elemento {element_id} | nós {node_i} -> {node_j} | L = {length_text}"
        )

        normal = get_element_group_critical(element, ("normal_i", "normal_j"))
        shear = get_element_group_critical(element, ("shear_i", "shear_j"))
        moment = get_element_group_critical(element, ("moment_i", "moment_j"))

        append_element_critical_line(lines, "Normal crítico", normal)
        append_element_critical_line(lines, "Cortante crítico", shear)
        append_element_critical_line(lines, "Momento crítico", moment)

    lines.append("")


def get_element_group_critical(element, force_keys):
    """
    Retorna o maior valor absoluto de um grupo de esforços em um elemento.
    """

    forces = element.get("forces", {})
    critical = None

    for force_key in force_keys:
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


def append_element_critical_line(lines, label, critical):
    """
    Adiciona uma linha de esforço crítico de um elemento.
    """

    if critical is None:
        lines.append(f"  {label}: não encontrado.")
        return

    force_key = critical["force_key"]
    value = critical["value"]
    case = critical["case"]

    lines.append(
        f"  {label}: "
        f"{FORCE_LABELS.get(force_key, force_key)} = "
        f"{format_force_value(force_key, value)} "
        f"({case})"
    )


def format_force_value(force_key, value):
    """
    Formata valor com unidade adequada.
    """

    if force_key.startswith("moment"):
        return f"{value:.3f} kN.m"

    return f"{value:.3f} kN"
