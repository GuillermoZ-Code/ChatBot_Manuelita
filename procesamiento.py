import re
from bs4 import BeautifulSoup
from langchain_text_splitters import RecursiveCharacterTextSplitter

def tiene_contenido_real(texto):
    """Comprueba si el texto tiene información útil (más de 15 letras puras)."""
    texto_sin_url = re.sub(r'http[s]?://\S+', '', texto)
    letras_reales = re.sub(r'[^a-záéíóúñA-ZÁÉÍÓÚÑ]', '', texto_sin_url)
    return len(letras_reales) > 15

def limpiar_y_segmentar(soup, url_origen):
    """Extrae títulos y párrafos. Si no hay párrafos reales, descarta la página."""
    
    titulo_pagina = soup.title.string.strip() if soup.title else "Página Corporativa"
    titulo_limpio = titulo_pagina.replace(" - Manuelita", "").replace(" | Manuelita", "")

    # DESTRUCCIÓN DE RUIDO Y MENÚS INVISIBLES
    for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'button', 'form', 'iframe', 'noscript']):
        tag.decompose()
        
    for class_name in ['menu', 'header', 'footer', 'sidebar', 'widget', 'popup', 'cookie', 'nav', 'banner']:
        for tag in soup.find_all(class_=re.compile(class_name, re.I)):
            tag.decompose()

    # EXTRACCIÓN Y VALIDACIÓN DE PÁRRAFOS
    contenido_util = []
    tiene_parrafos_reales = False 
    
    for etiqueta in soup.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'li']):
        texto = etiqueta.get_text(separator=" ", strip=True)
        
        # Filtro estricto: ¿Tiene letras de verdad?
        if tiene_contenido_real(texto):
            if etiqueta.name.startswith('h'):
                nivel = int(etiqueta.name[1])
                contenido_util.append(f"{'#' * nivel} {texto}")
                
            elif etiqueta.name in ['p', 'li']:
                if etiqueta.name == 'li':
                    contenido_util.append(f"- {texto}")
                else:
                    contenido_util.append(texto)
                
                # Confirmamos que encontramos "carne" (párrafos de lectura)
                tiene_parrafos_reales = True

    # Si la página solo tenía títulos pero ningún párrafo, la descartamos
    if not tiene_parrafos_reales:
        return [], "", ""

    texto_markdown = '\n\n'.join(contenido_util)

    # DEDUPLICACIÓN AVANZADA (Fuzzy Matching para noticias repetidas)
    parrafos = texto_markdown.split('\n\n')
    parrafos_unicos = []
    textos_vistos = set()
    
    for p in parrafos:
        p_comp = re.sub(r'http\S+', '', p)
        p_comp = re.sub(r'[^a-záéíóúñ0-9]', '', p_comp.lower())
        
        if len(p_comp) < 30:
            parrafos_unicos.append(p)
        elif p_comp not in textos_vistos:
            textos_vistos.add(p_comp)
            parrafos_unicos.append(p)
            
    texto_markdown_limpio = '\n\n'.join(parrafos_unicos)

    # SEGMENTACIÓN PARA LA IA
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, length_function=len)
    fragmentos_crudos = text_splitter.split_text(texto_markdown_limpio)
    
    fragmentos_enriquecidos = []
    for chunk in fragmentos_crudos:
        # Última validación: ¿El pedazo cortado sigue teniendo sentido?
        if tiene_contenido_real(chunk):
            contexto = f"DOCUMENTO: {titulo_limpio}\nFUENTE: {url_origen}\nCONTENIDO:\n{chunk}"
            fragmentos_enriquecidos.append(contexto)
            
    return fragmentos_enriquecidos, texto_markdown_limpio, titulo_limpio