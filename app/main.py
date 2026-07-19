# app/main.py

from pathlib import Path
import argparse
import sys

# Adiciona a raiz do projeto ao caminho de importação do Python
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


def run_single_analysis(model, output_dir: Path) -> dict:
    """
    Executa uma análise individual:
    - valida modelo;
    - escolhe solver conforme analysis_type;
    - salva JSON;
    - gera diagramas apenas para frame2d.
    """

    if getattr(model, "analysis_type", "frame2d") == "frame3d":
        return run_single_analysis_3d(model, output_dir)

    return run_single_analysis_2d(model, output_dir)

def run_single_analysis_2d(model, output_dir: Path) -> dict:
    """
    Executa uma análise 2D.
    """

    from core.validation import validate_model
    from core.solver import solve_structure
    from core.postprocess import enrich_results, print_analysis_summary
    from io_module.results_writer import write_results_json
    from plots.diagrams import generate_all_diagrams

    output_dir.mkdir(parents=True, exist_ok=True)

    print("[3/5] Validando e resolvendo modelo estrutural...")

    validate_model(model)
    results = solve_structure(model)

    results = enrich_results(model, results)
    print_analysis_summary(results)

    print("[4/5] Salvando resultados...")

    write_results_json(results, output_dir / "resultados.json")

    print("[5/5] Gerando resultados gráficos...")

    generate_all_diagrams(model, results, output_dir)

    return results


def run_single_analysis_3d(model, output_dir: Path) -> dict:
    """
    Executa uma análise 3D.

    Nesta etapa:
    - resolve com solver_3d;
    - salva JSON;
    - não gera diagramas;
    - não roda pós-processamento 2D.
    """

    from core.validation import validate_model
    from core.solver_3d import solve_structure_3d
    from io_module.results_writer import write_results_json

    output_dir.mkdir(parents=True, exist_ok=True)

    print("[3/5] Validando e resolvendo modelo estrutural 3D...")

    validate_model(model)
    results = solve_structure_3d(model)

    print_analysis_summary_3d(results)

    print("[4/5] Salvando resultados...")

    write_results_json(results, output_dir / "resultados.json")

    print("[5/5] Diagramas 3D ainda não implementados.")

    return results


def print_analysis_summary_3d(results: dict) -> None:
    """
    Imprime um resumo simples da análise 3D.
    """

    print()
    print("-" * 60)
    print("Resumo da análise 3D")
    print("-" * 60)
    print(f"Nós:               {results['number_of_nodes']}")
    print(f"Elementos:         {results['number_of_elements']}")
    print(f"Graus de liberdade:{results['number_of_dofs']}")

    displacement_entry = find_max_abs_result_entry(
        rows=results["displacements"],
        keys=("ux", "uy", "uz"),
    )

    rotation_entry = find_max_abs_result_entry(
        rows=results["displacements"],
        keys=("rx", "ry", "rz"),
    )

    print()
    print("Deslocamentos máximos:")

    if displacement_entry:
        print(
            f"  |{displacement_entry['key']}|max = "
            f"{displacement_entry['value']:.6e} m no nó {displacement_entry['node']}"
        )

    if rotation_entry:
        print(
            f"  |{rotation_entry['key']}|max = "
            f"{rotation_entry['value']:.6e} rad no nó {rotation_entry['node']}"
        )


def find_max_abs_result_entry(rows, keys):
    """
    Procura o maior valor absoluto em uma lista de dicionários.
    """

    best = None

    for row in rows:
        for key in keys:
            value = float(row.get(key, 0.0))

            candidate = {
                "node": row.get("node"),
                "key": key,
                "value": value,
                "abs_value": abs(value),
            }

            if best is None or candidate["abs_value"] > best["abs_value"]:
                best = candidate

    return best


def run_analysis(input_file: Path, output_dir: Path) -> None:
    """
    Executa a análise estrutural a partir de um arquivo JSON.

    Suporta:
    - modelo simples com nodal_loads/distributed_loads;
    - load_cases;
    - combinations.
    """

    if not input_file.exists():
        raise FileNotFoundError(f"Arquivo de entrada não encontrado: {input_file}")

    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Estruturalis - Análise Estrutural")
    print("=" * 60)
    print(f"Arquivo de entrada: {input_file}")
    print(f"Pasta de saída:      {output_dir}")
    print()

    print("[1/5] Lendo modelo estrutural...")

    from io_module.json_reader import read_model_from_json
    from core.normative_report import write_normative_summary_txt

    model = read_model_from_json(input_file)
    print(f"Tipo de análise: {model.analysis_type}")

    normative_summary_path = output_dir / "resumo_normativo.txt"
    write_normative_summary_txt(model, normative_summary_path)

    print(f"Resumo normativo salvo em: {normative_summary_path}")
    print()


    print("[2/5] Preparando análises...")

    from core.load_cases import (
        has_combinations,
        has_load_cases,
        build_model_for_combination,
        build_model_for_load_case,
    )

    if has_combinations(model):
        print(f"Foram encontradas {len(model.combinations)} combinações.")
        print()

        combination_results = {}

        for combination in model.combinations:
            print("=" * 60)
            print(f"Analisando combinação: {combination.name}")
            print("=" * 60)

            combined_model = build_model_for_combination(model, combination)
            combination_output_dir = output_dir / combination.name

            results = run_single_analysis(combined_model, combination_output_dir)
            combination_results[combination.name] = results

            print()
            print(f"Resultados da combinação salvos em: {combination_output_dir}")
            print()

        if model.analysis_type == "frame3d":
            print("=" * 60)
            print("Envoltória e dimensionamento 3D ainda não implementados.")
            print("=" * 60)
            print("Resultados 3D das combinações foram salvos nas subpastas.")
            print()
            return

        print("=" * 60)
        print("Gerando envoltória de esforços")
        print("=" * 60)

        from core.envelope import create_element_force_envelope
        from core.envelope_report import write_envelope_summary_txt
        from core.envelope_csv import write_envelope_csv
        from core.beam_design import design_beams_from_envelope
        from io_module.results_writer import write_results_json

        envelope = create_element_force_envelope(combination_results)

        envelope_json_path = output_dir / "envoltoria.json"
        envelope_summary_path = output_dir / "resumo_envoltoria.txt"
        envelope_csv_path = output_dir / "envoltoria_elementos.csv"

        beam_design_csv_path = output_dir / "dimensionamento_vigas.csv"
        beam_design_summary_path = output_dir / "resumo_dimensionamento_vigas.txt"

        write_results_json(envelope, envelope_json_path)
        write_envelope_summary_txt(envelope, envelope_summary_path)
        write_envelope_csv(envelope, envelope_csv_path)

        design_beams_from_envelope(
            model=model,
            envelope=envelope,
            csv_path=beam_design_csv_path,
            txt_path=beam_design_summary_path,
        )

        print(f"Envoltória salva em: {envelope_json_path}")
        print(f"Resumo da envoltória salvo em: {envelope_summary_path}")
        print(f"CSV da envoltória salvo em: {envelope_csv_path}")
        print(f"Dimensionamento preliminar de vigas salvo em: {beam_design_csv_path}")
        print(f"Resumo do dimensionamento de vigas salvo em: {beam_design_summary_path}")
        print()

    elif has_load_cases(model):
        print(f"Foram encontrados {len(model.load_cases)} casos de carregamento.")
        print()

        for load_case in model.load_cases:
            print("=" * 60)
            print(f"Analisando caso de carregamento: {load_case.name}")
            print("=" * 60)

            case_model = build_model_for_load_case(model, load_case.name)
            case_output_dir = output_dir / load_case.name

            run_single_analysis(case_model, case_output_dir)

            print()
            print(f"Resultados do caso salvos em: {case_output_dir}")
            print()

    else:
        print("Modelo sem load_cases/combinations. Rodando análise única.")
        print()

        run_single_analysis(model, output_dir)

    print()
    print("Análise concluída com sucesso!")
    print(f"Resultados salvos em: {output_dir}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="MiniTQS",
        description="Mini software didático de análise estrutural 2D."
    )

    parser.add_argument(
        "input",
        type=str,
        help="Caminho para o arquivo JSON do modelo estrutural."
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="results",
        help="Pasta onde os resultados serão salvos. Padrão: results"
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    input_file = Path(args.input)
    output_dir = Path(args.output)

    try:
        run_analysis(input_file, output_dir)
        return 0

    except Exception as error:
        print()
        print("Erro durante a análise:")
        print(error)
        return 1


if __name__ == "__main__":
    sys.exit(main())
