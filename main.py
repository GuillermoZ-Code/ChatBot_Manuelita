import requests
import json
import time
import random
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# Importamos nuestros módulos locales
import config
import procesamiento

def obtener_enlaces_internos(soup, url_actual, dominio_base):
    nuevos_enlaces = set()
    for etiqueta_a in soup.find_all("a", href=True):
        enlace_crudo = etiqueta_a["href"]
        enlace_completo = urljoin(url_actual, enlace_crudo).split('#')[0]
        enlace_limpio = enlace_completo.strip().lower()
        
        es_mismo_dominio = urlparse(enlace_completo).netloc == dominio_base
        
        # Bloqueamos archivos pesados y PDFs desde la raíz
        no_es_archivo_inutil = not any(ext in enlace_limpio.split('?')[0] for ext in ['.jpg', '.png', '.mp4', '.zip', '.xlsx', '.pdf'])
        no_es_correo = not enlace_crudo.startswith('mailto:')
        
        if es_mismo_dominio and no_es_archivo_inutil and no_es_correo:
            nuevos_enlaces.add(enlace_completo)
            
    return nuevos_enlaces

def iniciar_crawler():
    dominio_base = urlparse(config.URL_INICIO).netloc
    urls_por_visitar = [config.URL_INICIO] + config.URLS_EXTERNAS
    urls_visitadas = set()
    id_global = 0

    print(f"=== Iniciando Extracción Inteligente Estricta en: {dominio_base} ===")
    print(f"-> Regla activa: Solo páginas con contenido real (Se ignoran PDFs y webs vacías)")

    with open(config.ARCHIVO_JSONL, "w", encoding="utf-8") as f_json:
        
        while urls_por_visitar and len(urls_visitadas) < config.LIMITE_PAGINAS:
            url_actual = urls_por_visitar.pop(0)
            
            if url_actual in urls_visitadas:
                continue
            
            # Defensa contra PDFs que se colaron
            if url_actual.lower().endswith('.pdf'):
                print(f"[{len(urls_visitadas)+1}/{config.LIMITE_PAGINAS}] Saltando PDF: {url_actual}")
                urls_visitadas.add(url_actual)
                continue
                
            print(f"[{len(urls_visitadas)+1}/{config.LIMITE_PAGINAS}] Scrapeando: {url_actual}")
            
            try:
                headers = {'User-Agent': random.choice(config.LISTA_USER_AGENTS)}
                
                res = requests.get(url_actual, headers=headers, timeout=15)
                res.raise_for_status()
                soup = BeautifulSoup(res.text, 'html.parser')
                
                fragmentos, texto_completo, titulo = procesamiento.limpiar_y_segmentar(soup, url_actual)
                
                if urlparse(url_actual).netloc == dominio_base:
                    nuevos_enlaces = obtener_enlaces_internos(soup, url_actual, dominio_base)
                else:
                    nuevos_enlaces = set() 
                
                categoria_semantica = config.categorizar_url(url_actual)
                
                # GUARDADO EN JSONL (Solo lo que superó los filtros)
                for chunk in fragmentos:
                    data = {
                        "id": id_global, 
                        "url": url_actual, 
                        "categoria": categoria_semantica,
                        "titulo": titulo,
                        "contenido": chunk
                    }
                    f_json.write(json.dumps(data, ensure_ascii=False) + "\n")
                    id_global += 1
                
                # GUARDADO EN MARKDOWN
                if texto_completo.strip():
                    ruta_md = os.path.join(config.CARPETA_MD, f"{categoria_semantica}.md")
                    
                    with open(ruta_md, "a", encoding="utf-8") as f_md:
                        if os.path.getsize(ruta_md) == 0:
                            f_md.write(f"# Base de Conocimiento: {categoria_semantica.replace('_', ' ')}\n\n---\n\n")
                            
                        f_md.write(f"## {titulo}\n")
                        f_md.write(f"**Fuente original:** [{url_actual}]({url_actual})\n\n")
                        f_md.write(f"{texto_completo}\n\n")
                        f_md.write("---\n\n")
                else:
                    print("  -> Página descartada: No contiene párrafos informativos útiles.")
                
                # GESTIÓN DE ENLACES Y PAUSA (Polite Scraping)
                for enlace in nuevos_enlaces:
                    if enlace not in urls_visitadas and enlace not in urls_por_visitar:
                        urls_por_visitar.append(enlace)
                        
                urls_visitadas.add(url_actual)
                time.sleep(random.uniform(2.0, 4.5))
                
            except requests.exceptions.HTTPError as err:
                if err.response.status_code == 429:
                    print("  -> [!] Servidor saturado (HTTP 429). Retrocediendo...")
                    urls_por_visitar.insert(0, url_actual)
                    time.sleep(15)
                    continue
                else:
                    urls_visitadas.add(url_actual)
            except Exception as e:
                print(f"  -> Error: {e}")
                urls_visitadas.add(url_actual)

    print(f"\n=== Misión Cumplida ===")
    print(f"Páginas analizadas: {len(urls_visitadas)}")
    print(f"Fragmentos puros generados: {id_global}")

if __name__ == "__main__":
    iniciar_crawler()