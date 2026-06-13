"""
STUBS DE MÓDULOS — para probar app.py (Render) en el entorno de prueba.
Reemplazan los módulos reales (que tienen dependencias pesadas como Gemini)
con versiones ligeras que devuelven datos sintéticos. Permite probar TODA la
lógica de app.py: cron, agenda, persistencia, endpoints.
"""
import sys
import types
import json

def instalar_stubs():
    """Inyecta módulos falsos en sys.modules antes de importar app.py."""

    # ── modulos.usuarios ──
    m_usuarios = types.ModuleType("modulos.usuarios")
    class UsuarioManager:
        def __init__(self, *a, **k): pass
        def validar(self, *a, **k): return True
        def obtener_usuarios(self): return []
    m_usuarios.UsuarioManager = UsuarioManager

    # ── modulos.boveda ──
    m_boveda = types.ModuleType("modulos.boveda")
    class BovedaManager:
        def __init__(self, *a, **k): pass
        def obtener_datos(self): return {"youtube_api": "FAKE_KEY", "voice_api": "FAKE", "gemini_keys": ["k1"]}
        def guardar_boveda_completa(self, *a, **k): pass
        def obtener_llaves(self): return ["k1"]
    m_boveda.BovedaManager = BovedaManager

    # ── modulos.ai_engine ──
    m_ai = types.ModuleType("modulos.ai_engine")
    class AIEngine:
        def __init__(self, *a, **k): pass
        def generar_paquete_publicacion(self, *a, **k):
            return {"titulo": "Test", "descripcion": "Test", "tags": []}
    m_ai.AIEngine = AIEngine

    # ── modulos.cctv_engine ──
    m_cctv = types.ModuleType("modulos.cctv_engine")
    class CCTVEngine:
        def __init__(self, *a, **k): pass
    m_cctv.CCTVEngine = CCTVEngine

    # ── modulos.voice_engine ──
    m_voice = types.ModuleType("modulos.voice_engine")
    class VoiceEngine:
        def __init__(self, *a, **k): pass
    m_voice.VoiceEngine = VoiceEngine

    # ── modulos.video_engine ──
    m_video = types.ModuleType("modulos.video_engine")
    class VideoEngine:
        def __init__(self, *a, **k): pass
    m_video.VideoEngine = VideoEngine

    # ── modulos.trend_engine ──
    m_trend = types.ModuleType("modulos.trend_engine")
    class TrendEngine:
        def __init__(self, *a, **k): pass
        def inyectar_contexto_viral(self, marca, api_key=""):
            return f"CONTEXTO VIRAL para {marca}: tema en tendencia simulado."
        def escanear_traccion_competitiva(self, *a, **k):
            return {"tema": "Tema simulado", "vph": 1500}
    m_trend.TrendEngine = TrendEngine

    # ── modulos.compliance_engine ──
    m_comp = types.ModuleType("modulos.compliance_engine")
    class ComplianceEngine:
        def __init__(self, *a, **k): pass
        def blindar_guion(self, ai_engine_instancia, marca, contexto, peticion, longitud, formato):
            # Devuelve un guion JSON válido con escenas y hooks (como Gemini real)
            n = 25 if "9:16" in formato else 50
            escenas = [{"id": i+1, "prompt_visual": f"escena {i+1}",
                        "texto_locucion": f"Narración de la escena {i+1} con texto suficiente."}
                       for i in range(n)]
            return json.dumps({
                "marca": marca, "formato": formato,
                "titulo_sugerido": f"Video de {marca}",
                "hooks": ["Hook 1", "Hook 2", "Hook 3"],
                "escenas": escenas,
            }, ensure_ascii=False)
    m_comp.ComplianceEngine = ComplianceEngine

    # Registrar todos en sys.modules
    paquete = types.ModuleType("modulos")
    sys.modules["modulos"] = paquete
    sys.modules["modulos.usuarios"] = m_usuarios
    sys.modules["modulos.boveda"] = m_boveda
    sys.modules["modulos.ai_engine"] = m_ai
    sys.modules["modulos.cctv_engine"] = m_cctv
    sys.modules["modulos.voice_engine"] = m_voice
    sys.modules["modulos.video_engine"] = m_video
    sys.modules["modulos.trend_engine"] = m_trend
    sys.modules["modulos.compliance_engine"] = m_comp
