# Puente de WhatsApp para tu agente (Python)

Conecta WhatsApp con TU agente (un endpoint HTTP/REST). El puente recibe los
mensajes de WhatsApp, le manda a tu agente el texto **y el número de quien escribe**
(para que mantenga el historial por persona), y devuelve la respuesta por WhatsApp.

```
WhatsApp -> puente (FastAPI, :3000) -> TU agente (HTTP/REST) -> respuesta -> WhatsApp
```

Usa neonize (motor whatsmeow) para WhatsApp: corre local, con QR, sin navegador.

-------------------------------------------------------------------------------
## 1. Archivos del proyecto

```
whatsapp-agent-python/
├── README.md            (este archivo)
├── requirements.txt     (dependencias)
├── .env.example         (configuración; se copia a .env)
└── src/
    ├── agent.py         (se conecta a TU agente; aquí va el número)
    ├── whatsapp.py      (conexión a WhatsApp + QR)
    └── server.py        (API REST + arranque)
```

-------------------------------------------------------------------------------
## 2. Requisitos (una sola vez)

- Python 3.10 o superior. Verifícalo en una terminal:
  ```powershell
  python --version
  ```
  (si "python" no responde, prueba `py --version`)
- Tu agente corriendo y accesible por HTTP.

-------------------------------------------------------------------------------
## 3. Instalación paso a paso (Windows / PowerShell)

Importante: el puente se instala en su PROPIO entorno virtual (.venv), aislado
de tu agente. Esto evita choques de versiones (por ejemplo, protobuf) entre los
dos proyectos.

1) Abre una terminal dentro de la carpeta del proyecto:
   ```powershell
   cd ruta\a\whatsapp-agent-python
   ```

2) Crea el entorno virtual:
   ```powershell
   python -m venv .venv
   ```

3) Instala las dependencias DENTRO del entorno (usando su python por ruta
   completa, así no depende de "activar" nada):
   ```powershell
   .\.venv\Scripts\python.exe -m pip install --upgrade pip
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```
   Debe terminar con "Successfully installed neonize-... protobuf-7.x fastapi-...".

4) (Opcional) Verifica que quedó el protobuf correcto (7.x):
   ```powershell
   .\.venv\Scripts\python.exe -c "import google.protobuf; print(google.protobuf.__version__)"
   ```

5) Copia la configuración y edítala:
   ```powershell
   copy .env.example .env
   ```
   Abre el archivo .env y pon la URL de tu agente en AGENT_URL.

-------------------------------------------------------------------------------
## 4. Conectar con tu agente

En .env:
```
AGENT_URL=http://localhost:8000/chat   <- la URL de tu agente
```

El puente le envía a tu agente:
```json
POST {AGENT_URL}
{ "message": "<texto>", "numero": "573103716572", "sessionId": "573103716572" }
```
- "numero" / "sessionId": el teléfono de quien escribe (código de país, sin + ni @).
  Tu agente debe usarlo como llave para guardar/recuperar el historial por persona.
- Si tu agente usa otros nombres de campo (en el envío o en la respuesta),
  cámbialos en los dos puntos marcados con  AJUSTA  dentro de src/agent.py.

Del lado de tu agente, la idea es:
```python
numero = data["numero"]                  # o data["sessionId"]
historial = memoria.get(numero, [])      # lo anterior de esa persona
historial.append({"role": "user", "content": data["message"]})
# ...generas la respuesta usando 'historial'...
historial.append({"role": "assistant", "content": respuesta})
memoria[numero] = historial              # lo guardas para la próxima
```

-------------------------------------------------------------------------------
## 5. Arrancar el puente

Ejecuta SIEMPRE con el python del entorno (ruta completa):
```powershell
.\.venv\Scripts\python.exe server.py
```
- Si los archivos están sueltos (no dentro de src), usa `python ...` apuntando al
  server.py donde lo tengas. Lo importante es que agent.py, whatsapp.py y server.py
  estén juntos en la misma carpeta.

La primera vez aparece un QR en la terminal. En tu teléfono:
WhatsApp -> Dispositivos vinculados -> Vincular un dispositivo -> escanéalo.
Cuando veas "WhatsApp conectado y listo", ya está funcionando.

Mantén corriendo a la vez: tu agente y este puente.

-------------------------------------------------------------------------------
## 6. Probar

Sin WhatsApp (en otra terminal):
```powershell
.\.venv\Scripts\python.exe -c "import requests; print(requests.post('http://localhost:3000/chat', json={'message':'hola'}).text)"
```
O directamente: escríbele un WhatsApp al número vinculado desde otro teléfono.

-------------------------------------------------------------------------------
## 7. API REST del puente

| Método | Ruta      | Cuerpo (JSON)                              | Descripción                       |
|--------|-----------|--------------------------------------------|-----------------------------------|
| GET    | /status   | -                                          | Estado de la conexión a WhatsApp  |
| POST   | /send     | { "to": "573001112233", "message": "..." } | Enviar un mensaje manualmente     |
| POST   | /chat     | { "chatId": "test", "message": "..." }     | Probar el agente sin WhatsApp     |
| POST   | /reset    | { "chatId": "..." }                        | Reiniciar (si lo implementas)     |

Documentación interactiva: http://localhost:3000/docs

-------------------------------------------------------------------------------
## 8. Notas y problemas comunes

- "pip no se reconoce": usa `.\.venv\Scripts\python.exe -m pip ...` en vez de `pip`.
- Error de protobuf (gencode/runtime): pasa cuando se instala en el Python global
  junto a otro proyecto. Solución: usar el .venv como en el paso 3 (queda aislado).
- Activación de PowerShell bloqueada: no hace falta activar si usas la ruta completa
  `.\.venv\Scripts\python.exe`. (Si igual quieres activar:
  `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` y luego
  `.\.venv\Scripts\Activate.ps1`.)
- Cada vez que abras una terminal nueva para el puente, vuelve a usar la ruta
  completa del python del .venv.
- neonize/whatsmeow es no oficial: hay riesgo de bloqueo del número si hay mucho
  volumen o spam. Ideal para uso interno/controlado.
