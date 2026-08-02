import argparse
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str]) -> None:
    print("$", " ".join(cmd))
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main() -> None:
    parser = argparse.ArgumentParser(description="Actualiza stock y regenera dashboard")
    parser.add_argument("--url", required=True, help="URL del vendedor en MercadoLibre")
    parser.add_argument("--max-paginas", type=int, default=20, help="Tope de paginas a scrapear")
    parser.add_argument("--csv", default="stock.csv", help="Archivo CSV de salida")
    parser.add_argument("--html", default="dashboard.html", help="Archivo HTML del dashboard")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent

    run([
        sys.executable,
        str(root / "meli_vehiculos_scraper.py"),
        args.url,
        "--max-paginas",
        str(args.max_paginas),
        "--salida",
        str(root / args.csv),
    ])

    run([
        sys.executable,
        str(root / "visualizar_stock.py"),
        str(root / args.csv),
        "--salida",
        str(root / args.html),
    ])

    print("Actualizacion completada")


if __name__ == "__main__":
    main()
