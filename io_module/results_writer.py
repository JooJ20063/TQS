# io_module/results_writer.py

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any


def write_results_json(results: Any, file_path: str | Path) -> None:
    """Salva os resultados da análise em um arquivo JSON."""

    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    serializable_results = make_json_serializable(results)

    with file_path.open("w", encoding="utf-8") as file:
        json.dump(serializable_results, file, indent=4, ensure_ascii=False)


def make_json_serializable(obj: Any) -> Any:
    """Converte objetos Python/NumPy/dataclasses para algo compatível com JSON."""

    if obj is None:
        return None

    if isinstance(obj, (str, int, float, bool)):
        return obj

    if is_dataclass(obj):
        return make_json_serializable(asdict(obj))

    if isinstance(obj, dict):
        return {str(key): make_json_serializable(value) for key, value in obj.items()}

    if isinstance(obj, (list, tuple)):
        return [make_json_serializable(item) for item in obj]

    if hasattr(obj, "tolist"):
        return obj.tolist()

    return str(obj)
