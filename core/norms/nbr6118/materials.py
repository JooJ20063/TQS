from core.norms.units import mpa_to_kn_m2


def concrete_design_strength_kn_m2(fck_mpa, gamma_c=1.4, alpha_cc=0.85):
    """
    Resistência de cálculo do concreto.

    Modelo usado:
        fcd = alpha_cc * fck / gamma_c

    Entrada:
        fck_mpa em MPa

    Saída:
        fcd em kN/m²

    Observação:
    Confirmar alpha_cc e gamma_c conforme a edição normativa adotada.
    """

    fck_mpa = float(fck_mpa)

    if fck_mpa <= 0:
        raise ValueError("fck deve ser positivo.")

    if gamma_c <= 0:
        raise ValueError("gamma_c deve ser positivo.")

    fcd_mpa = alpha_cc * fck_mpa / gamma_c

    return mpa_to_kn_m2(fcd_mpa)


def steel_design_strength_kn_m2(fyk_mpa, gamma_s=1.15):
    """
    Resistência de cálculo do aço.

    Modelo usado:
        fyd = fyk / gamma_s

    Entrada:
        fyk_mpa em MPa

    Saída:
        fyd em kN/m²

    Observação:
    Confirmar gamma_s conforme a edição normativa adotada.
    """

    fyk_mpa = float(fyk_mpa)

    if fyk_mpa <= 0:
        raise ValueError("fyk deve ser positivo.")

    if gamma_s <= 0:
        raise ValueError("gamma_s deve ser positivo.")

    fyd_mpa = fyk_mpa / gamma_s

    return mpa_to_kn_m2(fyd_mpa)
