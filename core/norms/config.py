from dataclasses import dataclass


@dataclass(frozen=True)
class DesignCodeConfig:
    """
    Configuração normativa usada pelo MiniTQS.

    Observação:
    Este projeto é acadêmico. As versões, coeficientes e hipóteses devem ser
    conferidos pelo usuário com as normas oficiais da ABNT.
    """

    concrete_code: str
    concrete_code_version: str

    actions_code: str
    actions_code_version: str

    combinations_code: str
    combinations_code_version: str

    wind_code: str
    wind_code_version: str

    mode: str = "academic"

    gamma_c: float = 1.4
    gamma_s: float = 1.15

    alpha_cc: float = 0.85


def default_abnt_config() -> DesignCodeConfig:
    """
    Retorna a configuração normativa padrão do MiniTQS.

    Importante:
    Confirmar as versões vigentes e os coeficientes adotados antes de usar
    em qualquer estudo técnico.
    """

    return DesignCodeConfig(
        concrete_code="ABNT NBR 6118",
        concrete_code_version="verificar edição vigente",
        actions_code="ABNT NBR 6120",
        actions_code_version="verificar edição vigente",
        combinations_code="ABNT NBR 8681",
        combinations_code_version="verificar edição vigente",
        wind_code="ABNT NBR 6123",
        wind_code_version="verificar edição vigente",
        mode="academic",
    )
