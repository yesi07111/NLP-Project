#async_worker.py
import asyncio
import os
import json
from datetime import datetime
import re
from PyQt6.QtCore import QThread, pyqtSignal
from telethon import TelegramClient
from telethon import events
from telethon.tl.types import Channel, Chat, User
from telethon.tl.functions.messages import GetDialogFiltersRequest
from telethon.errors import SessionPasswordNeededError

from config.settings import API_ID, API_HASH, SESSION_NAME
from utils.cache import (
    save_chat_to_cache,
    load_chat_from_cache,
    save_session_info,
)
from utils.text_processing import sanitize_filename
from telegram.message_parser import parse_message

class AsyncWorker(QThread):
    success = pyqtSignal(str)
    error = pyqtSignal(str)
    chats_loaded = pyqtSignal(dict)
    code_sent = pyqtSignal()
    download_progress = pyqtSignal(str, int, int)
    download_completed = pyqtSignal(list, list)
    preview_loaded = pyqtSignal(list)
    conversation_threads_completed = pyqtSignal(dict)  # Señal cuando termine el análisis de hilos

    def __init__(self, client):
        super().__init__()
        self.client = client
        self.task = None
        self.phone = None
        self.code = None
        self.password = None
        self.loop = None
        self.sent_code = None
        self.selected_chats = []
        self.date_range = None
        self.analysis_type = None
        self.media_options = {
            "text": True,
            "images": False,
            "audio": False,
            "documents": False,
        }
        self.preview_limit = 50
        self.preview_offset = 0
        self.current_preview_chat = None

    def run(self):
        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

            try:
                self.client = TelegramClient(SESSION_NAME, API_ID, API_HASH, loop=self.loop)
            except TypeError:
                self.client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

            if self.task == "verify_session":
                self.loop.run_until_complete(self._verify_session())
            elif self.task == "send_code":
                self.loop.run_until_complete(self._send_code())
            elif self.task == "verify_code":
                self.loop.run_until_complete(self._verify_code())
            elif self.task == "verify_password":
                self.loop.run_until_complete(self._verify_password())
            elif self.task == "load_chats":
                self.loop.run_until_complete(self._load_chats())
            elif self.task == "download_chats":
                self.loop.run_until_complete(self._download_chats())
            elif self.task == "preview_chat":
                self.loop.run_until_complete(self._preview_chat())
            elif self.task == "send_message":
                self.loop.run_until_complete(self._send_message())
            elif self.task == "monitor_chats":
                self.loop.run_until_complete(self.monitor_chat_changes(self.task_args.get('chat_ids', [])))
        except Exception as e:
            try:
                self.error.emit(f"Error en worker: {e}")
            except Exception:
                print(f"Worker error (emit falló): {e}")
        finally:
            try:
                if getattr(self, "client", None):
                    try:
                        disc = self.client.disconnect()
                        if asyncio.iscoroutine(disc):
                            try:
                                self.loop.run_until_complete(disc)
                            except Exception:
                                pass
                    except Exception:
                        pass
            except Exception as e:
                print(f"Error durante desconexión del worker: {e}")
            finally:
                try:
                    if self.loop and not self.loop.is_closed():
                        self.loop.close()
                except Exception as e:
                    print(f"Error cerrando loop del worker: {e}")
                self.client = None
                self.loop = None

    def set_task(
        self,
        task_type,
        phone=None,
        code=None,
        password=None,
        selected_chats=None,
        date_range=None,
        analysis_type=None,
        media_options=None,
        preview_offset=0,
        task_args=None,
    ):
        # Manejar chat_ids como alias de selected_chats para monitoreo
        if task_args and 'chat_ids' in task_args and not selected_chats:
            selected_chats = task_args.get('chat_ids', [])
        self.task = task_type
        self.phone = phone
        self.code = code
        self.password = password
        self.selected_chats = selected_chats or []
        self.date_range = date_range
        self.analysis_type = analysis_type
        self.media_options = media_options or {
            "text": True,
            "images": False,
            "audio": False,
            "documents": False,
        }
        self.preview_offset = preview_offset
        self.task_args = task_args or {}

    async def _maybe_await(self, maybe_awaitable):
        try:
            if asyncio.iscoroutine(maybe_awaitable):
                return await maybe_awaitable
            return maybe_awaitable
        except Exception:
            return maybe_awaitable

    async def get_client(self):
        ok = await self._ensure_connection()
        if ok:
            return self.client
        return None

    async def _ensure_connection(self):
        try:
            if not getattr(self, "client", None):
                try:
                    self.client = TelegramClient(SESSION_NAME, API_ID, API_HASH, loop=self.loop)
                except TypeError:
                    self.client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

            is_conn = await self._maybe_await(self.client.is_connected())
            if not is_conn:
                await self._maybe_await(self.client.connect())

            return True
        except Exception as e:
            print(f"Error en conexión del worker: {e}")
            try:
                self.client = None
            except Exception:
                pass
            return False

    async def _send_code(self):
        try:
            ok = await self._ensure_connection()
            if not ok:
                self.error.emit("No se pudo conectar para enviar el código")
                return

            client = self.client

            is_auth = await self._maybe_await(client.is_user_authorized())
            if is_auth:
                self.success.emit("✅ Bienvenido de vuelta! Sesión ya activa.")
                await self._load_chats()
                return

            sent = await self._maybe_await(client.send_code_request(self.phone))
            self.sent_code = sent
            self.success.emit(f"Código enviado a {self.phone}")
            self.code_sent.emit()
        except Exception as e:
            self.error.emit(f"No se pudo enviar el código: {e}")

    async def _verify_code(self):
        try:
            ok = await self._ensure_connection()
            if not ok:
                self.error.emit("No se pudo conectar para verificar el código")
                return

            client = self.client

            phone_code_hash = None
            if getattr(self, "sent_code", None):
                phone_code_hash = getattr(self.sent_code, "phone_code_hash", None)

            try:
                if phone_code_hash:
                    await self._maybe_await(
                        client.sign_in(
                            phone=self.phone,
                            code=self.code,
                            phone_code_hash=phone_code_hash,
                        )
                    )
                else:
                    await self._maybe_await(client.sign_in(self.phone, self.code))
            except SessionPasswordNeededError:
                self.error.emit("password_required")
                return
            except Exception as signin_exc:
                txt = str(signin_exc).lower()
                if "password" in txt or "two-step" in txt or "two step" in txt:
                    self.error.emit("password_required")
                    return
                self.error.emit(f"Error verificando código: {signin_exc}")
                return

            try:
                await self._maybe_await(client.connect())
                await self._maybe_await(client.get_me())
            except Exception as e:
                self.error.emit(f"Error post-signin: {e}")
                return

            is_auth = await self._maybe_await(client.is_user_authorized())
            if not is_auth:
                self.error.emit("Sesión no autorizada tras verificar el código")
                return

            try:
                save_session_info(self.phone, self.password)
            except Exception:
                pass

            self.success.emit("¡Autenticación completada!")
            await self._load_chats()
        except Exception as e:
            self.error.emit(f"Error verificando código: {e}")

    async def _verify_password(self):
        try:
            if not await self._ensure_connection():
                self.error.emit("No se pudo conectar para verificar el pase seguro")
                return

            client = self.client

            try:
                await self._maybe_await(client.sign_in(password=self.password))
            except Exception as signin_exc:
                self.error.emit(f"Error verificando pase seguro: {signin_exc}")
                return

            try:
                await self._maybe_await(client.connect())
                await self._maybe_await(client.get_me())
            except Exception as e:
                self.error.emit(f"Error post-password-signin: {e}")
                return

            is_auth = await self._maybe_await(client.is_user_authorized())
            if not is_auth:
                self.error.emit("Sesión no autorizada tras verificar el pase seguro")
                return

            try:
                save_session_info(self.phone, self.password)
            except Exception:
                pass

            self.success.emit("¡Autenticación con pase seguro completada!")
            await self._load_chats()
        except Exception as e:
            self.error.emit(f"Error verificando pase seguro: {e}")

    async def _load_chats(self):
        try:
            if not await self._ensure_connection():
                self.error.emit("No se pudo establecer conexión para cargar chats")
                return

            client = self.client

            chats_data = {
                "all": [],
                "unread": [],
                "personal": [],
                "groups": [],
                "folders": {},
            }
            folders_map_by_peerid = {}
            folders_by_id = {}

            try:
                filters_resp = await client(GetDialogFiltersRequest())
                filters_list = getattr(filters_resp, "filters", []) or []

                for folder in filters_list:
                    raw_title = getattr(folder, "title", None) or getattr(folder, "name", None)
                    if hasattr(raw_title, "text"):
                        folder_name = raw_title.text
                    else:
                        folder_name = (
                            str(raw_title) if raw_title is not None
                            else f"Carpeta_{getattr(folder, 'id', '')}"
                        )
                    folder_name = folder_name or f"Carpeta_{getattr(folder, 'id', '')}"
                    chats_data["folders"][folder_name] = []

                    fid = getattr(folder, "id", None)
                    if fid is not None:
                        folders_by_id[fid] = folder_name

                    include_peers = (
                        getattr(folder, "include_peers", None)
                        or getattr(folder, "peers", None)
                        or []
                    )
                    if include_peers:
                        for peer in include_peers:
                            try:
                                try:
                                    ent = await client.get_entity(peer)
                                    pid = getattr(ent, "id", None)
                                except Exception:
                                    pid = None
                                    if hasattr(peer, "user_id"):
                                        pid = getattr(peer, "user_id", None)
                                    elif hasattr(peer, "chat_id"):
                                        pid = getattr(peer, "chat_id", None)
                                    elif hasattr(peer, "channel_id"):
                                        pid = getattr(peer, "channel_id", None)
                                if pid:
                                    folders_map_by_peerid[pid] = folder_name
                            except Exception as e:
                                print(f"Warning resolviendo peer en carpeta '{folder_name}': {e}")

            except Exception as e:
                print(f"Error obteniendo carpetas: {e}")

            # Buscar "Mensajes guardados" primero
            saved_messages_chat = None
            
            try:
                # Obtener el usuario actual
                me = await client.get_me()
                if me:
                    saved_messages_chat = {
                        "id": me.id,
                        "name": "💾 Mensajes guardados",
                        "unread_count": 0,
                        "entity": me,
                        "is_saved_messages": True
                    }
            except Exception as e:
                print(f"Error obteniendo mensajes guardados: {e}")

            try:
                async for dialog in client.iter_dialogs():
                    try:
                        ent = getattr(dialog, "entity", None)
                        ent_id = getattr(ent, "id", None) if ent else None
                        dialog_folder_id = getattr(dialog, "folder_id", None)

                        name = ""
                        if ent:
                            name = getattr(ent, "title", None) or (
                                str(getattr(ent, "first_name", "") or "")
                                + (
                                    " " + getattr(ent, "last_name", "")
                                    if getattr(ent, "last_name", None)
                                    else ""
                                )
                            )
                            if not name.strip():
                                name = getattr(ent, "username", None) or str(ent)
                        else:
                            name = getattr(dialog, "name", None) or str(dialog)

                        unread = int(
                            getattr(dialog, "unread_count", None)
                            or getattr(dialog, "unread_messages_count", 0)
                            or 0
                        )

                        chat_info = {
                            "id": ent_id or getattr(dialog, "id", None),
                            "name": str(name),
                            "unread_count": unread,
                            "entity": ent,
                        }

                        chats_data["all"].append(chat_info)
                        if chat_info["unread_count"] > 0:
                            chats_data["unread"].append(chat_info)

                        if isinstance(ent, User):
                            # Verificar si es el usuario mismo (Mensajes guardados)
                            if ent.is_self:
                                chat_info["name"] = "💾 Mensajes guardados"
                                chat_info["is_saved_messages"] = True
                                saved_messages_chat = chat_info
                            else:
                                chats_data["personal"].append(chat_info)
                        elif isinstance(ent, (Chat, Channel)):
                            chats_data["groups"].append(chat_info)
                        else:
                            if getattr(ent, "username", None) or getattr(ent, "first_name", None):
                                chats_data["personal"].append(chat_info)
                            else:
                                chats_data["groups"].append(chat_info)

                        assigned = False
                        if ent_id and ent_id in folders_map_by_peerid:
                            fname = folders_map_by_peerid[ent_id]
                            chats_data["folders"].setdefault(fname, []).append(chat_info)
                            assigned = True

                        if (
                            not assigned
                            and dialog_folder_id is not None
                            and dialog_folder_id in folders_by_id
                        ):
                            fname = folders_by_id[dialog_folder_id]
                            chats_data["folders"].setdefault(fname, []).append(chat_info)

                    except Exception as e:
                        print(f"Error procesando diálogo {getattr(dialog, 'id', '<no-id>')}: {e}")
                        continue
            except Exception as e:
                print(f"Error iterando diálogos: {e}")

            # Agregar mensajes guardados al principio de personales si existe
            if saved_messages_chat:
                chats_data["personal"].insert(0, saved_messages_chat)
            
            # Filtrar pestañas vacías
            # Solo mostrar "No Leídos" si hay chats no leídos
            if not chats_data["unread"]:
                chats_data.pop("unread", None)

            # Filtrar carpetas vacías
            chats_data["folders"] = {k: v for k, v in chats_data["folders"].items() if v}

            # Mantener referencia al cliente activo
            print("✅ Cliente de Telegram activo y listo para alarmas")
            
            self.chats_loaded.emit(chats_data)

        except Exception as e:
            self.error.emit(f"Error cargando chats: {e}")

    # Modificar la función monitor_chat_changes en async_worker.py:
    async def monitor_chat_changes(self, chat_ids):
        """Monitorear cambios en chats específicos en tiempo real"""
        try:
            if not await self._ensure_connection():
                print("❌ No se pudo conectar para monitoreo de chats")
                return
            
            client = self.client
            
            print(f"🔍 Iniciando monitoreo de {len(chat_ids)} chats...")
            
            # Crear un diccionario para mapear IDs a nombres de chat
            self.chat_names = {}
            for chat_id in chat_ids:
                try:
                    entity = await client.get_entity(chat_id)
                    if hasattr(entity, 'title'):
                        self.chat_names[chat_id] = entity.title
                    elif hasattr(entity, 'first_name'):
                        name = entity.first_name
                        if hasattr(entity, 'last_name') and entity.last_name:
                            name += f" {entity.last_name}"
                        self.chat_names[chat_id] = name
                    else:
                        self.chat_names[chat_id] = f"Chat {chat_id}"
                    print(f"✅ Chat {chat_id} ({self.chat_names[chat_id]}) preparado para monitoreo")
                except Exception as e:
                    print(f"⚠️ No se pudo obtener entidad para chat {chat_id}: {e}")
                    self.chat_names[chat_id] = f"Chat {chat_id}"
            
            # Definir manejador de eventos para nuevos mensajes
            @client.on(events.NewMessage())
            async def handler(event):
                try:
                    chat_id = event.chat_id
                    
                    # Verificar si estamos monitoreando este chat
                    if chat_id not in chat_ids:
                        return
                    
                    print(f"📨 Nuevo mensaje en chat {self.chat_names.get(chat_id, chat_id)}")
                    
                    # Procesar mensaje
                    message_data = {
                        'chat_id': chat_id,
                        'chat_name': self.chat_names.get(chat_id, f"Chat {chat_id}"),
                        'text': event.message.text or "",
                        'sender_id': event.message.sender_id,
                        'date': event.message.date,
                        'message_id': event.message.id
                    }
                    
                    # Obtener información del remitente
                    try:
                        sender = await event.get_sender()
                        if sender:
                            if hasattr(sender, 'first_name'):
                                message_data['sender_name'] = sender.first_name
                                if hasattr(sender, 'last_name') and sender.last_name:
                                    message_data['sender_name'] += f" {sender.last_name}"
                            elif hasattr(sender, 'title'):
                                message_data['sender_name'] = sender.title
                            elif hasattr(sender, 'username'):
                                message_data['sender_name'] = f"@{sender.username}"
                    except Exception as e:
                        print(f"⚠️ Error obteniendo remitente: {e}")
                        message_data['sender_name'] = "Desconocido"
                    
                    # Mostrar información del mensaje
                    preview = message_data['text'][:100] + "..." if len(message_data['text']) > 100 else message_data['text']
                    print(f"   👤 De: {message_data.get('sender_name', 'Desconocido')}")
                    print(f"   💬 Texto: {preview}")
                    print(f"   ⏰ Hora: {message_data['date']}")
                    
                    # Aquí podrías emitir una señal para actualizar la interfaz
                    # Por ejemplo: self.new_message_signal.emit(message_data)
                    
                    # Verificar patrones de alarma inmediatamente
                    await self.check_alarm_patterns(chat_id, message_data)
                    
                except Exception as e:
                    print(f"❌ Error procesando nuevo mensaje: {e}")
            
            print("✅ Monitoreo activado. Esperando nuevos mensajes...")
            
            # Mantener el cliente conectado
            await client.run_until_disconnected()
            
        except Exception as e:
            print(f"❌ Error en monitoreo de chats: {e}")


    async def _verify_session(self):
        try:
            ok = await self._ensure_connection()
            if not ok:
                self.error.emit("No se pudo conectar para verificar sesión")
                return

            client = self.client

            is_auth = await self._maybe_await(client.is_user_authorized())
            if is_auth:
                me = await self._maybe_await(client.get_me())
                if me and getattr(me, "phone", None):
                    current_phone = me.phone or ""
                    if self.phone:
                        def norm(p):
                            return re.sub(r"[\s\-\(\)\+]", "", str(p or ""))

                        normalized_input = norm(self.phone)
                        normalized_current = norm(current_phone)

                        if normalized_input == normalized_current:
                            self.success.emit("session_valid")
                            return
                        else:
                            try:
                                await self._maybe_await(client.log_out())
                            except Exception:
                                pass
                            try:
                                sess = getattr(client, "session", None)
                                if sess and hasattr(sess, "delete"):
                                    try:
                                        sess.delete()
                                    except Exception:
                                        pass
                                else:
                                    try:
                                        session_file = f"{SESSION_NAME}.session"
                                        if os.path.exists(session_file):
                                            os.remove(session_file)
                                    except Exception:
                                        pass
                            except Exception:
                                pass

                            await self._send_code()
                            return
                    else:
                        self.success.emit("session_valid")
                        return

            if self.phone:
                await self._send_code()
            else:
                self.success.emit("session_invalid")
        except Exception as e:
            self.error.emit(f"Error verificando sesión: {e}")

    async def _download_chats(self):
        if not await self._ensure_connection():
            self.error.emit("No se pudo establecer conexión con Telegram")
            return

        client = self.client

        successful = []
        failed = []
        total_chats = len(self.selected_chats or [])

        # Si no hay chats seleccionados pero es análisis de hilos, procesar archivos existentes
        if not self.selected_chats and self.analysis_type == "threads":
            print("🧵 No hay chats seleccionados, procesando análisis de hilos existentes...")
            await self._process_conversation_threads()
            self.download_completed.emit([], [])
            return

        if not self.selected_chats:
            self.error.emit("No se seleccionaron chats para descarga")
            return

        start_date, end_date = self.date_range

        for i, chat_info in enumerate(self.selected_chats):
            try:
                self.download_progress.emit(chat_info["name"], i + 1, total_chats)
                messages = []
                entity = chat_info["entity"]
                chat_name = chat_info["name"]

                print(f"📥 Descargando mensajes de: {chat_name} ({start_date} a {end_date})")

                async for message in client.iter_messages(entity, limit=None):
                    if not getattr(message, "date", None):
                        continue
                    message_date = message.date.date()

                    if message_date < start_date:
                        break
                    if message_date > end_date:
                        continue

                    data = await parse_message(message)
                    media_info = await self._process_media(message, chat_name)

                    msg_data = {
                        **data,
                        "media": media_info,
                    }

                    messages.append(msg_data)
                
                if messages:
                    await self._save_chat_files(chat_name, messages, start_date, end_date, self.task_args.get('path', '.'))
                    successful.append(chat_name)
                    print(f"✅ Chat {chat_name} procesado: {len(messages)} mensajes")
                else:
                    failed_msg = f"{chat_name}: No hay mensajes en el rango de fechas ({start_date} - {end_date})"
                    failed.append(failed_msg)
                    print(f"⚠️ {failed_msg}")

            except Exception as e:
                error_msg = f"{chat_info.get('name', '<unknown>')}: {str(e)}"
                failed.append(error_msg)
                print(f"❌ Error en {chat_info.get('name', '<unknown>')}: {e}")

        try:
            if self.analysis_type == "threads":
                await self._process_conversation_threads()
            # else:
            #     await self._set_alarms() #TODO: Implementar esa funcion de alarmas
        except Exception as e:
            print(f"Error en análisis: {e}")

        self.download_completed.emit(successful, failed)

    async def _save_chat_files(self, chat_name, messages, start_date, end_date, path = "."):
        safe_name = sanitize_filename(chat_name)
        filename_base = f"{safe_name}_{start_date}_{end_date}"

        json_data = {
            "metadata": {
                "chat_name": chat_name,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_messages": len(messages),
                "generated_at": datetime.now().isoformat(),
            },
            "messages": messages,
        }

        if path != ".":
            os.makedirs(path, exist_ok=True)

        json_filename = os.path.join(path, f"{filename_base}.json")

        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)

    # async def _preview_chat(self):
    #     try:
    #         if not self.selected_chats:
    #             self.error.emit("No se especificó chat para vista previa")
    #             return

    #         chat_info = self.selected_chats[0]

    #         cached_messages = load_chat_from_cache(chat_info)
    #         if cached_messages:
    #             print(f"Usando caché para {chat_info['name']}")
    #             self.preview_loaded.emit(cached_messages)
    #             return

    #         if not await self._ensure_connection():
    #             self.error.emit("No autenticado para vista previa")
    #             return

    #         client = self.client

    #         entity = chat_info["entity"]
    #         self.current_preview_chat = chat_info

    #         messages = []
    #         count = 0

    #         chat_type = "desconocido"
    #         try:
    #             if isinstance(entity, User):
    #                 chat_type = "usuario"
    #             elif isinstance(entity, Channel):
    #                 if hasattr(entity, "megagroup") and entity.megagroup:
    #                     chat_type = "grupo_mega"
    #                 elif hasattr(entity, "broadcast") and entity.broadcast:
    #                     chat_type = "canal"
    #                 else:
    #                     chat_type = "canal_o_grupo"
    #             elif isinstance(entity, Chat):
    #                 chat_type = "grupo_pequeño"
    #         except Exception as e:
    #             print(f"Error determinando tipo de chat: {e}")

    #         print(f"Vista previa para {chat_info['name']} (tipo: {chat_type})")

    #         async for message in client.iter_messages(
    #             entity, limit=self.preview_limit, offset_id=self.preview_offset
    #         ):
    #             try:
    #                 sender_name = "Unknown"
    #                 if getattr(message, "sender", None):
    #                     sender = message.sender
    #                     if hasattr(sender, "first_name"):
    #                         sender_name = str(getattr(sender, "first_name", "") or "")
    #                         if hasattr(sender, "last_name") and getattr(sender, "last_name", None):
    #                             sender_name += f" {str(getattr(sender, 'last_name', '') or '')}"
    #                     elif hasattr(sender, "title"):
    #                         sender_name = str(getattr(sender, "title", "") or "")
    #                     elif hasattr(sender, "username"):
    #                         sender_name = f"@{str(getattr(sender, 'username', '') or '')}"
    #                 else:
    #                     sender_name = "Usuario"
    #             except Exception:
    #                 sender_name = "Unknown"

    #             message_text = str(getattr(message, "text", "") or "")

    #             media_info = await self._process_media(message, chat_info["name"])

    #             msg_data = {
    #                 "id": message.id,
    #                 "date": message.date.isoformat() if getattr(message, "date", None) else "",
    #                 "sender": sender_name,
    #                 "text": message_text,
    #                 "media": media_info,
    #                 "chat_type": chat_type,
    #             }
    #             messages.append(msg_data)
    #             count += 1

    #         if messages:
    #             save_chat_to_cache(chat_info, messages)

    #         self.preview_loaded.emit(messages)

    #     except Exception as e:
    #         error_msg = f"Error en vista previa: {e}"
    #         print(error_msg)
    #         self.error.emit(error_msg)

    async def _preview_chat(self):
        try:
            if not self.selected_chats:
                self.error.emit("No se especificó chat para vista previa")
                return

            chat_info = self.selected_chats[0]

            # 1️⃣ Cargar caché
            cached_messages = load_chat_from_cache(chat_info) or []
            cached_ids = {msg["id"] for msg in cached_messages}

            if cached_messages:
                print(f"📦 Caché cargado: {len(cached_messages)} mensajes")

            # 2️⃣ Determinar cuántos faltan
            missing = self.preview_limit - len(cached_messages)
            messages = list(cached_messages)

            if missing > 0:
                if not await self._ensure_connection():
                    self.error.emit("No autenticado para vista previa")
                    return

                client = self.client
                entity = chat_info["entity"]
                self.current_preview_chat = chat_info

                fetched = 0

                # 🔑 CLAVE:
                # offset_id = 0 → mensajes MÁS RECIENTES
                async for message in client.iter_messages(
                    entity,
                    limit=missing,
                    offset_id=0
                ):
                    if message.id in cached_ids:
                        continue

                    sender_name = "Usuario"
                    try:
                        sender = message.sender
                        if sender:
                            if hasattr(sender, "first_name"):
                                sender_name = sender.first_name or ""
                                if getattr(sender, "last_name", None):
                                    sender_name += f" {sender.last_name}"
                            elif hasattr(sender, "title"):
                                sender_name = sender.title
                            elif hasattr(sender, "username"):
                                sender_name = f"@{sender.username}"
                    except Exception:
                        pass

                    media_info = await self._process_media(message, chat_info["name"])

                    msg_data = {
                        "id": message.id,
                        "date": message.date.isoformat() if message.date else "",
                        "sender": sender_name,
                        "text": message.text or "",
                        "media": media_info,
                    }

                    messages.append(msg_data)
                    fetched += 1

                if fetched:
                    print(f"🔄 Completados {fetched} mensajes desde Telegram")
                    save_chat_to_cache(chat_info, messages)

            # 3️⃣ Emitir UNA SOLA VEZ
            self.preview_loaded.emit(messages)

        except Exception as e:
            error_msg = f"Error en vista previa: {e}"
            print(error_msg)
            self.error.emit(error_msg)


    async def _process_media(self, message, chat_name):
        if not getattr(message, "media", None):
            return None

        media_info = {"type": None, "filename": None, "path": None, "downloaded": False}

        try:
            client = self.client
            safe_chat_name = sanitize_filename(chat_name)
            media_folder = f"media_{safe_chat_name}"
            os.makedirs(media_folder, exist_ok=True)

            if hasattr(message.media, "photo") and self.media_options.get("images", False):
                media_info["type"] = "photo"
                filename = f"photo_{message.id}.jpg"
                filepath = os.path.join(media_folder, filename)
                try:
                    await self._maybe_await(client.download_media(message.media, filepath))
                    media_info["filename"] = filename
                    media_info["path"] = filepath
                    media_info["downloaded"] = True
                except Exception:
                    media_info["downloaded"] = False

            elif hasattr(message.media, "document") and message.media.document:
                doc = message.media.document
                is_audio = any(
                    getattr(attr, "mime_type", "").startswith("audio/")
                    for attr in getattr(doc, "attributes", [])
                    if hasattr(attr, "mime_type")
                )
                is_voice = any(
                    getattr(attr, "voice", False)
                    for attr in getattr(doc, "attributes", [])
                )

                if (is_audio or is_voice) and self.media_options.get("audio", False):
                    media_info["type"] = "audio"
                    ext = ".ogg" if is_voice else ".mp3"
                    filename = f"audio_{message.id}{ext}"
                elif self.media_options.get("documents", False):
                    media_info["type"] = "document"
                    original_name = None
                    for attr in getattr(doc, "attributes", []):
                        if hasattr(attr, "file_name") and attr.file_name:
                            original_name = attr.file_name
                            break
                    if original_name:
                        filename = f"{message.id}_{original_name}"
                    else:
                        filename = f"document_{message.id}"
                else:
                    return {"type": "unsupported", "downloaded": False}

                if media_info["type"] in ["audio", "document"]:
                    filepath = os.path.join(media_folder, filename)
                    try:
                        await self._maybe_await(client.download_media(message.media, filepath))
                        media_info["filename"] = filename
                        media_info["path"] = filepath
                        media_info["downloaded"] = True
                    except Exception:
                        media_info["downloaded"] = False

        except Exception as e:
            print(f"Error procesando media: {e}")
            media_info["downloaded"] = False

        return media_info

    async def _process_conversation_threads(self):
        """Procesa los hilos de conversación usando el grafo de conocimiento"""
        try:
            print("🧵 Iniciando análisis de hilos de conversación...")
            
            # Importar el módulo de análisis de hilos
            from threads_analysis.main import process_chat_for_knowledge_graph
            
            # Buscar archivos JSON en la carpeta threads_analysis_results/chats/
            import glob
            json_files = glob.glob("threads_analysis_results/chats/*.json")
            if not json_files:
                self.error.emit("No se encontraron archivos JSON en threads_analysis_results/chats/")
                return
            
            print(f"📁 Encontrados {len(json_files)} archivos para analizar")
            
            results = {}
            successful_files = 0
            
            # Acumular todos los mensajes para análisis de sentimientos global
            all_messages = []
            
            # Procesar cada archivo JSON encontrado
            for json_file in json_files:
                try:
                    print(f"🔍 Analizando: {json_file}")
                    
                    # Cargar mensajes para análisis de sentimientos
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    all_messages.extend(data.get("messages", []))
                    
                    # Procesar el chat y obtener el grafo, hilos y análisis
                    graph, threads, analysis = process_chat_for_knowledge_graph(json_file)
                    
                    # Solo contar como exitoso si tenemos resultados
                    if graph is not None and threads is not None and analysis is not None:
                        # Guardar los resultados por archivo
                        base_name = os.path.basename(json_file)
                        results[base_name] = {
                            "graph_info": {
                                "total_nodos": len(graph.nodes()),
                                "total_aristas": len(graph.edges()),
                                "metadata": graph.graph.get('metadata', {})
                            },
                            "threads_count": len(threads),
                            "analysis_summary": {
                                "total_hilos": analysis['thread_metrics']['total_threads'],
                                "hilo_promedio": analysis['thread_metrics']['avg_thread_length'],
                                "usuarios_activos": len(analysis['user_engagement']['most_active_users']),
                                "patrones_detectados": analysis['conversation_patterns']['total_conversation_patterns']
                            }
                        }
                        successful_files += 1
                        print(f"✅ Completado: {base_name} - {len(threads)} hilos encontrados")
                    else:
                        print(f"⚠️  Archivo {json_file} no pudo ser procesado correctamente")
                    
                except Exception as e:
                    print(f"❌ Error procesando {json_file}: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            if successful_files == 0:
                self.error.emit("No se pudo procesar ningún archivo correctamente. Verifica que los archivos JSON tengan la estructura correcta.")
                return

            # Análisis de sentimientos global
            print(f"📊 Iniciando análisis de sentimientos en {len(all_messages)} mensajes...")
            
            if all_messages:
                # Importar y usar el módulo de análisis de sentimientos
                from utils.sentiments.sentiment_analysis import get_sentiment_summary
                summary = get_sentiment_summary(all_messages)
                
                # Guardar el resumen global en un archivo para la UI
                summary_file = "threads_analysis_results/global_sentiment_summary.json"
                os.makedirs(os.path.dirname(summary_file), exist_ok=True)
                
                with open(summary_file, 'w', encoding='utf-8') as f:
                    json.dump(summary, f, ensure_ascii=False, indent=2)
                print(f"✅ Resumen de sentimientos global guardado en {summary_file}")
            else:
                print("⚠️  No hay mensajes para análisis de sentimientos")
                summary = {
                    "total_messages": 0,
                    "average_score": 0.0,
                    "most_common_sentiment": "N/A",
                    "distribution": {},
                    "percentages": {},
                    "user_sentiments": {}
                }

            # Emitir señal con los resultados completos
            print("📤 Emitiendo señal conversation_threads_completed...")
            self.conversation_threads_completed.emit({
                "archivos_procesados": successful_files,
                "archivos_totales": len(json_files),
                "resultados_detallados": results,
                "resumen_sentimientos": summary,
                "timestamp": datetime.now().isoformat()
            })

            print(f"🎉 Análisis de hilos y sentimientos completado: {successful_files}/{len(json_files)} archivos procesados exitosamente")
            
        except Exception as e:
            error_msg = f"Error en análisis de hilos: {str(e)}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            self.error.emit(error_msg)

    def close_loop(self):
        try:
            if getattr(self, "client", None) and self.loop and not self.loop.is_closed():
                try:
                    disc = self.client.disconnect()
                    if asyncio.iscoroutine(disc):
                        try:
                            self.loop.run_until_complete(disc)
                        except Exception:
                            pass
                except Exception:
                    pass
        except Exception as e:
            print(f"Error cerrando cliente del worker: {e}")
        finally:
            try:
                if self.loop and not self.loop.is_closed():
                    self.loop.close()
            except Exception as e:
                print(f"Error cerrando loop del worker: {e}")
            self.client = None
            self.loop = None

    async def _send_message(self):
        """Enviar mensaje a mensajes guardados"""
        try:
            print("📤 Iniciando envío de mensaje...")
            
            if not await self._ensure_connection():
                print("❌ No se pudo conectar")
                self.error.emit("No se pudo conectar para enviar el mensaje")
                return
            
            client = self.client
            message = self.task_args.get('message', '')
            
            if not message:
                print("⚠️ Mensaje vacío")
                self.error.emit("El mensaje está vacío")
                return
            
            print(f"✅ Cliente conectado, enviando mensaje de {len(message)} caracteres...")
            
            # Enviar a "me" que son los mensajes guardados
            result = await client.send_message("me", message)
            
            print(f"✅ Mensaje enviado exitosamente (ID: {result.id})")
            self.success.emit("✅ Mensaje enviado a Mensajes Guardados")
            
        except Exception as e:
            error_msg = f"Error enviando mensaje: {e}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            self.error.emit(error_msg)





