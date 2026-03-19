from pathlib import Path
import re
from tempfile import NamedTemporaryFile

from fpdf import FPDF
from pypdf import PdfReader, PdfWriter, Transformation

# =========================
# CONFIGURACIÓN (EDITABLE)
# =========================
# 1) Ruta de imágenes para páginas con fondo BLANCO.
CARPETA_IMAGENES_FONDO_BLANCO = Path(r"c:\Users\adrip\OneDrive\Desktop\SAMURAIS_BLANCO")

# 1b) Ruta de imágenes para páginas con fondo ANTRACITA (no negro 100%).
#     Si no existe, el script la omite sin fallar.
CARPETA_IMAGENES_FONDO_NEGRO = Path(r"c:\Users\adrip\OneDrive\Desktop\SAMURAIS_NEGRO")

# 2) ÚNICA salida final: PDF impuesto para folleto en hoja SRA4.
PDF_SALIDA_FOLLETO_SRA4 = Path("catalogo_ropa_folleto_sra4.pdf")

# 2b) Mantener archivo temporal de páginas A5 (solo para diagnóstico).
#     Normalmente se elimina al terminar.
CONSERVAR_PDF_TEMPORAL_A5 = False

# 3) Ancho fijo de imagen en milímetros.
#    Si quieres imágenes más grandes o pequeñas, modifica este valor.
ANCHO_IMAGEN_MM = 120

# 4) Modo prueba: si está en True, solo genera el PDF con la primera imagen.
#    Ponlo en False para volver a incluir todas las imágenes.
SOLO_PRIMERA_IMAGEN = False

# 4b) Orden inicial de páginas:
#     define si el catálogo empieza por las imágenes de carpeta blanco o negro.
ORDEN_BLANCO_PRIMERO = True

# 5) Tipografía estilo Codec Pro:
#    - Si tienes el archivo .ttf de Codec Pro, pon aquí su ruta exacta.
#    - Si no existe, el script intentará usar Bahnschrift (Windows) como alternativa.
RUTA_FUENTE_CODEC_PRO = Path(r"C:\RUTA\A\CodecPro-Regular.ttf")

# 6) Ajustes de estilo fashion (más agresivo)
TITULO_TAMANO = 20
TITULO_ALTURA_LINEA_MM = 7
TITULO_TRACKING = 1.0

PIE_TAMANO = 9
PIE_TRACKING = 0.8

# 7) Tamaños de imposición y corte
SRA4_ANCHO_MM = 320
SRA4_ALTO_MM = 225
A4_ANCHO_MM = 297
A4_ALTO_MM = 210
LONGITUD_MARCA_CORTE_MM = 4

EXTENSIONES_VALIDAS = {".jpg", ".jpeg", ".png"}


class CatalogoPDF(FPDF):
    def __init__(self) -> None:
        super().__init__(orientation="P", unit="mm", format="A5")
        self.set_auto_page_break(auto=False)
        self.fuente_titulo = "Helvetica"
        self.fuente_pie = "Helvetica"
        self.numero_visible_por_pagina: dict[int, int] = {}

    def registrar_numero_visible(self, numero_visible: int) -> None:
        self.numero_visible_por_pagina[self.page_no()] = numero_visible

    def footer(self) -> None:
        self.set_y(-15)
        self.set_draw_color(220, 220, 220)
        self.set_line_width(0.3)
        self.line(18, self.get_y(), self.w - 18, self.get_y())

        self.ln(3)
        if self.fuente_pie == "Helvetica":
            self.set_font("Helvetica", size=PIE_TAMANO)
        else:
            self.set_font(self.fuente_pie, size=PIE_TAMANO)
        self.set_text_color(70, 70, 70)
        if hasattr(self, "set_char_spacing"):
            self.set_char_spacing(PIE_TRACKING)

        numero_visible = self.numero_visible_por_pagina.get(self.page_no(), self.page_no())
        numero_pagina = f"{numero_visible:02d}"
        self.cell(0, 6, f"{numero_pagina}", align="C")

        if hasattr(self, "set_char_spacing"):
            self.set_char_spacing(0)


def formatear_titulo_archivo(imagen_path: Path) -> str:
    nombre = imagen_path.stem
    nombre = re.sub(r"[_\-.]+", " ", nombre)
    nombre = re.sub(r"(?<=[a-záéíóúñ0-9])(?=[A-ZÁÉÍÓÚÑ])", " ", nombre)
    nombre = re.sub(r"\s+", " ", nombre).strip()
    return nombre.upper()


def configurar_fuentes_moderna(pdf: CatalogoPDF) -> None:
    rutas_fuente = [
        RUTA_FUENTE_CODEC_PRO,
        Path(r"C:\Windows\Fonts\bahnschrift.ttf"),
        Path(r"C:\Windows\Fonts\BAHNSCHRIFT.TTF"),
    ]

    for ruta in rutas_fuente:
        if ruta.exists():
            pdf.add_font("CodecStyle", fname=str(ruta))
            pdf.fuente_titulo = "CodecStyle"
            pdf.fuente_pie = "CodecStyle"
            return


def obtener_imagenes(carpeta: Path) -> list[Path]:
    if not carpeta.exists() or not carpeta.is_dir():
        print(f"Aviso: carpeta no encontrada, se omitirá: {carpeta}")
        return []

    return sorted(
        [
            archivo
            for archivo in carpeta.iterdir()
            if archivo.is_file() and archivo.suffix.lower() in EXTENSIONES_VALIDAS
        ]
    )


def obtener_paginas_ordenadas() -> list[Path]:
    paginas_blancas = obtener_imagenes(CARPETA_IMAGENES_FONDO_BLANCO)
    paginas_negras = obtener_imagenes(CARPETA_IMAGENES_FONDO_NEGRO)

    # Intercalar páginas blancas y negras alternadamente.
    # Esto asegura que en cada spread (doblez del folleto) todas las páginas
    # tengan el mismo color de fondo.
    paginas = []
    max_len = max(len(paginas_blancas), len(paginas_negras))
    
    for i in range(max_len):
        if i < len(paginas_blancas):
            paginas.append(paginas_blancas[i])
        if i < len(paginas_negras):
            paginas.append(paginas_negras[i])

    if SOLO_PRIMERA_IMAGEN:
        paginas = paginas[:1]

    if not paginas:
        raise ValueError(
            "No se encontraron imágenes válidas en las dos carpetas configuradas "
            f"({CARPETA_IMAGENES_FONDO_BLANCO} y {CARPETA_IMAGENES_FONDO_NEGRO})."
        )

    return paginas


def agregar_pagina_con_imagen(
    pdf: CatalogoPDF,
    imagen_path: Path,
    ancho_mm: float,
    numero_visible: int,
) -> None:
    pdf.add_page()
    pdf.registrar_numero_visible(numero_visible)

    # Título superior: nombre de archivo sin extensión, limpio y moderno
    pdf.set_y(9)
    if pdf.fuente_titulo == "Helvetica":
        pdf.set_font("Helvetica", size=TITULO_TAMANO)
    else:
        pdf.set_font(pdf.fuente_titulo, size=TITULO_TAMANO)
    pdf.set_text_color(12, 12, 12)
    if hasattr(pdf, "set_char_spacing"):
        pdf.set_char_spacing(TITULO_TRACKING)

    titulo = formatear_titulo_archivo(imagen_path)
    pdf.multi_cell(0, TITULO_ALTURA_LINEA_MM, titulo, align="C")

    if hasattr(pdf, "set_char_spacing"):
        pdf.set_char_spacing(0)

    # Centrado horizontal en A5
    x = (pdf.w - ancho_mm) / 2

    # Colocación vertical (debajo del título)
    y = max(30, pdf.get_y() + 5)

    # Se define solo ancho para mantener proporción original automáticamente
    pdf.image(str(imagen_path), x=x, y=y, w=ancho_mm)


def crear_catalogo_base_a5_temporal(
    imagenes: list[Path],
    ancho_imagen_mm: float,
) -> tuple[Path, int]:
    if ancho_imagen_mm <= 0:
        raise ValueError("El ancho de imagen debe ser mayor que 0.")

    if not imagenes:
        raise ValueError("No hay imágenes para crear el catálogo base temporal.")

    pdf = CatalogoPDF()
    configurar_fuentes_moderna(pdf)
    pdf.set_title("Catálogo de ropa")
    pdf.set_creator("Script Python con fpdf2")

    for numero_visible, imagen in enumerate(imagenes, start=1):
        agregar_pagina_con_imagen(
            pdf,
            imagen,
            ancho_imagen_mm,
            numero_visible,
        )

    archivo_temporal = NamedTemporaryFile(delete=False, suffix=".pdf")
    ruta_temporal = Path(archivo_temporal.name)
    archivo_temporal.close()

    pdf.output(str(ruta_temporal))
    return ruta_temporal, len(imagenes)


def mm_a_pt(valor_mm: float) -> float:
    return valor_mm * 72 / 25.4


def crear_overlay_marcas_corte_sra4(color_rgb: tuple[int, int, int]) -> Path:
    pdf_marcas = FPDF(orientation="P", unit="mm", format=(SRA4_ANCHO_MM, SRA4_ALTO_MM))
    pdf_marcas.set_auto_page_break(auto=False)
    pdf_marcas.add_page()

    x0 = (SRA4_ANCHO_MM - A4_ANCHO_MM) / 2
    y0 = (SRA4_ALTO_MM - A4_ALTO_MM) / 2
    x1 = x0 + A4_ANCHO_MM
    y1 = y0 + A4_ALTO_MM
    m = LONGITUD_MARCA_CORTE_MM

    r, g, b = color_rgb
    pdf_marcas.set_draw_color(r, g, b)
    pdf_marcas.set_line_width(0.25)

    # Esquina superior izquierda
    pdf_marcas.line(x0 - m, y0, x0 - 0.8, y0)
    pdf_marcas.line(x0, y0 - m, x0, y0 - 0.8)

    # Esquina superior derecha
    pdf_marcas.line(x1 + 0.8, y0, x1 + m, y0)
    pdf_marcas.line(x1, y0 - m, x1, y0 - 0.8)

    # Esquina inferior izquierda
    pdf_marcas.line(x0 - m, y1, x0 - 0.8, y1)
    pdf_marcas.line(x0, y1 + 0.8, x0, y1 + m)

    # Esquina inferior derecha
    pdf_marcas.line(x1 + 0.8, y1, x1 + m, y1)
    pdf_marcas.line(x1, y1 + 0.8, x1, y1 + m)

    archivo_temporal = NamedTemporaryFile(delete=False, suffix=".pdf")
    ruta_temporal = Path(archivo_temporal.name)
    archivo_temporal.close()

    pdf_marcas.output(str(ruta_temporal))
    return ruta_temporal


def generar_pdf_folleto_impuesto_sra4(
    pdf_entrada_a5: Path,
    pdf_salida_folleto_sra4: Path,
) -> tuple[int, int]:
    if not pdf_entrada_a5.exists():
        raise FileNotFoundError(f"No existe el PDF base A5 para imponer: {pdf_entrada_a5}")

    reader = PdfReader(str(pdf_entrada_a5))
    total_paginas_original = len(reader.pages)

    if total_paginas_original == 0:
        raise ValueError("El PDF base no contiene páginas para imponer.")

    total_paginas_impuestas = ((total_paginas_original + 3) // 4) * 4
    hojas = total_paginas_impuestas // 4

    primera_pagina = reader.pages[0]
    ancho_a5_pt = float(primera_pagina.mediabox.width)
    alto_a5_pt = float(primera_pagina.mediabox.height)

    ancho_sra4_pt = mm_a_pt(SRA4_ANCHO_MM)
    alto_sra4_pt = mm_a_pt(SRA4_ALTO_MM)
    ancho_a4_pt = mm_a_pt(A4_ANCHO_MM)
    alto_a4_pt = mm_a_pt(A4_ALTO_MM)

    offset_a4_x_pt = (ancho_sra4_pt - ancho_a4_pt) / 2
    offset_a4_y_pt = (alto_sra4_pt - alto_a4_pt) / 2

    ajuste_horizontal_spread_pt = max((ancho_a4_pt - (2 * ancho_a5_pt)) / 2, 0)
    x_izquierda_pt = offset_a4_x_pt + ajuste_horizontal_spread_pt
    x_derecha_pt = x_izquierda_pt + ancho_a5_pt
    y_colocacion_pt = offset_a4_y_pt + max((alto_a4_pt - alto_a5_pt) / 2, 0)

    color_marcas = (35, 35, 35)
    ruta_overlay_marcas = crear_overlay_marcas_corte_sra4(color_marcas)
    pagina_marcas = PdfReader(str(ruta_overlay_marcas)).pages[0]

    writer = PdfWriter()

    def obtener_pagina_o_blanco(indice: int):
        if indice >= total_paginas_original:
            return None
        return reader.pages[indice]

    for hoja in range(hojas):
        izquierda_frente = total_paginas_impuestas - 1 - (hoja * 2)
        derecha_frente = hoja * 2

        izquierda_dorso = hoja * 2 + 1
        derecha_dorso = total_paginas_impuestas - 2 - (hoja * 2)

        frente = writer.add_blank_page(width=ancho_sra4_pt, height=alto_sra4_pt)

        pagina_izquierda_frente = obtener_pagina_o_blanco(izquierda_frente)
        if pagina_izquierda_frente is not None:
            frente.merge_transformed_page(
                pagina_izquierda_frente,
                Transformation().translate(tx=x_izquierda_pt, ty=y_colocacion_pt),
            )

        pagina_derecha_frente = obtener_pagina_o_blanco(derecha_frente)
        if pagina_derecha_frente is not None:
            frente.merge_transformed_page(
                pagina_derecha_frente,
                Transformation().translate(tx=x_derecha_pt, ty=y_colocacion_pt),
            )

        frente.merge_page(pagina_marcas)

        dorso = writer.add_blank_page(width=ancho_sra4_pt, height=alto_sra4_pt)

        pagina_izquierda_dorso = obtener_pagina_o_blanco(izquierda_dorso)
        if pagina_izquierda_dorso is not None:
            dorso.merge_transformed_page(
                pagina_izquierda_dorso,
                Transformation().translate(tx=x_izquierda_pt, ty=y_colocacion_pt),
            )

        pagina_derecha_dorso = obtener_pagina_o_blanco(derecha_dorso)
        if pagina_derecha_dorso is not None:
            dorso.merge_transformed_page(
                pagina_derecha_dorso,
                Transformation().translate(tx=x_derecha_pt, ty=y_colocacion_pt),
            )

        dorso.merge_page(pagina_marcas)

    with pdf_salida_folleto_sra4.open("wb") as archivo_salida:
        writer.write(archivo_salida)

    if ruta_overlay_marcas.exists():
        ruta_overlay_marcas.unlink()

    return total_paginas_original, total_paginas_impuestas


def main() -> None:
    paginas_ordenadas = obtener_paginas_ordenadas()

    ruta_a5_temporal: Path | None = None
    total_paginas_original = 0
    total_paginas_impuestas = 0

    try:
        ruta_a5_temporal, _ = crear_catalogo_base_a5_temporal(
            paginas_ordenadas,
            ANCHO_IMAGEN_MM,
        )
        total_paginas_original, total_paginas_impuestas = generar_pdf_folleto_impuesto_sra4(
            ruta_a5_temporal,
            PDF_SALIDA_FOLLETO_SRA4,
        )
    finally:
        if (
            not CONSERVAR_PDF_TEMPORAL_A5
            and ruta_a5_temporal is not None
            and ruta_a5_temporal.exists()
        ):
            ruta_a5_temporal.unlink()

    total_pliegos = total_paginas_impuestas // 4
    total_paginas_final = total_pliegos * 2

    print(f"PDF folleto (SRA4) generado: {PDF_SALIDA_FOLLETO_SRA4.resolve()}")
    print(
        "Imposición aplicada "
        f"(páginas originales: {total_paginas_original} -> {total_paginas_impuestas}, "
        f"pliegos: {total_pliegos}, "
        f"páginas finales: {total_paginas_final})."
    )


if __name__ == "__main__":
    main()
