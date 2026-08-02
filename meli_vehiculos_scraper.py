"""
Scraper de publicaciones de vehículos de un vendedor en MercadoLibre Argentina
=================================================================================
Pensado para páginas tipo:
    https://vehiculos.mercadolibre.com.ar/_CustId_163733823

Extrae por cada publicación: marca, modelo, versión, año, kilómetros,
precio y link. Guarda todo en CSV.

Uso:
    python meli_vehiculos_scraper.py https://vehiculos.mercadolibre.com.ar/_CustId_163733823 --salida stock.csv

Requisitos:
    pip install requests beautifulsoup4

IMPORTANTE - leer antes de correr:
- Esa URL puntual tiene el robots.txt cerrado para bots, así que no pude
  previsualizar el HTML en vivo para calibrar los selectores al pixel.
  El script usa las clases del Andes Design System (compartido en TODO
  mercadolibre.com.ar, no solo en vehículos), más extracción por texto
  (regex) para año/km, que aguanta mejor los cambios de CSS que ir a
  buscar una clase puntual.
- Si te tira 0 resultados o campos vacíos: abrí la página en el navegador,
  clic derecho sobre una publicación > Inspeccionar > Copiar > Copiar
  elemento, y pasame ese HTML para recalibrar los selectores.
- Paginación: se arma la URL de cada página directamente con el patrón
  _Desde_{offset}_CustId_{id}_NoIndex_True (confirmado a mano probando el
  botón "2" del paginador), 48 publicaciones por página. No usa el link
  "Siguiente" porque en esta página la paginación es por JavaScript
  (el href del botón viene vacío).
- Marca/Modelo/Versión se separan de forma heurística a partir del
  título (que en ML viene como "Marca Modelo Versión..."). Si el
  vendedor tiene autos de una marca de nombre compuesto que no está en
  MULTI_WORD_MARCAS (más abajo), agregala ahí.
"""

import argparse
import csv
import random
import re
import time
from dataclasses import dataclass, asdict
from typing import Optional

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-AR,es;q=0.9",
}

# Selectores en cascada: se prueba el primero, si no existe se pasa al siguiente.
ITEM_SELECTORS = [
    "li.ui-search-layout__item",
    "div.ui-search-result__wrapper",
    "div.ui-search-result",
]
TITLE_SELECTORS = [
    "a.poly-component__title",
    "h3.poly-component__title-wrapper",
    "h2.ui-search-item__title",
]
PRICE_SELECTORS = [
    "span.andes-money-amount__fraction",
    "span.price-tag-fraction",
]
LINK_SELECTORS = [
    "a.poly-component__title",
    "a.ui-search-link",
]

ITEMS_POR_PAGINA = 48  # confirmado probando el paginador a mano
CUSTID_RE = re.compile(r"_CustId_(\d+)")

# Marcas de más de una palabra, para no cortar el nombre a la mitad al separar título.
MULTI_WORD_MARCAS = {
    "alfa romeo", "mercedes benz", "land rover", "great wall",
    "aston martin", "mg motor",
}

YEAR_RE = re.compile(r"\b(19[5-9]\d|20[0-3]\d)\b")
KM_RE = re.compile(r"(\d[\d.]*)\s*[Kk][Mm]\b")


@dataclass
class Vehiculo:
    titulo: str
    marca: Optional[str]
    modelo: Optional[str]
    version: Optional[str]
    anio: Optional[str]
    kms: Optional[str]
    precio: Optional[str]
    link: str


def _first_text(item, selectors) -> Optional[str]:
    for sel in selectors:
        el = item.select_one(sel)
        if el and el.get_text(strip=True):
            return el.get_text(strip=True)
    return None


def _first_link(item, selectors) -> Optional[str]:
    for sel in selectors:
        el = item.select_one(sel)
        if el and el.get("href"):
            return el["href"]
    return None


def _find_items(soup: BeautifulSoup) -> list:
    for sel in ITEM_SELECTORS:
        items = soup.select(sel)
        if items:
            return items
    return []


def _split_titulo(titulo: str):
    """Separa marca / modelo / versión de forma heurística.
    Los títulos de ML de autos suelen venir como 'Marca Modelo Versión...'."""
    tokens = titulo.split()
    if not tokens:
        return None, None, None

    lower = titulo.lower()
    marca_tokens = 1
    for mw in MULTI_WORD_MARCAS:
        if lower.startswith(mw):
            marca_tokens = len(mw.split())
            break

    marca = " ".join(tokens[:marca_tokens]) if len(tokens) > marca_tokens else None
    modelo = tokens[marca_tokens] if len(tokens) > marca_tokens else None
    version = " ".join(tokens[marca_tokens + 1:]) if len(tokens) > marca_tokens + 1 else None
    return marca, modelo, version


def _extraer_anio(version: Optional[str], texto_item: str) -> Optional[str]:
    """Busca el año primero en 'version' (lo que queda después de marca+modelo).
    Esto evita confundir el año con modelos que son números (ej: Peugeot 2008,
    donde 'modelo' ya se llevó el '2008' y el año real -2019, por ej- queda en
    'version'). Si no aparece ahí, cae a buscar en todo el texto del item."""
    if version:
        m = YEAR_RE.search(version)
        if m:
            return m.group(1)
    m = YEAR_RE.search(texto_item)
    return m.group(1) if m else None


def _extraer_kms(texto_item: str) -> Optional[str]:
    km_match = KM_RE.search(texto_item)
    if km_match:
        return km_match.group(1)
    if re.search(r"\b0\s*[Kk][Mm]\b", texto_item):
        return "0"
    return None


def _limpiar_version(version: Optional[str], anio: Optional[str]) -> Optional[str]:
    """Si 'version' arranca repitiendo el año (caso normal: 'Marca Modelo Año Motor...'),
    lo saca para no duplicarlo con la columna 'anio'."""
    if not version:
        return version
    tokens = version.split()
    if tokens and anio and tokens[0] == anio:
        resto = " ".join(tokens[1:])
        return resto or None
    return version


def _construir_url_pagina(url_base: str, pagina: int) -> Optional[str]:
    """Arma la URL de la página N a partir de la URL inicial (página 1).
    MercadoLibre pagina estas páginas de vendedor con el patrón:
        https://vehiculos.mercadolibre.com.ar/_Desde_{offset}_CustId_{id}_NoIndex_True
    donde offset = (pagina-1)*48 + 1. Confirmado probando el botón "2" a mano:
    el href del paginador viene vacío (es JS), pero la URL de la barra de
    direcciones sí cambia a ese patrón."""
    if pagina == 1:
        return url_base
    m = CUSTID_RE.search(url_base)
    if not m:
        return None
    cust_id = m.group(1)
    offset = (pagina - 1) * ITEMS_POR_PAGINA + 1
    return f"https://vehiculos.mercadolibre.com.ar/_Desde_{offset}_CustId_{cust_id}_NoIndex_True"


def scrapear(url_inicial: str, max_paginas: int = 20, delay_range=(1.5, 3.0)) -> list:
    vehiculos = []
    pagina = 1

    while pagina <= max_paginas:
        url = _construir_url_pagina(url_inicial, pagina)
        if not url:
            print("No pude armar la URL de esta página (¿la URL inicial tiene '_CustId_'?).")
            break

        print(f"Página {pagina}: {url}")
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"  Error de request: {e}")
            break

        soup = BeautifulSoup(resp.text, "html.parser")
        items = _find_items(soup)
        if not items:
            print("  No se encontraron publicaciones, corto acá.")
            break

        for item in items:
            titulo = _first_text(item, TITLE_SELECTORS)
            if not titulo:
                continue  # probablemente no es una publicación real (banner, etc)
            precio = _first_text(item, PRICE_SELECTORS)
            link = _first_link(item, LINK_SELECTORS) or ""
            texto_item = item.get_text(" ", strip=True)
            marca, modelo, version = _split_titulo(titulo)
            anio = _extraer_anio(version, texto_item)
            kms = _extraer_kms(texto_item)
            version = _limpiar_version(version, anio)
            vehiculos.append(Vehiculo(titulo, marca, modelo, version, anio, kms, precio, link))

        pagina += 1
        if pagina <= max_paginas:
            time.sleep(random.uniform(*delay_range))  # para no bombardear el servidor

    return vehiculos


def guardar_csv(vehiculos: list, salida: str):
    campos = ["titulo", "marca", "modelo", "version", "anio", "kms", "precio", "link"]
    with open(salida, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        for v in vehiculos:
            writer.writerow(asdict(v))
    print(f"Guardados {len(vehiculos)} vehículos en {salida}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Scraper de publicaciones de vehículos de un vendedor en MercadoLibre Argentina"
    )
    parser.add_argument("url", help="URL del vendedor, ej: https://vehiculos.mercadolibre.com.ar/_CustId_163733823")
    parser.add_argument("--max-paginas", type=int, default=20, help="Tope de páginas a recorrer (por las dudas)")
    parser.add_argument("--salida", default="stock_vehiculos.csv", help="Nombre del archivo CSV de salida")
    args = parser.parse_args()

    resultados = scrapear(args.url, args.max_paginas)
    guardar_csv(resultados, args.salida)