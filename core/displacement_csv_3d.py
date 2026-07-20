from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Any


def write_displacements_3d_csv(
    results: dict[str, Any],
    output_path: str | Path,
) -> None:
    """
    Exporta deslocamentos 3D nodais em CSV.
    """

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "node",
        "x",
        "y",
        "z",
        "ux",
        "uy",
        "uz",
        "rx",
        "ry",
        "rz",
        "horizontal_resultant",
        "translation_resultant",
        "rotation_resultant",
    ]

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for record in results.get("displacements", []):
            ux = float(record.get("ux", 0.0))
            uy = float(record.get("uy", 0.0))
            uz = float(record.get("uz", 0.0))
            rx = float(record.get("rx", 0.0))
            ry = float(record.get("ry", 0.0))
            rz = float(record.get("rz", 0.0))

            writer.writerow(
                {
                    "node": record.get("node"),
                    "x": record.get("x", 0.0),
                    "y": record.get("y", 0.0),
                    "z": record.get("z", 0.0),
                    "ux": ux,
                    "uy": uy,
                    "uz": uz,
                    "rx": rx,
                    "ry": ry,
                    "rz": rz,
                    "horizontal_resultant": math.sqrt(ux**2 + uy**2),
                    "translation_resultant": math.sqrt(ux**2 + uy**2 + uz**2),
                    "rotation_resultant": math.sqrt(rx**2 + ry**2 + rz**2),
                }
            )
