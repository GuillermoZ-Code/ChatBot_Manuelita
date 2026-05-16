import os
import time # NUEVO: Importamos time para hacer pausas
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

import config
import procesamiento 

def obtener_enlaces_internos(soup, url_actual, dominio_base):
    nuevos_enlaces = set()
    for etiqueta_a in soup.find_all("a", href=True):
        enlace_crudo = etiqueta_a["href"]
        enlace_completo = urljoin(url_actual, enlace_crudo).split('#')[0]
        enlace_limpio = enlace_completo.strip().lower()
        
        es_mismo_dominio = urlparse(enlace_completo).netloc == dominio_base
        no_es_archivo = not any(ext in enlace_limpio.split('?')[0] for ext in ['.jpg', '.png', '.mp4', '.zip', '.xlsx', '.pdf'])
        no_es_correo = not enlace_crudo.startswith('mailto:')
        
        if es_mismo_dominio and no_es_archivo and no_es_correo:
            nuevos_enlaces.add(enlace_completo)
            
    return nuevos_enlaces

def ejecutar_ingesta():
    print("🕵️ Iniciando Crawler de Ingesta y Vectorización Local (MODO SIN LÍMITE)...")
    documentos_finales = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    dominio_base = urlparse(config.URL_INICIO).netloc
    urls_por_visitar = [config.URL_INICIO] + config.URLS_EXTERNAS
    urls_visitadas = set()

    print("\n🌐 Fase 1: Navegando toda la web (Esto puede tardar varios minutos)...")
    
    # ELIMINAMOS LA RESTRICCIÓN DEL LÍMITE AQUÍ
    while urls_por_visitar:
        url_actual = urls_por_visitar.pop(0)
        
        if url_actual in urls_visitadas:
            continue
            
        try:
            res = requests.get(url_actual, headers=headers, timeout=15)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, 'html.parser')
            
            fragmentos, texto_md, titulo = procesamiento.limpiar_y_segmentar(soup, url_actual)
            
            if fragmentos:
                documentos_finales.extend(fragmentos)
                print(f"  ✅ Procesado [Pág. {len(urls_visitadas)+1}]: {titulo}")
            else:
                print(f"  ⏭️ Saltado [Pág. {len(urls_visitadas)+1}]: Sin contenido útil en {url_actual}")

            if urlparse(url_actual).netloc == dominio_base:
                nuevos_enlaces = obtener_enlaces_internos(soup, url_actual, dominio_base)
                for enlace in nuevos_enlaces:
                    if enlace not in urls_visitadas and enlace not in urls_por_visitar:
                        urls_por_visitar.append(enlace)
                        
            urls_visitadas.add(url_actual)
            
            # NUEVO: Pausa de 1 segundo para no saturar el servidor de Manuelita
            time.sleep(1)
            
        except Exception as e:
            print(f"  ❌ Error en {url_actual}: {e}")
            urls_visitadas.add(url_actual)

    if documentos_finales:
        print(f"\n🧠 Fase 2: Vectorizando {len(documentos_finales)} fragmentos encontrados...")
        
        model_name = "intfloat/multilingual-e5-large"
        model_kwargs = {'device': 'cpu'} 
        encode_kwargs = {'normalize_embeddings': True}
        
        print(f"📥 Cargando modelo de embeddings local '{model_name}'...")
        
        embeddings_locales = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs
        )

        carpeta_bd = "./chroma_db_manuelita_local"
        
        print("💾 Creando red neuronal y guardando vectores en ChromaDB...")
        vectorstore = Chroma.from_documents(
            documents=documentos_finales,
            embedding=embeddings_locales,
            persist_directory=carpeta_bd
        )
        print(f"\n🚀 ¡Éxito Total! Base de datos local construida con {len(urls_visitadas)} páginas visitadas.")
    else:
        print("\n⚠️ No se encontró contenido útil para indexar.")

if __name__ == "__main__":
    ejecutar_ingesta()