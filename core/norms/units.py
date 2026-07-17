def mpa_to_kn_m2(value_mpa):
    """
    Converte MPa para kN/m².

    1 MPa = 1000 kN/m²
    """

    return float(value_mpa) * 1000.0


def m2_to_cm2(value_m2):
    """
    Converte m² para cm².
    """

    return float(value_m2) * 10000.0


def cm2_to_m2(value_cm2):
    """
    Converte cm² para m².
    """

    return float(value_cm2) / 10000.0


def knm_to_knm(value):
    """
    Mantém valor em kN.m.

    Função existe apenas para clareza semântica em relatórios.
    """

    return float(value)
