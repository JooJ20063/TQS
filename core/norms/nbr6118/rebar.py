# core/norms/nbr6118/rebar.py

import math


DEFAULT_BAR_DIAMETERS_MM = (
    6.3,
    8.0,
    10.0,
    12.5,
    16.0,
    20.0,
    25.0,
    32.0,
)


def bar_area_cm2(diameter_mm):
    """
    Calcula a área de uma barra em cm².

    Entrada:
    - diâmetro em mm

    Saída:
    - área em cm²
    """

    diameter_cm = float(diameter_mm) / 10.0

    return math.pi * diameter_cm**2 / 4.0


def select_rebar_options(
    as_required_cm2,
    diameters_mm=DEFAULT_BAR_DIAMETERS_MM,
    max_bars=8,
    max_options=5,
):
    """
    Seleciona opções preliminares de armadura longitudinal.

    Critério:
    - testa combinações com barras de mesmo diâmetro;
    - aceita opções cuja área total seja maior ou igual à As requerida;
    - ordena pela menor sobra de aço;
    - retorna as melhores opções.

    Observação:
    Esta função não verifica espaçamento, cobrimento, camadas, ancoragem
    nem detalhamento completo.
    """

    as_required_cm2 = float(as_required_cm2)

    if as_required_cm2 <= 0:
        return []

    options = []

    for diameter_mm in diameters_mm:
        single_area_cm2 = bar_area_cm2(diameter_mm)

        for quantity in range(1, max_bars + 1):
            total_area_cm2 = quantity * single_area_cm2

            if total_area_cm2 >= as_required_cm2:
                surplus_cm2 = total_area_cm2 - as_required_cm2
                surplus_percent = 100.0 * surplus_cm2 / as_required_cm2

                options.append(
                    {
                        "quantity": quantity,
                        "diameter_mm": diameter_mm,
                        "single_area_cm2": single_area_cm2,
                        "total_area_cm2": total_area_cm2,
                        "surplus_cm2": surplus_cm2,
                        "surplus_percent": surplus_percent,
                        "label": format_rebar_label(quantity, diameter_mm),
                    }
                )

                break

    options.sort(
        key=lambda option: (
            option["surplus_cm2"],
            option["diameter_mm"],
            option["quantity"],
        )
    )

    return options[:max_options]


def format_rebar_label(quantity, diameter_mm):
    """
    Formata uma opção de armadura.

    Exemplo:
    2Ø16
    3Ø12.5
    """

    diameter_text = format_diameter(diameter_mm)

    return f"{quantity}Ø{diameter_text}"


def format_diameter(diameter_mm):
    diameter_mm = float(diameter_mm)

    if diameter_mm.is_integer():
        return str(int(diameter_mm))

    return str(diameter_mm).replace(".", ",")
