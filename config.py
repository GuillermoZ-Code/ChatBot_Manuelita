import os

# --- URLS PRINCIPALES Y EXTERNAS ---
URL_INICIO = "https://www.manuelita.com/"
URLS_EXTERNAS = [
    "https://www.valoraanalitik.com/2023/10/24/harold-eder-manuelita-habla-de-inversiones-y-proyectos/",
    "https://www.linkedin.com/company/manuelita/about/"
]

# --- LÍMITES Y SALIDAS ---
LIMITE_PAGINAS = 250
ARCHIVO_JSONL = "knowledge_base_manuelita.jsonl"
CARPETA_MD = "context"

# Crear la carpeta de Markdown automáticamente si no existe
os.makedirs(CARPETA_MD, exist_ok=True)

# --- DISFRACES DE NAVEGADOR (USER-AGENTS) ---
LISTA_USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/113.0'
]

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
    elif "noticias" in url_baja or "valoraanalitik" in url_baja:
        return "Actualidad_y_Liderazgo"
    elif "trabaja-con-nosotros" in url_baja or "empleo" in url_baja or "talento" in url_baja:
        return "Empleabilidad_y_Talento"
    
    return "General"