#alarm_manager.py
"""
Gestor de alarmas inteligentes - Ejecuta alarmas en hilos separados
"""
import json
import os
import re
import asyncio
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
import queue
from enum import Enum
import schedule
from dataclasses import dataclass, field
from collections import defaultdict

try:
    import requests
    HAS_AI_API = True
    AI_PROVIDER = "openrouter"
except ImportError:
    HAS_AI_API = False
    AI_PROVIDER = None
    print("⚠️ requests es requerido: pip install requests")

try:
    from link_processor.main import LinkProcessor
    HAS_LINK_PROCESSOR = True
except ImportError:
    HAS_LINK_PROCESSOR = False

from regex.regex_extractor import extract_regex_patterns
from regex.regex_config import get_alarm_message_prompt, format_extracted_data_for_prompt, get_ai_prompt_for_regex


@dataclass
class AlarmMessage:
    """Mensaje extraído de Telegram"""
    id: int
    text: str
    date: datetime
    sender: str
    media: Optional[Dict] = None


@dataclass
class AlarmConfig:
    """Configuración de una alarma"""
    alarm_id: int
    chat_id: int
    chat_title: str
    interval: Dict[str, int]
    date_range: Dict[str, datetime]
    patterns: List[Dict[str, str]]
    last_analyzed_message_id: Optional[int] = None
    last_analysis_time: Optional[datetime] = None
    total_runs: int = 0
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    next_run: Optional[datetime] = None


class AlarmManager:
    """Gestor principal de alarmas que ejecuta en hilos separados"""
    
    def __init__(self, telegram_client=None, telegram_app=None):
        self.telegram_client = telegram_client
        self.telegram_app = telegram_app
        self.alarms: Dict[int, AlarmConfig] = {}
        self.alarm_threads = {}
        self.running = False
        self.alarm_queue = queue.Queue()
        self.message_cache = defaultdict(list)
        self.lock = threading.RLock()
        
        # Configurar API de IA si está disponible
        if HAS_AI_API:
            self.setup_ai_api()
        
        # Cargar alarmas existentes
        self.load_alarms()
        
        # Iniciar hilo de procesamiento de alarmas
        self.start_processing_thread()
        
        print("🚀 AlarmManager iniciado")

    def setup_ai_api(self):
        """Configurar API de IA (OpenRouter)"""
        try:
            # Intentar con variable de entorno
            api_key = os.getenv('OPENROUTER_API_KEY')
            
            if api_key and api_key != 'your_api_key_here':
                print("✅ OpenRouter API configurada desde variable de entorno")
                return
            
            # Intentar con APIKeyManager
            try:
                from utils.api_keys import api_key_manager
                api_key = api_key_manager.get_openrouter_key()
                
                if api_key and api_key != 'your_api_key_here':
                    print("✅ OpenRouter API configurada desde APIKeyManager")
                    return
                    
            except ImportError:
                print("⚠️ APIKeyManager no disponible")
            
            print("⚠️ OPENROUTER_API_KEY no configurada. Usando mensajes básicos.")
            
        except Exception as e:
            print(f"❌ Error configurando OpenRouter API: {e}")
    
    def load_alarms(self):
        """Cargar alarmas desde archivo"""
        config_file = "alarm_configurations/alarm_settings.json"
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                with self.lock:
                    for alarm_data in data.get('alarm_configs', []):
                        date_range = alarm_data.get('date_range', {})
                        if not date_range.get('from') or not date_range.get('to'):
                            print(f"⚠️ Alarma {alarm_data.get('id')} sin fechas válidas, usando valores por defecto")
                            alarm_data['date_range'] = {
                                'from': (datetime.now() - timedelta(days=7)).isoformat(),
                                'to': datetime.now().isoformat()
                            }
                        try:
                            alarm_id = alarm_data.get('id')
                            if not alarm_id:
                                continue
                            
                             # Convertir strings a datetime
                            date_range = alarm_data.get('date_range', {})
                            if 'from' in date_range and date_range['from']:
                                if isinstance(date_range['from'], str):
                                    date_range['from'] = datetime.fromisoformat(date_range['from'])
                            if 'to' in date_range and date_range['to']:
                                if isinstance(date_range['to'], str):
                                    date_range['to'] = datetime.fromisoformat(date_range['to'])
                            
                            if 'created_at' in alarm_data:
                                if isinstance(date_range['created_at'], str):
                                    alarm_data['created_at'] = datetime.fromisoformat(alarm_data['created_at'])
                            if 'last_analysis_time' in alarm_data:
                                if isinstance(alarm_data['last_analysis_time'], str):
                                    alarm_data['last_analysis_time'] = datetime.fromisoformat(alarm_data['last_analysis_time']) 

                            alarm = AlarmConfig(
                                alarm_id=alarm_id,
                                chat_id=alarm_data.get('chat_id'),
                                chat_title=alarm_data.get('chat_title', 'Desconocido'),
                                interval=alarm_data.get('interval', {}),
                                date_range=date_range,
                                patterns=alarm_data.get('patterns', []),
                                last_analyzed_message_id=alarm_data.get('last_analyzed_message_id'),
                                last_analysis_time=alarm_data['last_analysis_time'] 
                                    if alarm_data.get('last_analysis_time') else None,
                                total_runs=alarm_data.get('total_runs', 0),
                                enabled=alarm_data.get('enabled', True),
                                created_at=alarm_data['created_at'] 
                                    if alarm_data.get('created_at') else datetime.now()
                            )
                            
                            # Calcular próxima ejecución
                            alarm.next_run = self.calculate_next_run(alarm)
                            self.alarms[alarm_id] = alarm
                            
                        except Exception as e:
                            print(f"⚠️ Error cargando alarma {alarm_data.get('id')}: {e}")
                            continue
                
                print(f"✅ Cargadas {len(self.alarms)} alarmas")
                
            except Exception as e:
                print(f"❌ Error cargando archivo de alarmas: {e}")
    
    def save_alarms(self):
        """Guardar alarmas en archivo"""
        with self.lock:
            try:
                config_dir = "alarm_configurations"
                os.makedirs(config_dir, exist_ok=True)
                
                alarm_data = []
                for alarm in self.alarms.values():
                    alarm_dict = {
                        'id': alarm.alarm_id,
                        'chat_id': alarm.chat_id,
                        'chat_title': alarm.chat_title,
                        'interval': alarm.interval,
                        'date_range': {
                            'from': alarm.date_range['from'].isoformat() if 'from' in alarm.date_range else None,
                            'to': alarm.date_range['to'].isoformat() if 'to' in alarm.date_range else None
                        },
                        'patterns': alarm.patterns,
                        'last_analyzed_message_id': alarm.last_analyzed_message_id,
                        'last_analysis_time': alarm.last_analysis_time.isoformat() if alarm.last_analysis_time else None,
                        'total_runs': alarm.total_runs,
                        'enabled': alarm.enabled,
                        'created_at': alarm.created_at.isoformat(),
                        'next_run': alarm.next_run.isoformat() if alarm.next_run else None
                    }
                    alarm_data.append(alarm_dict)
                
                config_file = os.path.join(config_dir, "alarm_settings.json")
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        "alarm_configs": alarm_data,
                        "updated_at": datetime.now().isoformat()
                    }, f, indent=2, ensure_ascii=False)
                
                print(f"💾 {len(alarm_data)} alarmas guardadas")
                
            except Exception as e:
                print(f"❌ Error guardando alarmas: {e}")
    
    from datetime import timedelta

    def add_alarm(self, alarm_config_dict):
        """Añadir nueva alarma"""
        with self.lock:
            try:
                alarm_id = max(self.alarms.keys(), default=0) + 1
                
                # Convertir date_range strings a datetime
                date_range = alarm_config_dict.get('date_range', {})
                if 'from' in date_range and isinstance(date_range['from'], str):
                    date_range['from'] = datetime.fromisoformat(date_range['from'])
                if 'to' in date_range and isinstance(date_range['to'], str):
                    date_range['to'] = datetime.fromisoformat(date_range['to'])
                
                # 🔹 Calcular intervalo real en minutos
                interval = alarm_config_dict.get('interval', {})
                total_minutes = (
                    interval.get('days', 0) * 24 * 60 +
                    interval.get('hours', 0) * 60 +
                    interval.get('minutes', 0)
                )
                
                if total_minutes <= 0:
                    total_minutes = 1  # fallback de seguridad
                
                now = datetime.now()
                next_run = now + timedelta(minutes=total_minutes)
                
                alarm = AlarmConfig(
                    alarm_id=alarm_id,
                    chat_id=alarm_config_dict.get('chat_id'),
                    chat_title=alarm_config_dict.get('chat_title', 'Desconocido'),
                    interval=interval,
                    date_range=date_range,
                    patterns=alarm_config_dict.get('patterns', []),
                    created_at=now,
                    next_run=next_run
                )
                
                self.alarms[alarm_id] = alarm
                self.save_alarms()
                
                # Programar alarma
                self.schedule_alarm(alarm_id)
                
                print(f"✅ Alarma {alarm_id} añadida para: {alarm.chat_title}")
                print(f"⏭ Próxima ejecución: {next_run}")
                return alarm_id
                
            except Exception as e:
                print(f"❌ Error añadiendo alarma: {e}")
                return None


    def calculate_next_run(self, alarm):
        """Calcular próxima ejecución basada en intervalo"""
        last_run = alarm.last_analysis_time or alarm.created_at
        interval = alarm.interval
        
        # Calcular siguiente ejecución sumando el intervalo
        next_run = last_run + timedelta(
            days=interval.get('days', 0),
            hours=interval.get('hours', 0),
            minutes=interval.get('minutes', 0)
        )
        
        return next_run
    
    def schedule_alarm(self, alarm_id):
        """Programar alarma usando schedule"""
        with self.lock:
            alarm = self.alarms.get(alarm_id)
            if not alarm or not alarm.enabled:
                return
            
            interval = alarm.interval
            total_minutes = (
                interval.get('days', 0) * 24 * 60 +
                interval.get('hours', 0) * 60 +
                interval.get('minutes', 0)
            )
            
            if total_minutes > 0:
                # Crear job para esta alarma
                def alarm_job():
                    self.queue_alarm(alarm_id)
                
                # Programar con schedule
                schedule.every(total_minutes).minutes.do(alarm_job)
                print(f"⏰ Alarma {alarm_id} programada cada {total_minutes} minutos")

    def remove_alarm(self, alarm_id):
        with self.lock:
            if alarm_id in self.alarms:
                del self.alarms[alarm_id]
                print(f"🗑 Alarma {alarm_id} eliminada")

    
    def queue_alarm(self, alarm_id):
        """Encolar alarma para ejecución"""
        self.alarm_queue.put(alarm_id)
        print(f"📥 Alarma {alarm_id} encolada para ejecución")
    
    def start_processing_thread(self):
        """Iniciar hilo de procesamiento de alarmas"""
        self.running = True
        self.processing_thread = threading.Thread(
            target=self._process_alarms,
            daemon=True,
            name="AlarmProcessor"
        )
        self.processing_thread.start()
        print("🚀 Hilo de procesamiento de alarmas iniciado")
    
    def _process_alarms(self):
        """Procesar alarmas encoladas"""
        print("🔄 Iniciando procesamiento de alarmas...")
        
        while self.running:
            try:
                # Ejecutar jobs de schedule
                schedule.run_pending()
                
                # Procesar alarmas encoladas
                try:
                    alarm_id = self.alarm_queue.get(timeout=1)
                    self.execute_alarm(alarm_id)
                    self.alarm_queue.task_done()
                except queue.Empty:
                    pass
                
                # Limpiar hilos completados
                self._cleanup_threads()
                
            except Exception as e:
                print(f"❌ Error en procesamiento de alarmas: {e}")
                time.sleep(5)
    
    def _cleanup_threads(self):
        """Limpiar hilos de alarmas completados"""
        completed = []
        for alarm_id, thread in list(self.alarm_threads.items()):
            if not thread.is_alive():
                completed.append(alarm_id)
        
        for alarm_id in completed:
            del self.alarm_threads[alarm_id]
    
    def get_chat_messages(self, alarm: AlarmConfig) -> List[AlarmMessage]:
        """Obtener mensajes del chat desde Telegram"""
        try:
            if not self.telegram_client:
                print(f"⚠️ No hay cliente de Telegram disponible para alarma {alarm.alarm_id}")
                return []
            
            # Importar aquí para evitar dependencias circulares
            from telethon.tl.types import PeerUser, PeerChat, PeerChannel
            
            # Convertir chat_id al tipo de peer correcto
            chat_id = alarm.chat_id
            
            # Determinar desde dónde buscar mensajes
            offset_id = alarm.last_analyzed_message_id
            limit = 100  # Limitar a 100 mensajes por ejecución
            
            # Usar el worker para obtener mensajes si está disponible
            if hasattr(self, 'telegram_app') and self.telegram_app and hasattr(self.telegram_app, 'worker'):
                print(f"🔍 Obteniendo mensajes para chat {chat_id} (alarma {alarm.alarm_id})...")
                
                # Esta función debería ser implementada en async_worker.py
                # Por ahora, devolveremos una lista vacía y mostraremos cómo se haría
                return self._simulate_get_messages(alarm)
            else:
                # Simular obtención de mensajes para pruebas
                return self._simulate_get_messages(alarm)
                
        except Exception as e:
            print(f"❌ Error obteniendo mensajes para alarma {alarm.alarm_id}: {e}")
            return []
    
    def _simulate_get_messages(self, alarm: AlarmConfig) -> List[AlarmMessage]:
        """Simular obtención de mensajes para pruebas"""
        messages = []
        
        # Generar mensajes de ejemplo basados en los patrones configurados
        for i in range(1, 6):
            msg_id = (alarm.last_analyzed_message_id or 0) + i
            
            # Texto de ejemplo con diferentes patrones
            text_examples = [
                f"Mi correo es usuario{i}@example.com y mi teléfono es +34 600 000 00{i}",
                f"El precio es ${i * 100} USD y el descuento es del {i * 10}%",
                f"Reunión el {datetime.now().strftime('%d/%m/%Y')} a las {i + 10}:00",
                f"Visita nuestro sitio https://sitio{i}.com y síguenos en @usuario{i}",
                f"Coordenadas: {40.41 + i/100}, {-3.70 + i/100} #viaje{i}"
            ]
            
            text = text_examples[i % len(text_examples)]
            
            message = AlarmMessage(
                id=msg_id,
                text=text,
                date=datetime.now() - timedelta(hours=i),
                sender=f"Usuario{i}",
                media=None
            )
            messages.append(message)
        
        return messages
    
    def execute_alarm(self, alarm_id):
        """Ejecutar una alarma específica"""
        with self.lock:
            alarm = self.alarms.get(alarm_id)
            if not alarm or not alarm.enabled:
                return
        
        print(f"🔔 Ejecutando alarma {alarm_id}: {alarm.chat_title}")
        
        try:
            # 1. Obtener mensajes del chat
            messages = self.get_chat_messages(alarm)
            
            if not messages:
                self.send_no_updates(alarm)
                self.update_alarm_status(alarm_id, 0, messages)
                return
            
            # 2. Extraer información con patrones
            extracted_data = self.extract_information(messages, alarm)
            
            if not extracted_data:
                self.send_no_updates(alarm)
                self.update_alarm_status(alarm_id, 0, messages)
                return
            
            # 3. Generar mensaje con IA
            alarm_message = self.generate_alarm_message(extracted_data, alarm)
            
            # 4. Enviar a mensajes guardados
            self.send_to_saved_messages(alarm_message, alarm)
            
            # 5. Actualizar estado de la alarma
            self.update_alarm_status(alarm_id, len(messages), messages)
            
            print(f"✅ Alarma {alarm_id} completada exitosamente")
            
        except Exception as e:
            print(f"❌ Error ejecutando alarma {alarm_id}: {e}")
            self.send_error_notification(alarm, str(e))
    
    def extract_information(self, messages: List[AlarmMessage], alarm: AlarmConfig):
        """Extraer información de los mensajes usando los patrones configurados"""
        if not messages:
            return {}
        
        # Concatenar texto de todos los mensajes
        all_text = " ".join([msg.text for msg in messages if msg.text])
        
        if not all_text:
            return {}
        
        extracted = defaultdict(list)
        
        # Usar patrones configurados
        for pattern_config in alarm.patterns:
            pattern = pattern_config.get('pattern', '')
            name = pattern_config.get('name', 'Desconocido')
            
            if not pattern:
                continue
            
            try:
                matches = re.findall(pattern, all_text, re.IGNORECASE)
                if matches:
                    # Procesar enlaces si es necesario
                    if 'url' in name.lower() or 'enlace' in name.lower() or 'link' in name.lower():
                        if HAS_LINK_PROCESSOR:
                            processed_matches = []
                            for match in matches:
                                if isinstance(match, str):
                                    try:
                                        processor = LinkProcessor()
                                        processed = processor.process_url(match)
                                        processed_matches.append(processed)
                                    except:
                                        processed_matches.append(match)
                            matches = processed_matches
                    
                    # Agrupar por tipo de patrón
                    extracted[name].extend(matches[:10])  # Limitar a 10 resultados
                    
            except re.error as e:
                print(f"⚠️ Error en patrón '{name}': {pattern} - {e}")
            except Exception as e:
                print(f"⚠️ Error procesando patrón '{name}': {e}")
        
        # También usar el extractor de regex global
        try:
            global_patterns = extract_regex_patterns(all_text)
            for category, values in global_patterns.items():
                if values:
                    extracted[f"Global_{category}"].extend(values[:5])
        except Exception as e:
            print(f"⚠️ Error en extractor global: {e}")
        
        return dict(extracted)
    
    def generate_alarm_message(self, extracted_data, alarm: AlarmConfig):
        """Generar mensaje de alarma usando IA"""
        if not HAS_AI_API:
            return self.generate_basic_message(extracted_data, alarm)
        
        try:
            # Obtener API key
            api_key = os.getenv('OPENROUTER_API_KEY')
            if not api_key:
                return self.generate_basic_message(extracted_data, alarm)
            
            # Formatear datos para el prompt
            from regex.regex_config import format_extracted_data_for_prompt
            data_summary = format_extracted_data_for_prompt(extracted_data)
            
            # Obtener prompt
            prompt = get_alarm_message_prompt(extracted_data, alarm.chat_title)
            
            # Modelos a probar (todos gratuitos)
            models = [
                "meta-llama/llama-3.1-8b-instruct:free",
                "microsoft/phi-3-medium-128k-instruct:free",
                "google/gemma-2-9b-it:free"
            ]
            
            for model_id in models:
                try:
                    response = requests.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": model_id,
                            "messages": [
                                {"role": "system", "content": "Eres un asistente que crea resúmenes concisos y útiles."},
                                {"role": "user", "content": prompt}
                            ],
                            "temperature": 0.3,
                            "max_tokens": 500
                        },
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        message = result['choices'][0]['message']['content'].strip()
                        print(f"✅ Mensaje generado con {model_id}")
                        return message
                    
                except Exception as e:
                    print(f"⚠️ Error con {model_id}: {e}")
                    continue
            
            # Si todos fallan, usar mensaje básico
            return self.generate_basic_message(extracted_data, alarm)
            
        except Exception as e:
            print(f"⚠️ Error con IA, usando mensaje básico: {e}")
            return self.generate_basic_message(extracted_data, alarm)


    def generate_basic_message(self, extracted_data, alarm: AlarmConfig):
        """Generar mensaje básico sin IA"""
        lines = []
        lines.append(f"🔔 RESUMEN DE ALARMA: {alarm.chat_title}")
        lines.append(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        lines.append(f"🆔 Alarma ID: {alarm.alarm_id}")
        lines.append("")
        
        if not extracted_data:
            lines.append("📭 No se encontró información nueva.")
        else:
            lines.append("📊 INFORMACIÓN ENCONTRADA:")
            total_matches = 0
            for name, values in extracted_data.items():
                count = len(values) if isinstance(values, list) else 1
                total_matches += count
                sample = values[:2] if values and isinstance(values, list) else []
                sample_str = ", ".join(str(v) for v in sample) if sample else "N/A"
                lines.append(f"  • {name}: {count} encontrados")
                if sample:
                    lines.append(f"    → Ejemplos: {sample_str}")
            
            lines.append("")
            lines.append(f"📈 Total de coincidencias: {total_matches}")
        
        lines.append("")
        lines.append("⏰ Próxima revisión según intervalo configurado")
        
        return "\n".join(lines)

    def send_to_saved_messages(self, message: str, alarm):
        """Enviar mensaje a mensajes guardados de Telegram"""
        try:
            # Manejar tanto objetos AlarmConfig como diccionarios
            if isinstance(alarm, dict):
                alarm_id = alarm.get('alarm_id', 0)
                chat_title = alarm.get('chat_title', 'Desconocido')
            else:
                alarm_id = alarm.alarm_id
                chat_title = alarm.chat_title
            
            print(f"📤 Preparando envío de mensaje de alarma {alarm_id}...")
            
            # Verificar si tenemos el app de Telegram con worker
            if not hasattr(self, 'telegram_app') or not self.telegram_app:
                print("⚠️ No hay telegram_app, guardando en archivo")
                self._save_to_file_as_backup(message, alarm)
                return
            
            # Verificar si hay worker disponible
            if not hasattr(self.telegram_app, 'worker') or not self.telegram_app.worker:
                print("⚠️ No hay worker disponible, guardando en archivo")
                self._save_to_file_as_backup(message, alarm)
                return
            
            # Verificar si el worker tiene cliente
            if not hasattr(self.telegram_app.worker, 'client') or not self.telegram_app.worker.client:
                print("⚠️ Worker sin cliente, guardando en archivo")
                self._save_to_file_as_backup(message, alarm)
                return
            
            print(f"✅ Todo listo, creando worker para enviar...")
            
            # Crear un NUEVO worker para este envío
            from telegram.async_worker import AsyncWorker
            
            send_worker = AsyncWorker(None)
            send_worker.client = self.telegram_app.worker.client
            send_worker.loop = self.telegram_app.worker.loop
            
            # Configurar señales
            send_success = False
            send_error = None
            
            def on_send_success(msg):
                nonlocal send_success
                send_success = True
                print(f"✅ {msg}")
            
            def on_send_error(err):
                nonlocal send_error
                send_error = err
                print(f"❌ Error: {err}")
            
            send_worker.success.connect(on_send_success)
            send_worker.error.connect(on_send_error)
            
            # Configurar tarea
            send_worker.set_task("send_message", task_args={'message': message})
            
            # Iniciar y esperar
            print("🚀 Iniciando worker...")
            send_worker.start()
            
            # Esperar con timeout
            if send_worker.wait(10000):  # 10 segundos
                if send_success:
                    print(f"✅ Mensaje de alarma {alarm_id} enviado exitosamente")
                elif send_error:
                    print(f"⚠️ Error al enviar, guardando en archivo: {send_error}")
                    self._save_to_file_as_backup(message, alarm)
                else:
                    print(f"⚠️ Envío completado pero sin confirmación, guardando en archivo")
                    self._save_to_file_as_backup(message, alarm)
            else:
                print(f"⚠️ Timeout al enviar, guardando en archivo")
                self._save_to_file_as_backup(message, alarm)
                
        except Exception as e:
            print(f"❌ Error enviando mensaje de alarma: {e}")
            import traceback
            traceback.print_exc()
            self._save_to_file_as_backup(message, alarm)

    def _save_to_file_as_backup(self, message: str, alarm: AlarmConfig):
        """Guardar mensaje en archivo como respaldo"""
        try:
            # Manejar tanto objetos AlarmConfig como diccionarios
            if isinstance(alarm, dict):
                alarm_id = alarm.get('alarm_id', 0)
                chat_title = alarm.get('chat_title', 'Desconocido')
            else:
                alarm_id = alarm.alarm_id
                chat_title = alarm.chat_title
            log_dir = "alarm_logs"
            os.makedirs(log_dir, exist_ok=True)
            
            log_file = os.path.join(log_dir, f"alarma_{alarm_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"Alarma: {chat_title} (ID: {alarm_id})\n")
                f.write(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write("-" * 50 + "\n")
                f.write(message + "\n")
            
            print(f"💾 Mensaje de alarma {alarm_id} guardado como respaldo en: {log_file}")
                
        except Exception as e:
            print(f"❌ Error guardando mensaje de alarma en archivo: {e}")

    def send_no_updates(self, alarm: AlarmConfig):
        """Enviar notificación de que no hay actualizaciones"""
        message = f"📭 Alarma: {alarm.chat_title} (ID: {alarm.alarm_id})\nNo hay mensajes nuevos para analizar."
        self.send_to_saved_messages(message, alarm)
    
    def send_error_notification(self, alarm: AlarmConfig, error: str):
        """Enviar notificación de error"""
        message = f"❌ ERROR en alarma: {alarm.chat_title} (ID: {alarm.alarm_id})\nError: {error[:100]}"
        self.send_to_saved_messages(message, alarm)
    
    def update_alarm_status(self, alarm_id, messages_processed, messages=None):
        """Actualizar estado de la alarma"""
        with self.lock:
            alarm = self.alarms.get(alarm_id)
            if not alarm:
                return
            
            alarm.last_analysis_time = datetime.now()
            if messages:
                alarm.last_analyzed_message_id = max(msg.id for msg in messages) if messages else None
            alarm.total_runs += 1
            alarm.next_run = self.calculate_next_run(alarm)
            
            # Guardar cambios
            self.save_alarms()
            
            print(f"📊 Alarma {alarm_id} actualizada. Procesados {messages_processed} mensajes. Próxima ejecución: {alarm.next_run}")
    
    def test_alarm_patterns(self, alarm_id, test_text):
        """Probar patrones de una alarma con texto específico"""
        with self.lock:
            alarm = self.alarms.get(alarm_id)
            if not alarm:
                return {"error": f"Alarma {alarm_id} no encontrada"}
        
        # Simular mensajes con el texto de prueba
        test_message = AlarmMessage(
            id=999999,
            text=test_text,
            date=datetime.now(),
            sender="Usuario de prueba",
            media=None
        )
        
        # Extraer información
        extracted_data = self.extract_information([test_message], alarm)
        
        return {
            "alarm_id": alarm_id,
            "chat_title": alarm.chat_title,
            "test_text": test_text,
            "extracted_data": extracted_data,
            "patterns_count": len(alarm.patterns),
            "patterns": [p.get('name', 'Desconocido') for p in alarm.patterns]
        }
    
    def stop(self):
        """Detener el gestor de alarmas"""
        print("🛑 Deteniendo gestor de alarmas...")
        self.running = False
        
        # Esperar a que termine el hilo de procesamiento
        if hasattr(self, 'processing_thread') and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=2)
        
        # Limpiar jobs de schedule
        schedule.clear()
        
        print("✅ Gestor de alarmas detenido")
    
    def get_alarm_status(self):
        """Obtener estado de todas las alarmas"""
        with self.lock:
            status = []
            now = datetime.now()
            
            for alarm in self.alarms.values():
                time_left = "Ahora"

                if alarm.next_run:
                    time_delta = alarm.next_run - now
                    total_seconds = int(time_delta.total_seconds())

                    if total_seconds > 0:
                        days, remainder = divmod(total_seconds, 86400)  # 24*60*60
                        hours, remainder = divmod(remainder, 3600)
                        minutes, _ = divmod(remainder, 60)

                        parts = []
                        if days > 0:
                            parts.append(f"{days}d")
                        if hours > 0 or days > 0:
                            parts.append(f"{hours}h")
                        parts.append(f"{minutes}m")

                        time_left = " ".join(parts)

                status.append({
                    'id': alarm.alarm_id,
                    'title': alarm.chat_title,
                    'enabled': alarm.enabled,
                    'total_runs': alarm.total_runs,
                    'next_run': alarm.next_run.strftime('%d/%m/%Y %H:%M')
                                if alarm.next_run else "N/A",
                    'time_left': time_left,
                    'patterns': len(alarm.patterns),
                    'last_run': alarm.last_analysis_time.strftime('%d/%m/%Y %H:%M')
                                if alarm.last_analysis_time else "Nunca"
                })
            
            return status

    from datetime import datetime

    def _format_time_left(self, next_run):
        if not next_run:
            return "—"

        delta = next_run - datetime.now()

        if delta.total_seconds() <= 0:
            return "Ejecutándose…"

        total_seconds = int(delta.total_seconds())

        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60

        parts = []

        if days > 0:
            parts.append(f"{days}d")
        if hours > 0 or days > 0:
            parts.append(f"{hours}h")
        parts.append(f"{minutes}m")

        return " ".join(parts)
