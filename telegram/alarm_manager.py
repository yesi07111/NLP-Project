#alarm_manager.py
"""
Gestor de alarmas inteligentes - Ejecuta alarmas en hilos separados
"""
import os
import re
import json
import pytz
import time
import queue
import schedule
import threading
from typing import List
from collections import defaultdict, Counter
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

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

    def __init__(self, telegram_client, telegram_app=None):
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

        # 1️⃣ Cargar alarmas desde disco
        self.load_alarms()

        # 2️⃣ 🔥 NORMALIZAR tiempos (tratarlas como nuevas)
        self.normalize_loaded_alarms()

        # 3️⃣ 🔁 REPROGRAMAR alarmas en schedule
        self.schedule_all_alarms()

        # 4️⃣ Iniciar procesamiento
        self.start_processing_thread()

        print("🚀 AlarmManager iniciado")

    def normalize_loaded_alarms(self):
        """Recalcula tiempos de alarmas cargadas como si fueran nuevas"""
        now = datetime.now(timezone.utc)

        with self.lock:
            for alarm_id, alarm in self.alarms.items():
                if not alarm.enabled:
                    continue

                interval = alarm.interval
                delta = timedelta(
                    days=interval.get('days', 0),
                    hours=interval.get('hours', 0),
                    minutes=interval.get('minutes', 0)
                )

                if delta.total_seconds() <= 0:
                    print(f"⚠️ Alarma {alarm_id} sin intervalo válido, omitida")
                    continue

                # 🔥 TRATAR COMO NUEVA
                alarm.last_analysis_time = None
                alarm.created_at = now
                alarm.next_run = now 

                print(
                    f"🔁 Alarma {alarm_id} normalizada → next_run: "
                    f"{alarm.next_run.strftime('%H:%M:%S')}"
                )

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

        if not os.path.exists(config_file):
            return

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            with self.lock:
                for alarm_data in data.get('alarm_configs', []):
                    try:
                        alarm_id = alarm_data.get('id')
                        if not alarm_id:
                            continue

                        # --- date_range ---
                        date_range = alarm_data.get('date_range', {})
                        if not date_range.get('from') or not date_range.get('to'):
                            print(f"⚠️ Alarma {alarm_id} sin fechas válidas, usando valores por defecto")
                            date_range = {
                                'from': datetime.now(timezone.utc) - timedelta(days=7),
                                'to': datetime.now(timezone.utc)
                            }
                        else:
                            if isinstance(date_range.get('from'), str):
                                date_range['from'] = datetime.fromisoformat(date_range['from'])
                            if isinstance(date_range.get('to'), str):
                                date_range['to'] = datetime.fromisoformat(date_range['to'])

                        # --- created_at ---
                        if alarm_data.get('created_at'):
                            if isinstance(alarm_data['created_at'], str):
                                alarm_data['created_at'] = datetime.fromisoformat(alarm_data['created_at'])
                        else:
                            alarm_data['created_at'] = datetime.now(timezone.utc)

                        # --- last_analysis_time ---
                        if alarm_data.get('last_analysis_time'):
                            if isinstance(alarm_data['last_analysis_time'], str):
                                alarm_data['last_analysis_time'] = datetime.fromisoformat(
                                    alarm_data['last_analysis_time']
                                )
                        
                        if 'from' in date_range and date_range['from']:
                            if date_range['from'].tzinfo is None:
                                # Si no tiene timezone, asumir local y convertir a UTC
                                local_tz = pytz.timezone('America/New_York')  # o configurar según sistema
                                date_range['from'] = local_tz.localize(date_range['from']).astimezone(timezone.utc)
                        
                        if 'to' in date_range and date_range['to']:
                            if date_range['to'].tzinfo is None:
                                local_tz = pytz.timezone('America/New_York')
                                date_range['to'] = local_tz.localize(date_range['to']).astimezone(timezone.utc)

                        alarm = AlarmConfig(
                            alarm_id=alarm_id,
                            chat_id=alarm_data.get('chat_id'),
                            chat_title=alarm_data.get('chat_title', 'Desconocido'),
                            interval=alarm_data.get('interval', {}),
                            date_range=date_range,
                            patterns=alarm_data.get('patterns', []),
                            last_analyzed_message_id=alarm_data.get('last_analyzed_message_id'),
                            last_analysis_time=alarm_data.get('last_analysis_time'),
                            total_runs=alarm_data.get('total_runs', 0),
                            enabled=alarm_data.get('enabled', True),
                            created_at=alarm_data['created_at']
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
                        # 'date_range': {
                        #     'from': alarm.date_range['from'].isoformat() if 'from' in alarm.date_range else None,
                        #     'to': alarm.date_range['to'].isoformat() if 'to' in alarm.date_range else None
                        # },
                        'date_range': {
                            'from': alarm.date_range['from'].isoformat() if alarm.date_range.get('from') else None,
                            'to': alarm.date_range['to'].isoformat() if alarm.date_range.get('to') else None
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
                        "updated_at": datetime.now(timezone.utc).isoformat()
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
                
                now = datetime.now(timezone.utc)
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
        interval = alarm.interval
        delta = timedelta(
            days=interval.get('days', 0),
            hours=interval.get('hours', 0),
            minutes=interval.get('minutes', 0)
        )

        if delta.total_seconds() <= 0:
            return None

        base = alarm.last_analysis_time or alarm.created_at
        next_run = base + delta
        now = datetime.now(timezone.utc)

        while next_run <= now:
            next_run += delta

        return next_run

    def schedule_alarm(self, alarm_id):
        alarm = self.alarms.get(alarm_id)
        if not alarm or not alarm.enabled:
            return

        interval = alarm.interval
        total_minutes = (
            interval.get('days', 0) * 24 * 60 +
            interval.get('hours', 0) * 60 +
            interval.get('minutes', 0)
        )

        if total_minutes <= 0:
            return

        schedule.every(total_minutes).minutes.do(
            lambda: self.queue_alarm(alarm_id)
        )

    def remove_alarm(self, alarm_id):
        with self.lock:
            if alarm_id in self.alarms:
                import schedule
                schedule.clear()
                del self.alarms[alarm_id]
                print(f"🗑 Alarma {alarm_id} eliminada")

                # Reprogramar todas las alarmas que quedan
                for remaining_id, remaining_alarm in self.alarms.items():
                    if remaining_alarm.enabled:
                        self.schedule_alarm(remaining_id)
                        print(f"🔄 Alarma {remaining_id} reprogramada")
                
                print(f"✅ Schedule limpiado y reconstruido sin alarma {alarm_id}")

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
   
    def _parse_date(self, value):
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        return datetime.fromisoformat(value)
    
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
                f"Reunión el {datetime.now(timezone.utc).strftime('%d/%m/%Y')} a las {i + 10}:00",
                f"Visita nuestro sitio https://sitio{i}.com y síguenos en @usuario{i}",
                f"Coordenadas: {40.41 + i/100}, {-3.70 + i/100} #viaje{i}"
            ]
            
            text = text_examples[i % len(text_examples)]
            
            message = AlarmMessage(
                id=msg_id,
                text=text,
                date=datetime.now(timezone.utc) - timedelta(hours=i),
                sender=f"Usuario{i}",
                media=None
            )
            messages.append(message)
        
        return messages
    
    def execute_alarm(self, alarm_id):
        """Ejecutar una alarma específica (controlada por next_run)"""

        import logging
        logger = logging.getLogger(__name__)

        # --- obtener alarma ---
        with self.lock:
            alarm = self.alarms.get(alarm_id)
            if not alarm or not alarm.enabled:
                return

            now = datetime.now(timezone.utc)

            # # ⛔ aún no toca ejecutar
            # if alarm.next_run and now < alarm.next_run:
            #     return

        logger.info("🔔 Ejecutando alarma %s (%s)", alarm_id, alarm.chat_title)

        try:
            # 1️⃣ Obtener mensajes
            messages = self.get_chat_messages(alarm)

            if not messages:
                # Sin mensajes también cuenta como ejecución
                self.send_no_updates(alarm)
                self.update_alarm_status(alarm_id, 0, messages)

            else:
                # 2️⃣ Extraer información
                extracted_data = self.extract_information(messages, alarm)

                total_matches = sum(len(v) for v in (extracted_data or {}).values())

                # 3️⃣ Generar mensaje
                alarm_message = self.generate_alarm_message(extracted_data, alarm)

                # 4️⃣ Enviar notificación
                if total_matches == 0:
                    logger.info(
                        "Alarma %s sin coincidencias. Enviando resumen.",
                        alarm.alarm_id
                    )
                    self.send_to_saved_messages(alarm_message, alarm)
                    self.update_alarm_status(alarm_id, 0, messages)
                else:
                    logger.info(
                        "Alarma %s con %d coincidencias. Enviando alerta.",
                        alarm.alarm_id,
                        total_matches
                    )
                    self.send_to_saved_messages(alarm_message, alarm)
                    self.update_alarm_status(alarm_id, 1, messages)

            logger.info("✅ Alarma %s ejecutada correctamente", alarm_id)

        except Exception as e:
            logger.exception("❌ Error ejecutando alarma %s", alarm_id)
            self.send_error_notification(alarm, str(e))

        finally:
            # 🔁 ACTUALIZAR ESTADO SIEMPRE
            with self.lock:
                now = datetime.now(timezone.utc)  # IMPORTANTE: con timezone UTC
                alarm.last_analysis_time = now
                
                # 📅 ACTUALIZAR RANGO DE FECHAS para próxima ejecución
                # El nuevo "from" es el anterior "to"
                # El nuevo "to" es la fecha actual
                old_to = alarm.date_range.get('to')
                
                print(f"📅 [AlarmManager] Alarma {alarm_id} - Actualizando fechas:")
                print(f"   Antiguo 'to': {old_to}")
                print(f"   Nuevo 'from': {old_to}")
                print(f"   Nuevo 'to': {now}")
                
                if old_to:
                    alarm.date_range['from'] = old_to
                alarm.date_range['to'] = now
                
                # Calcular próxima ejecución
                alarm.next_run = self.calculate_next_run(alarm)
                
                print(f"⏭️ [AlarmManager] Alarma {alarm_id} próxima ejecución: {alarm.next_run}")
                # Persistir si corresponde
                try:
                    self.save_alarms()
                except Exception:
                    logger.warning("No se pudo persistir estado de alarmas")

    def extract_information(self, messages: List[AlarmMessage], alarm: AlarmConfig):
        """Extraer información de los mensajes usando los patrones configurados.

        - Usa solo los patrones listados en alarm.patterns (predefined/custom).
        - Registra claramente patrones inválidos, número de matches y ejemplos.
        - No añade automáticamente patrones globales — el extractor global solo se ejecuta
        si existe una entrada en alarm.patterns con type == 'global' o use_global == True.
        """
        import logging
        logger = logging.getLogger(__name__)

        if not messages:
            logger.debug("extract_information: no hay mensajes para analizar.")
            return {}

        # Concatenar texto de todos los mensajes
        all_text = " ".join([msg.text for msg in messages if getattr(msg, "text", None)])
        if not all_text:
            logger.debug("extract_information: texto concatenado vacío.")
            return {}

        extracted = defaultdict(list)

        logger.info("extract_information: iniciando análisis con %d patrones configurados.",
                    len(alarm.patterns or []))

        # Procesar solo los patrones que vienen en la configuración de la alarma
        for idx, pattern_config in enumerate(alarm.patterns or []):
            pattern = pattern_config.get('pattern', '')
            name = pattern_config.get('name', f'Patrón_{idx}')
            ptype = pattern_config.get('type', 'custom')  # 'predefined', 'custom', 'global', etc.

            logger.debug("Pattern[%d] name=%s type=%s pattern=%s", idx, name, ptype, pattern)

            # Guardamos entrada aunque no encuentre nada para poder mostrar 0 matches en el informe
            extracted[name] = []

            if not pattern:
                logger.warning("Pattern[%d] '%s' vacío. Se omite.", idx, name)
                continue

            try:
                compiled = re.compile(pattern, re.IGNORECASE)
            except re.error as e:
                logger.error("⚠️ Error compilando patrón '%s' (%s): %s", name, pattern, e)
                continue

            try:
                # usar finditer para obtener grupos y preservar contexto
                matches = []
                for m in compiled.finditer(all_text):
                    # Si la regex tiene grupos, re.Match.groups() devuelve tupla; normalizamos a string
                    if m.groups():
                        # seleccionar el primer grupo no vacío si hay varios
                        grp_vals = [g for g in m.groups() if g is not None and g != ""]
                        if grp_vals:
                            matches.append(grp_vals[0])
                        else:
                            matches.append(m.group(0))
                    else:
                        matches.append(m.group(0))

                logger.info("Patrón '%s' → %d coincidencias.", name, len(matches))

                # Procesar enlaces si corresponde (mantengo tu lógica)
                if matches and ('url' in name.lower() or 'enlace' in name.lower() or 'link' in name.lower()):
                    if HAS_LINK_PROCESSOR:
                        processed_matches = []
                        for match in matches:
                            if isinstance(match, str):
                                try:
                                    processor = LinkProcessor()
                                    processed = processor.process_url(match)
                                    processed_matches.append(processed)
                                except Exception as e:
                                    logger.debug("LinkProcessor fallo para '%s': %s", match, e)
                                    processed_matches.append(match)
                            else:
                                processed_matches.append(match)
                        matches = processed_matches

                # Limitar a 10 resultados por patrón para no inflar el mensaje
                if matches:
                    extracted[name].extend(matches[:10])

                # Registrar ejemplos
                if matches:
                    examples = matches[:3]
                    logger.debug("Patrón '%s' ejemplos: %s", name, examples)
                else:
                    logger.debug("Patrón '%s' no detectó coincidencias.", name)

            except Exception as e:
                logger.exception("⚠️ Error procesando patrón '%s': %s", name, e)

        # Ejecutar extractor global solo si alguna entrada lo solicita explícitamente
        run_global = any((p.get('type') == 'global' or p.get('use_global')) for p in (alarm.patterns or []))
        if run_global:
            try:
                logger.info("extract_information: ejecutando extractor global (petición explícita).")
                global_patterns = extract_regex_patterns(all_text)
                for category, values in global_patterns.items():
                    if values:
                        key = f"Global_{category}"
                        extracted[key].extend(values[:5])
                        logger.info("Global extractor '%s' → %d valores.", category, len(values))
                    else:
                        logger.debug("Global extractor '%s' → 0 valores.", category)
            except Exception as e:
                logger.exception("⚠️ Error en extractor global: %s", e)
        else:
            logger.debug("extract_information: extractor global SKIPPED (no solicitado en la configuración).")

        return dict(extracted)

    def schedule_all_alarms(self):
        with self.lock:
            for alarm_id, alarm in self.alarms.items():
                if alarm.enabled:
                    self.schedule_alarm(alarm_id)

    def generate_alarm_message(self, extracted_data, alarm: AlarmConfig):
        """Generar mensaje de alarma usando IA (si está disponible) — con logs detallados."""
        import logging
        logger = logging.getLogger(__name__)

        if not HAS_AI_API:
            logger.debug("generate_alarm_message: NO hay API de IA disponible; usando mensaje básico.")
            return self.generate_basic_message(extracted_data, alarm)

        try:
            api_key = os.getenv('OPENROUTER_API_KEY')
            if not api_key:
                logger.warning("generate_alarm_message: falta OPENROUTER_API_KEY; usando mensaje básico.")
                return self.generate_basic_message(extracted_data, alarm)

            from regex.regex_config import format_extracted_data_for_prompt
            data_summary = format_extracted_data_for_prompt(extracted_data)
            prompt = get_alarm_message_prompt(extracted_data, alarm.chat_title)

            models = [
                "google/gemini-2.0-flash-exp:free",
                "mistralai/mistral-7b-instruct:free",
                "qwen/qwen-2.5-7b-instruct:free",
                "meta-llama/llama-3.2-3b-instruct:free"
            ]

            for model_id in models:
                try:
                    logger.info("Intentando generar mensaje con modelo %s", model_id)
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
                        logger.info("✅ Mensaje generado con %s (status 200).", model_id)
                        # también loggear una versión corta del mensaje para depuración (sin exponer todo)
                        logger.debug("Mensaje IA (preview): %s", (message[:300] + '...') if len(message) > 300 else message)
                        return message
                    else:
                        logger.warning("Respuesta no-200 con %s: %s - %s", model_id, response.status_code, response.text[:200])

                except Exception as e:
                    logger.exception("⚠️ Error llamando a modelo %s: %s", model_id, e)
                    continue

            logger.warning("generate_alarm_message: todos los modelos fallaron; usando mensaje básico.")
            return self.generate_basic_message(extracted_data, alarm)

        except Exception as e:
            logger.exception("⚠️ Error en generate_alarm_message (capa superior): %s", e)
            return self.generate_basic_message(extracted_data, alarm)

    def generate_basic_message(self, extracted_data, alarm: AlarmConfig):
        """Generar mensaje básico sin IA mostrando resultado completo por cada patrón."""
        lines = []
        lines.append(f"🔔 RESUMEN DE ALARMA: {alarm.chat_title}")
        lines.append(f"📅 {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M')}")
        lines.append(f"🆔 Alarma ID: {alarm.alarm_id}")
        lines.append("")

        lines.append("📊 RESULTADOS POR PATRÓN:")
        total_matches = 0

        for pattern_cfg in (alarm.patterns or []):
            name = pattern_cfg.get("name", "Desconocido")
            ptype = pattern_cfg.get("type", "custom")
            values = extracted_data.get(name, []) if extracted_data else []

            if not isinstance(values, list):
                values = [values] if values else []

            count = len(values)
            total_matches += count

            lines.append(f"  • {name} ({ptype}): {count} encontrados")

            if count:
                counter = Counter(str(v) for v in values)
                items = list(counter.items())  # preserva orden de aparición
                unique_count = len(items)

                encontrados = []
                for val, qty in items[:20]:
                    if qty > 1:
                        encontrados.append(f"{val} ({qty} veces)")
                    else:
                        encontrados.append(val)

                if unique_count > 20:
                    lines.append(
                        f"    → encontrados: {', '.join(encontrados)} "
                        f"(y {unique_count - 20} valores únicos más)"
                    )
                else:
                    lines.append(f"    → encontrados: {', '.join(encontrados)}")

        # Resultados del extractor global
        global_keys = [k for k in (extracted_data or {}).keys() if k.startswith("Global_")]
        if global_keys:
            lines.append("")
            lines.append("🔎 RESULTADOS DEL EXTRACTOR GLOBAL:")
            for k in global_keys:
                vals = extracted_data.get(k, [])
                if not isinstance(vals, list):
                    vals = [vals] if vals else []

                count = len(vals)
                total_matches += count
                lines.append(f"  • {k}: {count} encontrados")

                if count:
                    counter = Counter(str(v) for v in vals)
                    items = list(counter.items())
                    unique_count = len(items)

                    encontrados = []
                    for val, qty in items[:20]:
                        if qty > 1:
                            encontrados.append(f"{val} ({qty} veces)")
                        else:
                            encontrados.append(val)

                    if unique_count > 20:
                        lines.append(
                            f"    → encontrados: {', '.join(encontrados)} "
                            f"(y {unique_count - 20} valores únicos más)"
                        )
                    else:
                        lines.append(f"    → encontrados: {', '.join(encontrados)}")

        lines.append("")
        lines.append(f"📈 Total de coincidencias: {total_matches}")
        lines.append("")
        lines.append("⏰ Próxima revisión según intervalo configurado")

        return "\n".join(lines)

    def get_chat_messages(self, alarm: AlarmConfig) -> List[AlarmMessage]:
        """Obtener mensajes del chat usando el worker del main_window"""
        date_from = alarm.date_range.get('from')
        date_to = alarm.date_range.get('to')
        
        # Formatear fechas para logging
        from_str = date_from.strftime('%Y-%m-%d %H:%M:%S') if date_from else 'None'
        to_str = date_to.strftime('%Y-%m-%d %H:%M:%S') if date_to else 'None'
        
        print(f"🔍 Solicitando mensajes del chat {alarm.chat_id} desde {from_str} hasta {to_str}")

        if not self.telegram_app:
            print(f"❌ Sin telegram_app para alarma {alarm.alarm_id}")
            return []
        
        date_from = alarm.date_range.get("from")
        date_to = alarm.date_range.get("to")
        
        print(f"🔍 [AlarmManager] Fechas que se enviarán al worker:")
        print(f"   from: {date_from} (tz: {date_from.tzinfo if date_from else 'N/A'})")
        print(f"   to: {date_to} (tz: {date_to.tzinfo if date_to else 'N/A'})")
        
        try:
            # Delegar al main_window que use el worker
            messages = self.telegram_app.fetch_chat_messages_for_alarm(
                chat_id=alarm.chat_id,
                date_from=date_from,
                date_to=date_to,
                alarm_id=alarm.alarm_id
            )
            
            print(f"✅ Alarma {alarm.alarm_id}: {len(messages)} mensajes obtenidos")
            return messages
            
        except Exception as e:
            print(f"❌ Error obteniendo mensajes para alarma {alarm.alarm_id}: {e}")
            import traceback
            traceback.print_exc()
            return []
        
    def send_to_saved_messages(self, message: str, alarm):
        """Enviar mensaje usando el worker del main_window"""
        alarm_id = getattr(alarm, "alarm_id", "N/A")
        print(f"📤 Enviando mensaje de alarma {alarm_id} a Mensajes Guardados...")
        
        if not self.telegram_app:
            print("❌ No hay telegram_app, guardando en archivo")
            self._save_to_file_as_backup(message, alarm)
            return
        
        try:
            # Delegar al main_window que use el worker
            success = self.telegram_app.send_alarm_message_to_saved(message, alarm_id)
            
            if success:
                print(f"✅ Mensaje de alarma {alarm_id} enviado correctamente")
            else:
                print(f"⚠️ No se pudo confirmar envío de alarma {alarm_id}, guardando respaldo")
                self._save_to_file_as_backup(message, alarm)
                    
        except Exception as e:
            print(f"❌ Error enviando mensaje de alarma {alarm_id}: {e}")
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
            
            log_file = os.path.join(log_dir, f"alarma_{alarm_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.txt")
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"Alarma: {chat_title} (ID: {alarm_id})\n")
                f.write(f"Fecha: {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M:%S')}\n")
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
            
            alarm.last_analysis_time = datetime.now(timezone.utc)
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
            date=datetime.now(timezone.utc),
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
            now = datetime.now(timezone.utc)
            
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

        delta = next_run - datetime.now(timezone.utc)

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
