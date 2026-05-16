# config.py
import os

# --- URLS PRINCIPALES Y EXTERNAS ---
URL_INICIO = "https://www.manuelita.com/"
URLS_EXTERNAS = [
]

# --- LÍMITES Y SALIDAS ---
LIMITE_PAGINAS = 1000000
ARCHIVO_ESTRUCTURADO = "datos_empresa.json"

# --- LÓGICA DE CATEGORIZACIÓN ---
def categorizar_url(url):
    """Asigna una categoría semántica basada en palabras clave de la URL."""
    url_baja = url.lower()
    
    if "sostenibilidad" in url_baja or "esg" in url_baja:
        return "Sostenibilidad"
    elif "historia" in url_baja or "quienes-somos" in url_baja or "nuestra-historia" in url_baja:
        return "Historia_y_Cultura"
    elif "plataformas" in url_baja or "productos" in url_baja or "agroindustriales" in url_baja:
        return "Unidades_de_Negocio"
    elif "trabaja-con-nosotros" in url_baja or "empleo" in url_baja or "talento" in url_baja:
        return "Empleabilidad_y_Talento"
    
    return "General"