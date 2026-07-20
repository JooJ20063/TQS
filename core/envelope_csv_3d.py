from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


def write_envelope_3d_csv(envelope: dict[str, Any], output_path: str | Path) -> None:
    """
    Exporta a envoltória 3D em CSV.

    Cada linha representa o valor crítico de um grupo de esforço em um elemento.
    """

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "element",
        "group",
        "min_value",
        "min_case",
        "min_component",
        "max_value",
        "max_case",
        "max_component",
        "abs_value",
        "abs_case",
        "abs_component",
    ]

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for element in envelope.get("elements", []):
            element_id = element["id"]

            for group_name, group in element.get("groups", {}).items():
                writer.writerow(
                    {
                        "element": element_id,
                        "group": group_name,
                        "min_value": group["min"]["value"],
                        "min_case": group["min"]["case"],
                        "min_component": group["min"]["component"],
                        "max_value": group["max"]["value"],
                        "max_case": group["max"]["case"],
                        "max_component": group["max"]["component"],
                        "abs_value": group["abs"]["value"],
                        "abs_case": group["abs"]["case"],
                        "abs_component": group["abs"]["component"],
                    }
                )
