import re
from bs4 import BeautifulSoup
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

def tiene_contenido_real(texto):
    texto_sin_url = re.sub(r'http[s]?://\S+', '', texto)
    letras_reales = re.sub(r'[^a-záéíóúñA-ZÁÉÍÓÚÑ]', '', texto_sin_url)
    return len(letras_reales) > 15

def limpiar_y_segmentar(soup, url_origen):
    titulo_pagina = soup.title.string.strip() if soup.title else "Página Corporativa"
    titulo_limpio = titulo_pagina.replace(" - Manuelita", "").replace(" | Manuelita", "")

    # Limpiamos ruido
    for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'button', 'form']):
        tag.decompose()

    contenido_util = []
    tiene_parrafos_reales = False 
    
    for etiqueta in soup.find_all(['h1', 'h2', 'h3', 'p', 'li']):
        texto = etiqueta.get_text(separator=" ", strip=True)
        if tiene_contenido_real(texto):
            contenido_util.append(texto)
            if etiqueta.name in ['p', 'li']:
                tiene_parrafos_reales = True

    if not tiene_parrafos_reales:
        return [], "", ""

    texto_completo = '\n\n'.join(contenido_util)

    # Segmentamos para el RAG
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    fragmentos_crudos = text_splitter.split_text(texto_completo)
    
    fragmentos_documentos = []
    for chunk in fragmentos_crudos:
        if tiene_contenido_real(chunk):
            # Convertimos el texto en un "Documento" oficial de LangChain
            doc = Document(
                page_content=chunk,
                metadata={"source": url_origen, "titulo": titulo_limpio}
            )
            fragmentos_documentos.append(doc)
            
    return fragmentos_documentos, texto_completo, titulo_limpio