# core/envelope_csv.py

from pathlib import Path
import csv


CSV_COLUMNS = [
    "elemento",
    "no_i",
    "no_j",
    "comprimento_m",

    "normal_posicao",
    "normal_valor_kN",
    "normal_abs_kN",
    "normal_caso",

    "cortante_posicao",
    "cortante_valor_kN",
    "cortante_abs_kN",
    "cortante_caso",

    "momento_posicao",
    "momento_valor_kNm",
    "momento_abs_kNm",
    "momento_caso",
]


def write_envelope_csv(envelope, file_path):
    """
    Escreve a envoltória de esforços em formato CSV.

    Cada linha representa um elemento estrutural.
    Para cada elemento, são salvos:
    - normal crítico;
    - cortante crítico;
    - momento crítico.
    """

    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    rows = create_envelope_csv_rows(envelope)

    with file_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=CSV_COLUMNS,
            delimiter=";",
        )

        writer.writeheader()
        writer.writerows(rows)


def create_envelope_csv_rows(envelope):
    """
    Cria as linhas da tabela CSV a partir da envoltória.
    """

    rows = []

    for element in envelope.get("elements", []):
        normal = get_element_group_critical(element, ("normal_i", "normal_j"))
        shear = get_element_group_critical(element, ("shear_i", "shear_j"))
        moment = get_element_group_critical(element, ("moment_i", "moment_j"))

        row = {
            "elemento": element.get("id"),
            "no_i": element.get("node_i"),
            "no_j": element.get("node_j"),
            "comprimento_m": format_number(element.get("length")),

            "normal_posicao": get_force_key(normal),
            "normal_valor_kN": get_force_value(normal),
            "normal_abs_kN": get_force_abs_value(normal),
            "normal_caso": get_force_case(normal),

            "cortante_posicao": get_force_key(shear),
            "cortante_valor_kN": get_force_value(shear),
            "cortante_abs_kN": get_force_abs_value(shear),
            "cortante_caso": get_force_case(shear),

            "momento_posicao": get_force_key(moment),
            "momento_valor_kNm": get_force_value(moment),
            "momento_abs_kNm": get_force_abs_value(moment),
            "momento_caso": get_force_case(moment),
        }

        rows.append(row)

    return rows


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


def get_force_key(critical):
    """
    Retorna a posição do esforço crítico.
    """

    if critical is None:
        return ""

    return critical["force_key"]


def get_force_value(critical):
    """
    Retorna o valor assinado do esforço crítico.
    """

    if critical is None:
        return ""

    return format_number(critical["value"])


def get_force_abs_value(critical):
    """
    Retorna o valor absoluto do esforço crítico.
    """

    if critical is None:
        return ""

    return format_number(critical["abs_value"])


def get_force_case(critical):
    """
    Retorna o caso/combinação que gerou o esforço crítico.
    """

    if critical is None:
        return ""

    return critical["case"]


def format_number(value):
    """
    Formata número para CSV mantendo ponto decimal.

    Isso facilita o uso em Python, LibreOffice, Excel e outros programas.
    """

    if value is None:
        return ""

    return f"{float(value):.6f}"
