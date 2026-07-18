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
    min_diameter_mm=10.0,
    max_bars=6,
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

        if diameter_mm < min_diameter_mm:
            continue

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
            option["quantity"],
            option["diameter_mm"],
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

def check_single_layer_spacing(
    quantity,
    diameter_mm,
    beam_width_m,
    cover_m=0.03,
    stirrup_diameter_m=0.005,
    min_clear_spacing_m=0.02,
):
    """
    Verifica, de forma preliminar, se uma quantidade de barras cabe em uma
    única camada horizontal da viga.

    Modelo simplificado:
    - considera cobrimento lateral;
    - considera diâmetro do estribo;
    - considera espaçamento livre mínimo parametrizado;
    - não verifica camadas múltiplas;
    - não verifica agregados;
    - não verifica ancoragem.

    Todas as dimensões principais estão em metros, exceto diameter_mm.
    """

    quantity = int(quantity)
    diameter_m = float(diameter_mm) / 1000.0
    beam_width_m = float(beam_width_m)

    if quantity <= 0:
        return {
            "status": "not_available",
            "available_width_m": 0.0,
            "required_width_m": 0.0,
            "clear_spacing_m": 0.0,
            "message": "Quantidade de barras inválida.",
        }

    available_width_m = beam_width_m - 2.0 * (float(cover_m) + float(stirrup_diameter_m))

    if quantity == 1:
        required_width_m = diameter_m
        clear_spacing_m = available_width_m
    else:
        required_width_m = quantity * diameter_m + (quantity - 1) * float(min_clear_spacing_m)
        clear_spacing_m = (available_width_m - quantity * diameter_m) / (quantity - 1)

    fits = required_width_m <= available_width_m

    return {
        "status": "ok" if fits else "not_ok",
        "available_width_m": available_width_m,
        "required_width_m": required_width_m,
        "clear_spacing_m": clear_spacing_m,
        "message": (
            "Barras cabem em uma camada."
            if fits
            else "Barras não cabem em uma camada com o espaçamento mínimo adotado."
        ),
    }
