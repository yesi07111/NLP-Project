# 🤖 Proyecto NLP — Cliente Telegram para exportar chats

## 🧠 Resumen
Este proyecto es una herramienta de **Procesamiento del Lenguaje Natural (NLP)** que funciona como cliente de Telegram. Permite iniciar sesión con una cuenta, seleccionar chats/grupos y descargar los mensajes en un formato **estructurado (JSON)** para análisis posterior. Es posible filtrar por rango de fechas y elegir si descargar contenidos multimedia (imágenes, audios, documentos).

---

## 🎯 Funcionalidades principales
- 🔐 Iniciar sesión y gestionar la sesión (incluye soporte para 2FA / contraseña de verificación).  
- 📥 Descargar mensajes por chat o grupos seleccionados.  
- 📅 Filtrar por rango de fezas.  
- ✅ Seleccionar tipos de medios a descargar: imágenes, audio, documentos.  
- 🗂️ Guardar los mensajes y metadatos en un archivo `JSON` por chat, y los archivos multimedia en carpetas `media_<nombre_del_chat>`.

---

## 📦 Formato del JSON generado
El JSON contiene dos secciones principales: `metadata` y `messages`.

- `metadata`:
  - `chat_name`: nombre del chat o canal.
  - `start_date`, `end_date`: rango de fechas solicitado.
  - `total_messages`: número total de mensajes incluidos.
  - `generated_at`: marca de tiempo de generación del JSON.

- `messages`: lista de mensajes, cada uno con campos como:
  - `id`: identificador del mensaje.
  - `sender_id`, `sender_name`, `sender_username`
  - `text`: texto limpio del mensaje (ver **Preprocesamiento**).
  - `reactions`: objeto con conteo por emoji (ej. `{ "👍": 3 }`).
  - `mentions`: lista de menciones (si aplica).
  - `reply_id`: id del mensaje al que responde (si existe).
  - `date`: marca de tiempo en formato ISO.
  - `media`: **información sobre el multimedia** (ver abajo).

### 🔎 Estructura del campo `media`
Al decidir descargar los medios, cada mensaje puede contener un objeto `media` con esta forma (si no hay medios, puede ser `null`):

```json
"media": {
  "type": "photo" | "audio" | "document" | null,
  "filename": "photo_12345.jpg" | "audio_67890.ogg" | "54321_document.pdf" | null,
  "path": "media_Grupo Estudio\\photo_12345.jpg",
  "downloaded": true | false
}
```

* Los archivos descargados se guardan en una carpeta por chat: `media_<nombre_del_chat_sanitizado>` (ej.: `media_Grupo Estudio`).
* `path` es la ruta relativa al archivo dentro del proyecto (utiliza separadores de sistema según la plataforma).
* Si `downloaded: false` o `media` es `null`, no hay archivo local disponible para ese mensaje.

#### Ejemplo breve (fragmento del JSON):

```json
{
  "id": 67890,
  "sender_id": 987654321,
  "sender_name": "Ana García",
  "sender_username": "anagarcia_dev",
  "text": "¿Quedamos para estudiar mañana?",
  "reactions": {"❤️": 2},
  "mentions": [],
  "reply_id": null,
  "date": "2024-03-15T10:30:00+00:00",
  "media": {
    "type": "photo",
    "filename": "photo_67890.jpg",
    "path": "media_Grupo Estudio\\photo_67890.jpg",
    "downloaded": true
  }
}
```

```json
{
  "id": 67900,
  "sender_id": 123456789,
  "sender_name": "Carlos López",
  "sender_username": "carlos_tech",
  "text": "Aquí está el documento que mencioné",
  "reactions": {},
  "mentions": [],
  "reply_id": 67890,
  "date": "2024-03-15T10:35:00+00:00",
  "media": {
    "type": "document",
    "filename": "67900_apuntes.pdf",
    "path": "media_Grupo Estudio\\67900_apuntes.pdf",
    "downloaded": true
  }
}
```

---

## 🧹 Preprocesamiento del texto (cómo limpiar los mensajes)

Actualmente existe un preprocesamiento centrado en:

1. **Sustitución de enlaces**

   * Utilizar expresiones regulares para localizar URLs y sustituirlas por descripciones contextualizadas (ej. `[Video de YouTube]`, `[Reel de Instagram]`, `[Invitación a grupo de Telegram]`, `[Enlace externo]`, etc.).
   * Esto evita que URLs largas ensucien el texto y facilita el análisis semántico.

2. **Markdown → Texto plano**

   * Los mensajes con formato Markdown (negritas, cursivas, listas) se transforman a HTML con `markdown.markdown(...)`.
   * Luego `BeautifulSoup` analiza ese HTML y extrae el texto plano con `soup.get_text(...)`.
   * Esto preserva el contenido semántico (texto) y elimina etiquetas de formato.

3. **Preservación de emojis y reacciones**

   * Los emojis permanecen en el campo `text`. Las reacciones se guardan en `reactions` como un objeto con recuentos por emoji.

4. **Saneamiento de nombres de archivo**

   * Para almacenar medios en disco se construyen nombres seguros (se reemplazan caracteres inválidos para el sistema de archivos).

> Ejemplo de flujo (función `clean_message_text`):
>
> * Detectar y reemplazar URLs → `replace_link(...)`.
> * Convertir Markdown a HTML → `markdown.markdown(...)`.
> * Extraer texto limpio → `BeautifulSoup(...).get_text(...)`.
> * Devolver texto ya normalizado y sin URLs crudas.

---

## 🌳 Árbol de conocimiento / reconstrucción de hilos (planificado)

Próximamente se integrará una capa que permita **reconstruir hilos de conversación** incluso cuando Telegram no indique explícitamente a qué mensaje responde un texto. La idea:

* Analizar **secuencia temporal**, menciones, palabras clave y proximidad semántica.
* Construir un **grafo/árbol** donde los nodos sean mensajes y las aristas representen relaciones de respuesta o continuidad temática.
* Utilizarlo para: reconstruir hilos, agrupar subconversaciones, extraer temas y facilitar resúmenes automáticos.

Esto permitirá **restaurar contextos** en chats donde las referencias implícitas están fragmentadas.

---

## ⚙️ Ejecución (guía rápida)

1. Instalar las dependencias desde el `requirements.txt`:

```bash
pip install -r requirements.txt
```

2. Ejecutar la aplicación principal:

```bash
python main.py
```

> El `requirements.txt` debe listar `telethon`, `markdown`, `beautifulsoup4` y demás librerías que el proyecto requiere.

---

## 🗂️ Organización de archivos (resumen)

* `main.py` → punto de entrada.
* `telegram/` → lógica del cliente y worker (Telethon).
* `ui/` → interfaz PyQt (ventanas, widgets, diálogos).
* `utils/` → utilidades: `sanitize_filename`, análisis, caché, etc.
* `media_<chat_name>/` → carpetas donde se guardan imágenes, audio y documentos descargados.
* `output/<chat_name>_<start>_<end>.json` → JSON resultante por chat.

---

## 📝 Notas finales

* El JSON y la organización de medios están diseñados para **hacer reproducible y sencillo el pipeline de análisis**.
* El preprocesamiento actual es deliberadamente conservador: prioriza mantener el contenido legible y sustituir elementos ruidosos (URLs largos) por descriptores útiles para NLP.

---