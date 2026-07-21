from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


def write_beam_shear_torsion_3d_csv(
    report: dict[str, Any],
    output_path: str | Path,
) -> None:
    """
    Exporta relatório preliminar de cortante e torção em vigas 3D.
    """

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "element",
        "node_i",
        "node_j",
        "classification",
        "status",
        "section",
        "shear_y_kN",
        "shear_y_abs_kN",
        "shear_y_case",
        "shear_y_component",
        "shear_z_kN",
        "shear_z_abs_kN",
        "shear_z_case",
        "shear_z_component",
        "torsion_kNm",
        "torsion_abs_kNm",
        "torsion_case",
        "torsion_component",
        "preliminary_index",
        "preliminary_index_shear_y",
        "preliminary_index_shear_z",
        "preliminary_index_torsion",
        "reason",
    ]

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for record in report.get("elements", []):
            terms = record.get("preliminary_index_terms", {})

            writer.writerow(
                {
                    "element": record.get("element"),
                    "node_i": record.get("node_i"),
                    "node_j": record.get("node_j"),
                    "classification": record.get("classification"),
                    "status": record.get("status"),
                    "section": record.get("section", ""),
                    "shear_y_kN": record.get("shear_y_kN", ""),
                    "shear_y_abs_kN": record.get("shear_y_abs_kN", ""),
                    "shear_y_case": record.get("shear_y_case", ""),
                    "shear_y_component": record.get("shear_y_component", ""),
                    "shear_z_kN": record.get("shear_z_kN", ""),
                    "shear_z_abs_kN": record.get("shear_z_abs_kN", ""),
                    "shear_z_case": record.get("shear_z_case", ""),
                    "shear_z_component": record.get("shear_z_component", ""),
                    "torsion_kNm": record.get("torsion_kNm", ""),
                    "torsion_abs_kNm": record.get("torsion_abs_kNm", ""),
                    "torsion_case": record.get("torsion_case", ""),
                    "torsion_component": record.get("torsion_component", ""),
                    "preliminary_index": record.get("preliminary_index", ""),
                    "preliminary_index_shear_y": terms.get("shear_y", ""),
                    "preliminary_index_shear_z": terms.get("shear_z", ""),
                    "preliminary_index_torsion": terms.get("torsion", ""),
                    "reason": record.get("reason", ""),
                }
            )
