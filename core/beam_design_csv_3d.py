from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


def write_beam_design_3d_csv(
    design: dict[str, Any],
    output_path: str | Path,
) -> None:
    """
    Exporta dimensionamento preliminar de vigas 3D em CSV.
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
        "b_m",
        "h_m",
        "my_kNm",
        "mz_kNm",
        "as_my_calc_cm2",
        "as_my_min_cm2",
        "as_my_req_cm2",
        "as_my_governing_reason",
        "as_mz_calc_cm2",
        "as_mz_min_cm2",
        "as_mz_req_cm2",
        "as_mz_governing_reason",
        "as_required_cm2",
        "critical_as_calculated_cm2",
        "critical_as_min_cm2",
        "critical_as_max_cm2",
        "critical_axis",
        "governing_reason",
        "reason",
        "warnings",
    ]

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for record in design.get("elements", []):
            design_my = record.get("design_my", {})
            design_mz = record.get("design_mz", {})

            writer.writerow(
                {
                    "element": record.get("element"),
                    "node_i": record.get("node_i"),
                    "node_j": record.get("node_j"),
                    "classification": record.get("classification"),
                    "status": record.get("status"),
                    "section": record.get("section", ""),
                    "b_m": record.get("b_m", ""),
                    "h_m": record.get("h_m", ""),
                    "my_kNm": record.get("my_kNm", ""),
                    "mz_kNm": record.get("mz_kNm", ""),
                    "as_my_calc_cm2": design_my.get("as_calculated_cm2", ""),
                    "as_my_min_cm2": design_my.get("as_min_cm2", ""),
                    "as_my_req_cm2": design_my.get("as_required_cm2", ""),
                    "as_my_governing_reason": design_my.get("governing_reason", ""),
                    "as_mz_calc_cm2": design_mz.get("as_calculated_cm2", ""),
                    "as_mz_min_cm2": design_mz.get("as_min_cm2", ""),
                    "as_mz_req_cm2": design_mz.get("as_required_cm2", ""),
                    "as_mz_governing_reason": design_mz.get("governing_reason", ""),
                    "as_required_cm2": record.get("as_required_cm2", ""),
                    "critical_as_calculated_cm2": record.get("critical_as_calculated_cm2", ""),
                    "critical_as_min_cm2": record.get("critical_as_min_cm2", ""),
                    "critical_as_max_cm2": record.get("critical_as_max_cm2", ""),
                    "critical_axis": record.get("critical_axis", ""),
                    "governing_reason": record.get("governing_reason", ""),
                    "reason": record.get("reason", ""),
                    "warnings": "; ".join(record.get("warnings", [])),
                }
            )
