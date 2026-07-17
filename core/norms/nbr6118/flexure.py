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

    Este módulo é uma primeira camada normativa/rastreável.

    Implementado nesta etapa:
    - identificação do momento solicitante de cálculo;
    - cálculo de fcd;
    - cálculo de fyd;
    - estimativa de braço de alavanca z = 0.9*d;
    - cálculo de As = Md/(z*fyd);
    - relatório explícito de hipóteses e verificações ainda não implementadas.

    Ainda não implementado:
    - verificação completa de domínio;
    - linha neutra;
    - momento resistente por bloco comprimido;
    - armadura mínima;
    - armadura máxima;
    - detalhamento;
    - ancoragem;
    - fissuração;
    - flecha;
    - cortante.

    Portanto, ainda não é um dimensionamento normativo completo.
    """

    if config is None:
        config = default_abnt_config()

    moment_kNm = float(moment_kNm)
    b_m = float(b_m)
    h_m = float(h_m)
    d_m = float(d_m)

    if b_m <= 0:
        raise ValueError("b_m deve ser positivo.")

    if h_m <= 0:
        raise ValueError("h_m deve ser positivo.")

    if d_m <= 0:
        raise ValueError("d_m deve ser positivo.")

    if d_m >= h_m:
        raise ValueError("d_m deve ser menor que h_m.")

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

    if moment_abs_kNm == 0:
        as_required_m2 = 0.0
    else:
        as_required_m2 = moment_abs_kNm / (z_m * fyd_kn_m2)

    reinforcement_position = "superior" if moment_kNm < 0 else "inferior"

    return {
        "method": "flexure_rectangular_preliminary",
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
        },

        "intermediate_results": {
            "fcd_kn_m2": fcd_kn_m2,
            "fyd_kn_m2": fyd_kn_m2,
            "z_m": z_m,
        },

        "results": {
            "as_required_m2": as_required_m2,
            "as_required_cm2": m2_to_cm2(as_required_m2),
            "reinforcement_position": reinforcement_position,
        },

        "checks": {
            "as_min": "not_implemented",
            "as_max": "not_implemented",
            "neutral_axis": "not_implemented",
            "ductility": "not_implemented",
            "shear": "not_implemented",
            "anchorage": "not_implemented",
            "crack_control": "not_implemented",
            "deflection": "not_implemented",
        },

        "status": "preliminary_not_complete",
        "warning": (
            "Cálculo preliminar acadêmico. "
            "Ainda não representa dimensionamento normativo completo."
        ),
    }
