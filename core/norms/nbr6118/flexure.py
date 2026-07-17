from core.norms.config import default_abnt_config
from core.norms.units import m2_to_cm2
from core.norms.nbr6118.materials import (
    concrete_design_strength_kn_m2,
    steel_design_strength_kn_m2,
)


def design_rectangular_section_flexure(
    moment_kNm,
    b_m,
    h_m,
    d_m,
    fck_mpa=25.0,
    fyk_mpa=500.0,
    config=None,
):
    """
    Dimensionamento preliminar à flexão simples de seção retangular.

    Implementado nesta etapa:
    - cálculo de fcd;
    - cálculo de fyd;
    - estimativa de braço de alavanca z = 0.9*d;
    - cálculo de As,calc = Md/(z*fyd);
    - cálculo parametrizado de As,min;
    - cálculo parametrizado de As,max;
    - cálculo de As,adotada = max(As,calc, As,min);
    - verificação preliminar As,adotada <= As,max.

    Observação importante:
    Os parâmetros rho_min_beam_flexure e rho_max_beam_flexure devem ser
    conferidos com a edição oficial da norma adotada antes de qualquer uso técnico.
    """

    if config is None:
        config = default_abnt_config()

    moment_kNm = float(moment_kNm)
    b_m = float(b_m)
    h_m = float(h_m)
    d_m = float(d_m)

    validate_rectangular_flexure_inputs(
        b_m=b_m,
        h_m=h_m,
        d_m=d_m,
        fck_mpa=fck_mpa,
        fyk_mpa=fyk_mpa,
        config=config,
    )

    fcd_kn_m2 = concrete_design_strength_kn_m2(
        fck_mpa=fck_mpa,
        gamma_c=config.gamma_c,
        alpha_cc=config.alpha_cc,
    )

    fyd_kn_m2 = steel_design_strength_kn_m2(
        fyk_mpa=fyk_mpa,
        gamma_s=config.gamma_s,
    )

    moment_abs_kNm = abs(moment_kNm)
    z_m = 0.9 * d_m

    as_calc_m2 = calculate_required_steel_area(
        moment_kNm=moment_abs_kNm,
        z_m=z_m,
        fyd_kn_m2=fyd_kn_m2,
    )

    as_min_m2 = calculate_minimum_steel_area(
        b_m=b_m,
        h_m=h_m,
        rho_min=config.rho_min_beam_flexure,
    )

    as_max_m2 = calculate_maximum_steel_area(
        b_m=b_m,
        h_m=h_m,
        rho_max=config.rho_max_beam_flexure,
    )

    as_adopted_m2 = max(as_calc_m2, as_min_m2)

    reinforcement_position = "superior" if moment_kNm < 0 else "inferior"

    as_min_check = as_adopted_m2 >= as_min_m2
    as_max_check = as_adopted_m2 <= as_max_m2

    if as_min_check and as_max_check:
        status = "preliminary_ok"
    else:
        status = "preliminary_not_ok"

    return {
        "method": "flexure_rectangular_preliminary_with_limits",
        "code": config.concrete_code,
        "code_version": config.concrete_code_version,
        "mode": config.mode,

        "inputs": {
            "moment_kNm": moment_kNm,
            "b_m": b_m,
            "h_m": h_m,
            "d_m": d_m,
            "fck_mpa": float(fck_mpa),
            "fyk_mpa": float(fyk_mpa),
            "gamma_c": config.gamma_c,
            "gamma_s": config.gamma_s,
            "alpha_cc": config.alpha_cc,
            "rho_min_beam_flexure": config.rho_min_beam_flexure,
            "rho_max_beam_flexure": config.rho_max_beam_flexure,
        },

        "intermediate_results": {
            "fcd_kn_m2": fcd_kn_m2,
            "fyd_kn_m2": fyd_kn_m2,
            "z_m": z_m,
        },

        "results": {
            "as_calc_m2": as_calc_m2,
            "as_calc_cm2": m2_to_cm2(as_calc_m2),

            "as_min_m2": as_min_m2,
            "as_min_cm2": m2_to_cm2(as_min_m2),

            "as_max_m2": as_max_m2,
            "as_max_cm2": m2_to_cm2(as_max_m2),

            "as_adopted_m2": as_adopted_m2,
            "as_adopted_cm2": m2_to_cm2(as_adopted_m2),

            "reinforcement_position": reinforcement_position,
        },

        "checks": {
            "as_min": "ok" if as_min_check else "not_ok",
            "as_max": "ok" if as_max_check else "not_ok",
            "neutral_axis": "not_implemented",
            "ductility": "not_implemented",
            "shear": "not_implemented",
            "anchorage": "not_implemented",
            "crack_control": "not_implemented",
            "deflection": "not_implemented",
        },

        "status": status,
        "warning": (
            "Cálculo preliminar acadêmico com limites parametrizados. "
            "Parâmetros de armadura mínima e máxima devem ser conferidos "
            "com a edição oficial da norma adotada."
        ),
    }


def validate_rectangular_flexure_inputs(
    b_m,
    h_m,
    d_m,
    fck_mpa,
    fyk_mpa,
    config,
):
    """
    Valida entradas básicas da seção retangular.
    """

    if b_m <= 0:
        raise ValueError("b_m deve ser positivo.")

    if h_m <= 0:
        raise ValueError("h_m deve ser positivo.")

    if d_m <= 0:
        raise ValueError("d_m deve ser positivo.")

    if d_m >= h_m:
        raise ValueError("d_m deve ser menor que h_m.")

    if fck_mpa <= 0:
        raise ValueError("fck_mpa deve ser positivo.")

    if fyk_mpa <= 0:
        raise ValueError("fyk_mpa deve ser positivo.")

    if config.rho_min_beam_flexure < 0:
        raise ValueError("rho_min_beam_flexure não pode ser negativo.")

    if config.rho_max_beam_flexure <= 0:
        raise ValueError("rho_max_beam_flexure deve ser positivo.")

    if config.rho_min_beam_flexure > config.rho_max_beam_flexure:
        raise ValueError(
            "rho_min_beam_flexure não pode ser maior que rho_max_beam_flexure."
        )


def calculate_required_steel_area(moment_kNm, z_m, fyd_kn_m2):
    """
    Calcula As,calc.

    Unidade:
    - momento em kN.m
    - z em m
    - fyd em kN/m²
    - saída em m²
    """

    moment_kNm = float(moment_kNm)

    if moment_kNm <= 0:
        return 0.0

    return moment_kNm / (z_m * fyd_kn_m2)


def calculate_minimum_steel_area(b_m, h_m, rho_min):
    """
    Calcula As,min de forma parametrizada.

    Modelo:
        As,min = rho_min * Ac

    com:
        Ac = b*h
    """

    concrete_area_m2 = float(b_m) * float(h_m)

    return float(rho_min) * concrete_area_m2


def calculate_maximum_steel_area(b_m, h_m, rho_max):
    """
    Calcula As,max de forma parametrizada.

    Modelo:
        As,max = rho_max * Ac

    com:
        Ac = b*h
    """

    concrete_area_m2 = float(b_m) * float(h_m)

    return float(rho_max) * concrete_area_m2
