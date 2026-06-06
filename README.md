# Agente Conversacional Manuelita S.A.

Este proyecto implementa un asistente conversacional corporativo para Manuelita S.A. orientado a responder consultas institucionales a través de WhatsApp y una interfaz de apoyo en Streamlit. La solución combina memoria conversacional persistente, recuperación documental con RAG, datos estructurados para respuestas deterministas y una arquitectura modular basada en FastAPI, LangChain/LangGraph, ChromaDB y SQLite.

## Propósito

El objetivo del sistema es ofrecer respuestas claras, útiles y controladas sobre información institucional de Manuelita S.A., reduciendo errores y alucinaciones mediante el uso combinado de varias capas de conocimiento. El agente no depende únicamente de un modelo generativo: también consulta memoria, conocimiento documental y fuentes estructuradas antes de responder.

## Alcance del sistema

El agente se diseñó como una solución funcional para operación local y académica, con capacidad de integrarse al canal de WhatsApp mediante un servidor puente y una API interna del agente. Además, la arquitectura deja abierta la posibilidad de evolucionar hacia escenarios más robustos, por ejemplo migrando a PostgreSQL, fortaleciendo autenticación o incorporando monitoreo más avanzado.

## Arquitectura general

La solución se organiza en cinco capas principales:

1. **Canal de entrada y puente de mensajería**: `server.py` conecta WhatsApp con el agente y expone endpoints REST para estado, chat, envío y reinicio de sesión.
2. **API interna del agente**: `agent_api.py` recibe la consulta, resuelve la sesión por número telefónico, carga configuración y delega la respuesta al servicio del agente.
3. **Orquestación inteligente**: `agent_service.py` analiza la consulta y decide si responder por memoria, dato estructurado o recuperación RAG.
4. **Persistencia**: `db.py` y `chat_memory.py` almacenan conversaciones, configuraciones y perfil de usuario en SQLite.
5. **Recuperación y conocimiento**: `rag_client.py`, `structured_tool.py`, `tools.py` y `structured_data.json` permiten responder con base en documentos y datos institucionales controlados.

## Flujo de una consulta

El flujo operativo puede resumirse así:

1. El usuario envía un mensaje por WhatsApp.
2. `server.py` recibe el mensaje y lo traduce a una solicitud HTTP interna hacia `agent_api.py`.
3. `agent_api.py` identifica al usuario por número telefónico, asigna o recupera su `chat_id` persistente y crea la sesión conversacional correspondiente.
4. `agent_service.py` analiza la pregunta y decide si debe resolverse por memoria, por datos estructurados o por RAG.
5. El modelo LLM genera la respuesta usando el contexto disponible.
6. La interacción queda registrada en SQLite para continuidad, trazabilidad y reutilización posterior.
7. `server.py` devuelve la respuesta al usuario por el canal de WhatsApp.

## Estrategia de respuesta

El sistema no responde todas las preguntas del mismo modo. En su lugar, aplica una lógica híbrida:

- **Memoria conversacional**: útil para recordar información compartida por el usuario, como su nombre o contexto reciente.
- **Datos estructurados**: se usan para responder consultas fijas, por ejemplo contacto, sedes, horarios o información operativa controlada.
- **RAG institucional**: se activa cuando la consulta requiere contenido documental más amplio, como historia, trayectoria, contexto corporativo o temas institucionales no triviales.

Esta separación mejora la confiabilidad del sistema y evita que preguntas simples dependan innecesariamente del modelo generativo.

## Componentes principales

### `server.py`
Puente entre WhatsApp y el agente. Gestiona la conexión del canal, recibe mensajes entrantes, envía respuestas y expone endpoints REST como `/status`, `/chat`, `/send` y `/reset`.

### `agent_api.py`
Puerta HTTP del agente. Recibe solicitudes desde el puente, resuelve la sesión por número telefónico, selecciona el modelo activo y ejecuta el flujo de respuesta del agente.

### `agent.py`
Cliente HTTP interno que conecta `server.py` con `agent_api.py` y encapsula la invocación al agente remoto/local.

### `agent_service.py`
Capa principal de decisión. Evalúa la consulta y selecciona la mejor ruta de respuesta entre memoria, dato estructurado o RAG.

### `chat_memory.py`
Servicio de memoria conversacional. Guarda y recupera historial, extrae datos básicos del usuario y mantiene continuidad por sesión o número telefónico.

### `db.py`
Capa de persistencia basada en SQLite. Administra chats, mensajes, configuraciones y asociaciones entre número telefónico y sesión.

### `rag_client.py`
Cliente de acceso al vector store. Consulta ChromaDB para recuperar fragmentos relevantes del corpus documental institucional.

### `structured_tool.py`
Resuelve consultas deterministas desde la base estructurada. Es especialmente útil para datos operativos o institucionales fijos.

### `tools.py`
Centraliza las herramientas disponibles para el agente, incluyendo recuperación RAG y acceso a datos estructurados.

### `llm_factory.py`
Construye instancias de modelos locales y API según la configuración disponible. Soporta proveedores como Ollama, Gemini y GPT-4o mini.

### `settings.py`
Archivo de configuración central. Define rutas, parámetros por defecto, límites, modelo por defecto y prompt base del sistema.

### `app.py`
Aplicación base en Streamlit. Proporciona chat, historial, configuración técnica y una interfaz administrativa inicial del asistente.

### `ui_components.py`
Contiene estilos y fragmentos de interfaz reutilizables para mantener una apariencia visual consistente.

### `ingesta.py`
Script de preparación del RAG. Procesa el corpus documental, aplica particionado y genera la base vectorial persistente en ChromaDB.

### `context/`
Carpeta con los documentos fuente usados para construir el corpus institucional del agente.

### `structured_data.json`
Base estructurada con información fija de negocio y contacto para respuestas controladas.

### `chroma_db_manuelita_local/`
Directorio donde se persiste la base vectorial generada a partir del corpus institucional.

## Stack tecnológico

| Componente | Uso principal |
|---|---|
| FastAPI | API del agente y puente REST |
| Streamlit | Interfaz local de operación y prueba |
| LangChain / LangGraph | Orquestación del agente y uso de herramientas |
| ChromaDB | Recuperación semántica del conocimiento institucional |
| HuggingFace Embeddings | Embeddings multilingües para el RAG |
| SQLite | Persistencia conversacional y configuración |
| WhatsApp vía código | Canal conversacional de entrada y salida |
| Ollama / Gemini / GPT-4o mini | Modelos LLM locales y por API |

## Funcionalidades implementadas

- Integración con WhatsApp mediante una arquitectura code-centric.
- API interna del agente sobre FastAPI.
- Persistencia de conversaciones y configuración en SQLite.
- Soporte para memoria conversacional por usuario o número telefónico.
- Respuestas deterministas desde datos estructurados.
- Respuestas documentales usando RAG sobre ChromaDB.
- Selección de modelos locales y por API.
- Interfaz base en Streamlit para chat y configuración.
- Trazabilidad opcional con LangSmith cuando se dispone de credenciales.

## Decisiones de diseño relevantes

### Arquitectura híbrida
Se eligió una solución híbrida porque un agente empresarial no debe depender solo de generación libre. La combinación de memoria, datos estructurados y RAG permite mayor control, mejor trazabilidad y respuestas más confiables.

### Persistencia con SQLite
La implementación actual usa SQLite como mecanismo principal de persistencia por simplicidad operativa y viabilidad en entorno local. Esta decisión deja una base funcional que puede migrarse más adelante a PostgreSQL en entornos más exigentes.

### Integración WhatsApp sin N8N
Se optó por una integración code-centric en lugar de una capa intermedia con N8N. Esto da más control técnico sobre el flujo, simplifica la trazabilidad y reduce dependencias externas.

### Separación entre memoria y razonamiento
La memoria persistente del usuario se mantiene separada del estado interno del razonamiento del agente. Esta decisión evita contaminación de contexto entre turnos y mejora la estabilidad de las respuestas.

## Requisitos previos

Antes de ejecutar el proyecto, verifica lo siguiente:

- Tener Python instalado.
- Contar con un entorno virtual configurado.
- Instalar las dependencias del proyecto.
- Configurar correctamente el archivo `.env`.
- Disponer del corpus documental para construir o reutilizar la base vectorial.
- Tener un archivo `structured_data.json` válido.
- Si usarás modelos API, contar con las claves correspondientes.
- Si usarás modelos locales, tener Ollama instalado y con modelos disponibles.

## Configuración del entorno

1. Copia `.env.example` a `.env`.
2. Define las credenciales necesarias para el proveedor LLM que vayas a usar.
3. Si deseas trazabilidad, configura LangSmith en el entorno.
4. Verifica que la carpeta `context/` exista y contenga los documentos institucionales fuente.
5. Si cambias el corpus, reconstruye la base vectorial antes de iniciar el sistema.

Ejemplo de variables de entorno:

```env
LANGSMITH_API_KEY=tu_api_key
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=agente_manuelita
GEMINI_API_KEY=tu_api_key_gemini
OPENAI_API_KEY=tu_api_key_openai
```

## Ejecución del proyecto

### Interfaz Streamlit

Para ejecutar la interfaz base:

```bash
streamlit run app.py
```

### API del agente

Para iniciar la API del agente:

```bash
uv run python agent_api.py
```

### Servidor puente de WhatsApp

Para iniciar el servidor puente:

```bash
uv run python server.py
```

### Reconstrucción del RAG

Si modificas los documentos de `context/`, reconstruye la base vectorial antes de volver a usar el sistema:

```bash
uv run python ingesta.py
```

## Endpoints principales

| Endpoint | Servicio | Propósito |
|---|---|---|
| `/chat` | `agent_api.py` | Procesar consultas del agente por número o sesión |
| `/status` | `agent_api.py` | Verificar estado del agente y modelos disponibles |
| `/status` | `server.py` | Confirmar si WhatsApp está conectado |
| `/send` | `server.py` | Enviar mensajes manualmente por el puente |
| `/reset` | `server.py` | Reiniciar sesión o contexto operativo |

## Limitaciones actuales

- La persistencia productiva robusta con PostgreSQL no está implementada todavía; la solución actual usa SQLite.
- El análisis avanzado de conversaciones, por ejemplo con t-SNE, aparece como posibilidad futura y no como componente actual.
- El sistema puede fortalecerse con autenticación, rate limiting y monitoreo más robusto.

## Trabajo futuro recomendado

- Migrar de SQLite a PostgreSQL para escenarios multiusuario o distribuidos.
- Añadir autenticación y control de acceso a la API del agente.
- Incorporar monitoreo y trazabilidad más completa en producción.
- Fortalecer seguridad, validaciones de entrada y rate limiting.
- Desarrollar analítica posterior sobre conversaciones y uso del sistema.

## Valor del proyecto

El valor principal de este agente no está solo en responder mensajes, sino en haber sido construido con una lógica técnica defendible, modular y extensible. La solución integra fuentes controladas, separa responsabilidades, documenta sus límites y deja una base realista para evolucionar hacia un asistente corporativo más robusto.