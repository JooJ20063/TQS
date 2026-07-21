from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


def write_column_critical_forces_3d_csv(
    report: dict[str, Any],
    output_path: str | Path,
) -> None:
    """
    Exporta esforços críticos de pilares 3D em CSV.
    """

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "element",
        "node_i",
        "node_j",
        "status",
        "length",
        "normal_value",
        "normal_abs",
        "normal_component",
        "normal_case",
        "shear_y_value",
        "shear_y_abs",
        "shear_z_value",
        "shear_z_abs",
        "torsion_value",
        "torsion_abs",
        "moment_y_value",
        "moment_y_abs",
        "moment_z_value",
        "moment_z_abs",
        "preliminary_index",
        "normal_ratio",
        "moment_y_ratio",
        "moment_z_ratio",
        "reason",
    ]

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for column in report.get("columns", []):
            forces = column.get("forces", {})
            index = column.get("preliminary_index", {})

            writer.writerow(
                {
                    "element": column.get("element"),
                    "node_i": column.get("node_i"),
                    "node_j": column.get("node_j"),
                    "status": column.get("status"),
                    "length": column.get("length", ""),
                    "normal_value": forces.get("normal", {}).get("value", ""),
                    "normal_abs": forces.get("normal", {}).get("abs_value", ""),
                    "normal_component": forces.get("normal", {}).get("component", ""),
                    "normal_case": forces.get("normal", {}).get("case", ""),
                    "shear_y_value": forces.get("shear_y", {}).get("value", ""),
                    "shear_y_abs": forces.get("shear_y", {}).get("abs_value", ""),
                    "shear_z_value": forces.get("shear_z", {}).get("value", ""),
                    "shear_z_abs": forces.get("shear_z", {}).get("abs_value", ""),
                    "torsion_value": forces.get("torsion", {}).get("value", ""),
                    "torsion_abs": forces.get("torsion", {}).get("abs_value", ""),
                    "moment_y_value": forces.get("moment_y", {}).get("value", ""),
                    "moment_y_abs": forces.get("moment_y", {}).get("abs_value", ""),
                    "moment_z_value": forces.get("moment_z", {}).get("value", ""),
                    "moment_z_abs": forces.get("moment_z", {}).get("abs_value", ""),
                    "preliminary_index": index.get("value", ""),
                    "normal_ratio": index.get("normal_ratio", ""),
                    "moment_y_ratio": index.get("moment_y_ratio", ""),
                    "moment_z_ratio": index.get("moment_z_ratio", ""),
                    "reason": column.get("reason", ""),
                }
            )
