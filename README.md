# Catálogo de ropa en PDF (folleto SRA4)

Script en Python para generar un único PDF final en modo folleto con imposición automática sobre hoja SRA4.

## Requisitos

- Python 3.10+
- Dependencias: `fpdf2`, `pypdf`

## Instalación

```powershell
pip install -r requirements.txt
```

## Configuración

Abre `crear_catalogo_pdf.py` y edita estas variables:

- `CARPETA_IMAGENES_FONDO_BLANCO`: imágenes que deben ir con fondo blanco
- `CARPETA_IMAGENES_FONDO_NEGRO`: imágenes que deben ir con fondo antracita
- `PDF_SALIDA_FOLLETO_SRA4`: único PDF final impuesto
- `ANCHO_IMAGEN_MM`: ancho fijo de la imagen en milímetros (por defecto `120`)

## Ejecución

```powershell
python crear_catalogo_pdf.py
```

## Qué hace

- Lee todas las imágenes válidas de la carpeta indicada
- Crea páginas base A5 (temporales) con una imagen por página
- Elimina la extensión del nombre de archivo y lo usa como título superior
- Aplica fondo blanco o antracita según la carpeta de origen de cada imagen
- En fondo antracita, título, línea divisoria y número de página pasan a blanco
- Impone automáticamente en orden de folleto (1 con última, 2 con penúltima, etc.)
- Mantiene coherencia por pliego: frente y dorso del mismo pliego son del mismo tema (blanco con blanco, negro con negro)
- Combina los pliegos finales intercalando temas para evitar bloques completos de un solo color
- Genera un único PDF final en SRA4 (`320 x 225 mm`) con marcas de corte para A4
- Si faltan páginas para cuadrar a múltiplos de 4, añade páginas en blanco automáticamente
