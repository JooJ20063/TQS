# core/envelope.py

FORCE_KEYS = (
    "normal_i",
    "shear_i",
    "moment_i",
    "normal_j",
    "shear_j",
    "moment_j",
)


def create_element_force_envelope(results_by_case):
    """
    Cria a envoltória de esforços de ponta dos elementos.

    Entrada:
        results_by_case = {
            "ELU_01": resultados_da_combinacao_1,
            "ELU_02": resultados_da_combinacao_2,
            ...
        }

    Saída:
        dict com, para cada elemento e esforço:
        - valor mínimo;
        - combinação/caso que gerou o mínimo;
        - valor máximo;
        - combinação/caso que gerou o máximo;
        - maior valor absoluto;
        - combinação/caso que gerou o maior absoluto.
    """

    if not results_by_case:
        raise ValueError("Não há resultados para gerar a envoltória.")

    envelope = {}

    for case_name, results in results_by_case.items():
        elements = results.get("elements", [])

        for element_result in elements:
            element_id = element_result["id"]
            local_end_forces = element_result.get("local_end_forces", {})

            if element_id not in envelope:
                envelope[element_id] = {
                    "id": element_id,
                    "node_i": element_result.get("node_i"),
                    "node_j": element_result.get("node_j"),
                    "length": element_result.get("length"),
                    "forces": {},
                }

            for force_key in FORCE_KEYS:
                if force_key not in local_end_forces:
                    continue

                value = float(local_end_forces[force_key])

                if force_key not in envelope[element_id]["forces"]:
                    envelope[element_id]["forces"][force_key] = _initial_force_envelope(
                        value,
                        case_name,
                    )

                _update_force_envelope(
                    envelope[element_id]["forces"][force_key],
                    value,
                    case_name,
                )

    return {
        "type": "element_force_envelope",
        "cases": list(results_by_case.keys()),
        "force_keys": list(FORCE_KEYS),
        "elements": [
            envelope[element_id]
            for element_id in sorted(envelope)
        ],
        "global_critical": _calculate_global_critical(envelope),
    }


def _initial_force_envelope(value, case_name):
    """Cria o registro inicial de envoltória para um esforço."""

    return {
        "min": value,
        "min_case": case_name,
        "max": value,
        "max_case": case_name,
        "max_abs": abs(value),
        "max_abs_value": value,
        "max_abs_case": case_name,
    }


def _update_force_envelope(force_envelope, value, case_name):
    """Atualiza mínimo, máximo e maior absoluto de um esforço."""

    if value < force_envelope["min"]:
        force_envelope["min"] = value
        force_envelope["min_case"] = case_name

    if value > force_envelope["max"]:
        force_envelope["max"] = value
        force_envelope["max_case"] = case_name

    if abs(value) > force_envelope["max_abs"]:
        force_envelope["max_abs"] = abs(value)
        force_envelope["max_abs_value"] = value
        force_envelope["max_abs_case"] = case_name


def _calculate_global_critical(envelope):
    """
    Calcula os esforços críticos globais da estrutura.

    Retorna o maior normal, cortante e momento em valor absoluto.
    """

    critical = {
        "normal": None,
        "shear": None,
        "moment": None,
    }

    force_groups = {
        "normal": ("normal_i", "normal_j"),
        "shear": ("shear_i", "shear_j"),
        "moment": ("moment_i", "moment_j"),
    }

    for element_id, element_envelope in envelope.items():
        forces = element_envelope["forces"]

        for group_name, keys in force_groups.items():
            for key in keys:
                if key not in forces:
                    continue

                candidate = {
                    "element": element_id,
                    "force_key": key,
                    "value": forces[key]["max_abs_value"],
                    "abs_value": forces[key]["max_abs"],
                    "case": forces[key]["max_abs_case"],
                }

                current = critical[group_name]

                if current is None or candidate["abs_value"] > current["abs_value"]:
                    critical[group_name] = candidate

    return critical
