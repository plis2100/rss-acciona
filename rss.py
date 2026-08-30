import json
import urllib.request
import xml.etree.ElementTree as ET

from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from urllib.parse import urljoin

WEB_URL = "https://www.acciona.com/es/actualidad/noticias"

API_URL = (
    "https://www.acciona.com/content/accionacom/es/"
    "actualidad/noticias/jcr:content.filter.json"
    "?filter=news&page=1&pageSize=50"
)

OUTPUT_FILE = Path("acciona.xml")


def descargar_noticias():
    solicitud = urllib.request.Request(
        API_URL,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/124 Safari/537.36"
            ),
            "Accept": "application/json",
        },
    )

    with urllib.request.urlopen(solicitud, timeout=60) as respuesta:
        datos = json.loads(respuesta.read().decode("utf-8"))

    return datos.get("data", [])


def crear_rss(noticias):
    rss = ET.Element(
        "rss",
        {
            "version": "2.0",
            "xmlns:atom": "http://www.w3.org/2005/Atom",
        },
    )

    canal = ET.SubElement(rss, "channel")

    ET.SubElement(canal, "title").text = "Noticias de ACCIONA"
    ET.SubElement(canal, "link").text = WEB_URL
    ET.SubElement(canal, "description").text = (
        "Últimas noticias publicadas por ACCIONA"
    )
    ET.SubElement(canal, "language").text = "es"
    ET.SubElement(canal, "lastBuildDate").text = format_datetime(
        datetime.now(timezone.utc)
    )

    enlace_atom = ET.SubElement(
        canal,
        "{http://www.w3.org/2005/Atom}link",
    )
    enlace_atom.set("href", WEB_URL)
    enlace_atom.set("rel", "self")
    enlace_atom.set("type", "application/rss+xml")

    for noticia in noticias:
        titulo = noticia.get("title", "").strip()
        enlace = urljoin(WEB_URL, noticia.get("url", ""))
        descripcion = noticia.get("description", "").strip()
        fecha = noticia.get("date", "").strip()

        categorias = noticia.get("solutions", [])
        nombres_categorias = []

        for categoria in categorias:
            nombre = categoria.get("text", "").strip()

            if nombre:
                nombres_categorias.append(nombre)

        if not titulo or not enlace:
            continue

        elemento = ET.SubElement(canal, "item")

        ET.SubElement(elemento, "title").text = titulo
        ET.SubElement(elemento, "link").text = enlace
        ET.SubElement(elemento, "description").text = descripcion

        for categoria in nombres_categorias:
            ET.SubElement(elemento, "category").text = categoria

        identificador = ET.SubElement(elemento, "guid")
        identificador.set("isPermaLink", "true")
        identificador.text = enlace

        if fecha:
            try:
                fecha_publicacion = datetime.strptime(
                    fecha, "%Y-%m-%d"
                ).replace(tzinfo=timezone.utc)

                ET.SubElement(elemento, "pubDate").text = format_datetime(
                    fecha_publicacion
                )
            except ValueError:
                pass

    ET.indent(rss, space="  ")

    arbol = ET.ElementTree(rss)
    arbol.write(
        OUTPUT_FILE,
        encoding="utf-8",
        xml_declaration=True,
    )


def main():
    noticias = descargar_noticias()

    if not noticias:
        raise RuntimeError("No se encontraron noticias de ACCIONA")

    crear_rss(noticias)

    print(f"RSS creada correctamente con {len(noticias)} noticias")


if __name__ == "__main__":
    main()
