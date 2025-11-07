"""
Analiza tendencias temporales en los patrones extraídos:
- Evolución de precios por moneda
- Patrones de actividad por hora/día
- Correlación entre tipos de patrones
- Detección de eventos/anomalías
"""

import json
from datetime import datetime, timedelta
from collections import defaultdict
import statistics
from typing import Dict, List, Any

class TrendAnalyzer:
    def __init__(self, patterns_data: Dict):
        self.patterns_data = patterns_data
        self.messages = patterns_data.get("message_analysis", [])
    
    def analyze_price_evolution(self) -> Dict:
        """
        Analiza la evolución de precios mencionados por moneda a lo largo del tiempo
        """
        price_evolution = defaultdict(list)
        
        for msg in self.messages:
            timestamp = msg.get("timestamp")
            if not timestamp:
                continue
                
            date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            patterns = msg.get("patterns_detected", {})
            
            # Extraer precios por moneda
            for currency_match in patterns.get("monedas_explicitas", []):
                if len(currency_match) >= 2:
                    price = self._extract_price(currency_match[0])
                    currency = currency_match[1].lower()
                    if price and currency:
                        price_evolution[currency].append({
                            "date": date,
                            "price": price,
                            "message": msg.get("enriched_text", "")
                        })
        
        # Calcular estadísticas por moneda
        stats = {}
        for currency, prices_data in price_evolution.items():
            prices = [p["price"] for p in prices_data]
            if prices:
                stats[currency] = {
                    "count": len(prices),
                    "min": min(prices),
                    "max": max(prices),
                    "avg": statistics.mean(prices),
                    "median": statistics.median(prices),
                    "trend": self._calculate_trend(prices),
                    "volatility": statistics.stdev(prices) if len(prices) > 1 else 0
                }
        
        return {
            "price_statistics": stats,
            "raw_data": price_evolution,
            "time_period": self._get_analysis_period()
        }
    
    def analyze_temporal_patterns(self) -> Dict:
        """
        Analiza patrones de actividad temporal
        """
        hourly_activity = defaultdict(int)
        daily_activity = defaultdict(int)
        pattern_by_hour = defaultdict(lambda: defaultdict(int))
        
        for msg in self.messages:
            timestamp = msg.get("timestamp")
            if not timestamp:
                continue
                
            date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            hour = date.hour
            day = date.strftime("%A")
            patterns = msg.get("patterns_detected", {})
            
            hourly_activity[hour] += 1
            daily_activity[day] += 1
            
            # Contar patrones por hora
            if patterns.get("monedas_explicitas"):
                pattern_by_hour[hour]["financial"] += 1
            if any(key.startswith('dates_') for key in patterns):
                pattern_by_hour[hour]["temporal"] += 1
            if patterns.get("urls_raw"):
                pattern_by_hour[hour]["urls"] += 1
        
        return {
            "hourly_activity": dict(hourly_activity),
            "daily_activity": dict(daily_activity),
            "patterns_by_hour": pattern_by_hour,
            "peak_hours": self._find_peak_hours(hourly_activity),
            "recommended_times": self._recommend_engagement_times(pattern_by_hour)
        }
    
    def detect_anomalies(self) -> Dict:
        """
        Detecta comportamientos anómalos o inusuales
        """
        anomalies = {
            "price_spikes": [],
            "unusual_activity": [],
            "suspicious_patterns": []
        }
        
        # Detectar spikes de precios
        price_data = self.analyze_price_evolution()
        for currency, stats in price_data["price_statistics"].items():
            if stats["volatility"] > stats["avg"] * 0.5:  # Alta volatilidad
                anomalies["price_spikes"].append({
                    "currency": currency,
                    "volatility": stats["volatility"],
                    "reason": "Precio muy volátil"
                })
        
        # Detectar actividad inusual
        temporal_data = self.analyze_temporal_patterns()
        for hour, count in temporal_data["hourly_activity"].items():
            if 2 <= hour <= 5 and count > 10:  # Mucha actividad nocturna
                anomalies["unusual_activity"].append({
                    "hour": hour,
                    "activity_count": count,
                    "reason": "Alta actividad en horas nocturnas"
                })
        
        # Detectar patrones sospechosos
        for msg in self.messages:
            patterns = msg.get("patterns_detected", {})
            if (len(patterns.get("phone_numbers", [])) > 2 or 
                len(patterns.get("emails", [])) > 2):
                anomalies["suspicious_patterns"].append({
                    "message_id": msg.get("message_id"),
                    "patterns": {k: v for k, v in patterns.items() if v},
                    "reason": "Múltiples datos de contacto en un solo mensaje"
                })
        
        return anomalies
    
    def correlation_analysis(self) -> Dict:
        """
        Analiza correlaciones entre diferentes tipos de patrones
        """
        correlations = {
            "financial_temporal": self._correlate_financial_temporal(),
            "social_financial": self._correlate_social_financial(),
            "contact_technical": self._correlate_contact_technical()
        }
        
        return {
            "correlations": correlations,
            "insights": self._generate_correlation_insights(correlations)
        }
    
    def _extract_price(self, price_str: str) -> float:
        """Extrae valor numérico del precio"""
        try:
            # Manejar rangos (tomar promedio)
            if '-' in price_str:
                parts = price_str.split('-')
                return (float(parts[0].strip()) + float(parts[1].strip())) / 2
            # Manejar decimales con coma
            price_str = price_str.replace(',', '.')
            return float(''.join(c for c in price_str if c.isdigit() or c == '.'))
        except:
            return None
    
    def _calculate_trend(self, prices: List[float]) -> str:
        """Calcula tendencia de precios"""
        if len(prices) < 2:
            return "estable"
        
        first_half = statistics.mean(prices[:len(prices)//2])
        second_half = statistics.mean(prices[len(prices)//2:])
        
        if second_half > first_half * 1.1:
            return "alcista"
        elif second_half < first_half * 0.9:
            return "bajista"
        else:
            return "estable"
    
    def _get_analysis_period(self) -> Dict:
        """Obtiene período de análisis"""
        dates = []
        for msg in self.messages:
            if msg.get("timestamp"):
                dates.append(datetime.fromisoformat(msg.get("timestamp").replace('Z', '+00:00')))
        
        return {
            "start": min(dates) if dates else None,
            "end": max(dates) if dates else None,
            "days": (max(dates) - min(dates)).days if len(dates) > 1 else 0
        }
    
    def _find_peak_hours(self, hourly_activity: Dict) -> List:
        """Encuentra horas pico de actividad"""
        sorted_hours = sorted(hourly_activity.items(), key=lambda x: x[1], reverse=True)
        return [{"hour": hour, "activity": count} for hour, count in sorted_hours[:3]]
    
    def _recommend_engagement_times(self, pattern_by_hour: Dict) -> List:
        """Recomienda mejores horarios para engagement"""
        recommendations = []
        for hour in range(24):
            financial = pattern_by_hour[hour]["financial"]
            if financial > 0:
                recommendations.append({
                    "hour": hour,
                    "recommendation": "Ideal para transacciones financieras",
                    "financial_activity": financial
                })
        return sorted(recommendations, key=lambda x: x["financial_activity"], reverse=True)[:3]
    
    def _correlate_financial_temporal(self) -> Dict:
        """Correlación entre actividad financiera y temporal"""
        financial_by_weekday = defaultdict(int)
        for msg in self.messages:
            timestamp = msg.get("timestamp")
            patterns = msg.get("patterns_detected", {})
            if timestamp and patterns.get("monedas_explicitas"):
                date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                financial_by_weekday[date.strftime("%A")] += 1
        
        return {
            "financial_by_weekday": dict(financial_by_weekday),
            "most_active_day": max(financial_by_weekday.items(), key=lambda x: x[1]) if financial_by_weekday else None
        }
    
    def _correlate_social_financial(self) -> Dict:
        """Correlación entre actividad social y financiera"""
        social_financial = 0
        total_financial = 0
        
        for msg in self.messages:
            patterns = msg.get("patterns_detected", {})
            has_financial = bool(patterns.get("monedas_explicitas"))
            has_social = bool(patterns.get("hashtags") or patterns.get("mentions"))
            
            if has_financial:
                total_financial += 1
                if has_social:
                    social_financial += 1
        
        return {
            "social_financial_correlation": social_financial / total_financial if total_financial > 0 else 0,
            "total_correlated_messages": social_financial
        }
    
    def _correlate_contact_technical(self) -> Dict:
        """Correlación entre contactos y patrones técnicos"""
        contact_technical = 0
        total_contact = 0
        
        for msg in self.messages:
            patterns = msg.get("patterns_detected", {})
            has_contact = bool(patterns.get("emails") or patterns.get("phone_numbers"))
            has_technical = bool(patterns.get("coordinates") or patterns.get("ip_addresses"))
            
            if has_contact:
                total_contact += 1
                if has_technical:
                    contact_technical += 1
        
        return {
            "contact_technical_correlation": contact_technical / total_contact if total_contact > 0 else 0,
            "implications": "Posibles transacciones con ubicación específica" if contact_technical > 0 else "Sin correlación significativa"
        }
    
    def _generate_correlation_insights(self, correlations: Dict) -> List[str]:
        """Genera insights basados en correlaciones"""
        insights = []
        
        # Insight de días financieros
        financial_day = correlations["financial_temporal"].get("most_active_day")
        if financial_day:
            insights.append(f"💸 Día más activo financieramente: {financial_day[0]} con {financial_day[1]} transacciones")
        
        # Insight social-financiero
        social_fin = correlations["social_financial"]["social_financial_correlation"]
        if social_fin > 0.3:
            insights.append("📱 Las transacciones financieras frecuentemente incluyen elementos sociales (hashtags, menciones)")
        
        # Insight contacto-técnico
        contact_tech = correlations["contact_technical"]["contact_technical_correlation"]
        if contact_tech > 0.2:
            insights.append("📍 Los contactos suelen venir acompañados de información técnica (coordenadas, IPs)")
        
        return insights

def generate_comprehensive_report(patterns_file: str) -> Dict:
    """
    Genera un reporte completo de análisis de tendencias
    """
    with open(patterns_file, 'r', encoding='utf-8') as f:
        patterns_data = json.load(f)
    
    analyzer = TrendAnalyzer(patterns_data)
    
    report = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "source_file": patterns_file,
            "total_messages_analyzed": len(analyzer.messages)
        },
        "price_analysis": analyzer.analyze_price_evolution(),
        "temporal_patterns": analyzer.analyze_temporal_patterns(),
        "anomalies": analyzer.detect_anomalies(),
        "correlations": analyzer.correlation_analysis(),
        "executive_summary": generate_executive_summary(analyzer)
    }
    
    return report

def generate_executive_summary(analyzer: TrendAnalyzer) -> Dict:
    """Genera un resumen ejecutivo con los hallazgos más importantes"""
    price_analysis = analyzer.analyze_price_evolution()
    temporal_patterns = analyzer.analyze_temporal_patterns()
    anomalies = analyzer.detect_anomalies()
    correlations = analyzer.correlation_analysis()
    
    summary = {
        "key_findings": [],
        "recommendations": [],
        "risk_factors": []
    }
    
    # Hallazgos clave
    if price_analysis["price_statistics"]:
        most_active_currency = max(price_analysis["price_statistics"].items(), 
                                 key=lambda x: x[1]["count"])
        summary["key_findings"].append(
            f"Moneda más mencionada: {most_active_currency[0]} ({most_active_currency[1]['count']} referencias)"
        )
    
    if temporal_patterns["peak_hours"]:
        peak = temporal_patterns["peak_hours"][0]
        summary["key_findings"].append(
            f"Hora pico de actividad: {peak['hour']}:00 ({peak['activity']} mensajes)"
        )
    
    # Recomendaciones
    if temporal_patterns["recommended_times"]:
        best_time = temporal_patterns["recommended_times"][0]
        summary["recommendations"].append(
            f"Mejor horario para engagement financiero: {best_time['hour']}:00"
        )
    
    # Factores de riesgo
    if anomalies["price_spikes"]:
        summary["risk_factors"].append(
            f"Alta volatilidad detectada en {len(anomalies['price_spikes'])} monedas"
        )
    
    if anomalies["suspicious_patterns"]:
        summary["risk_factors"].append(
            f"{len(anomalies['suspicious_patterns'])} mensajes con patrones sospechosos detectados"
        )
    
    return summary

# Ejemplo de uso
if __name__ == "__main__":
    # Uso básico
    patterns_file = "patterns/chat_patterns.json"  # Ajusta la ruta
    report = generate_comprehensive_report(patterns_file)
    
    # Guardar reporte
    with open("trend_analysis_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print("📊 Reporte de análisis de tendencias generado exitosamente!")
    print(f"📈 Monedas analizadas: {len(report['price_analysis']['price_statistics'])}")
    print(f"⚠️  Anomalías detectadas: {len(report['anomalies']['price_spikes']) + len(report['anomalies']['suspicious_patterns'])}")
    print(f"💡 Insights generados: {len(report['executive_summary']['key_findings'])}")